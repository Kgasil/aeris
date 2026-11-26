import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from aeris.release_check import (build_portable, verify_portable, verify_release,
                                 REQUIRED, safe_name)


def fake_pe(machine=0x8664):
    raw = bytearray(134)
    raw[:2] = b'MZ'
    struct.pack_into('<I', raw, 60, 128)
    raw[128:132] = b'PE\0\0'
    struct.pack_into('<H', raw, 132, machine)
    return bytes(raw)


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / 'Aeris'
        self.version = '0.13.0a2'
        self.zip = self.root / f'Aeris-{self.version}-Windows-x64-portable.zip'
        for name in REQUIRED:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(fake_pe() if p.suffix in ('.exe', '.dll') else b'fixture')
        (self.bundle / '.hidden').write_bytes(b'preserved')

    def test_roundtrip(self):
        self.assertEqual(build_portable(self.bundle, self.zip), 6)
        self.assertEqual(verify_portable(self.zip), 6)
        with zipfile.ZipFile(self.zip) as z:
            self.assertIn('Aeris/.hidden', z.namelist())

    def test_missing_required(self):
        (self.bundle / 'Aeris.exe').unlink()
        with self.assertRaises(ValueError): build_portable(self.bundle, self.zip)
        self.assertFalse(self.zip.exists())

    def test_architecture(self):
        (self.bundle / 'Aeris.exe').write_bytes(fake_pe(0x14c))
        with self.assertRaises(ValueError): build_portable(self.bundle, self.zip)
        self.assertFalse(self.zip.exists())

    def test_runtime_dll_required(self):
        (self.bundle / '_internal' / 'python314.dll').unlink()
        with self.assertRaises(ValueError):
            build_portable(self.bundle, self.zip)
        self.assertFalse(self.zip.exists())
    
    def test_runtime_dll_architecture(self):
        (self.bundle / '_internal' / 'python314.dll').write_bytes(fake_pe(0x14c))
        with self.assertRaises(ValueError):
            build_portable(self.bundle, self.zip)
        self.assertFalse(self.zip.exists())
    
    def test_path_rejection(self):
        for name in ('Aeris/../outside', 'Aeris/C:bad', 'Aeris/a\\b', 'Aeris/NUL.txt', 'Aeris/trailing.', '/Aeris/test', 'Aeris//test'):
            with self.subTest(name=name), self.assertRaises(ValueError): safe_name(name)

    def test_archive_extra_and_duplicate(self):
        build_portable(self.bundle, self.zip)
        with zipfile.ZipFile(self.zip, 'a') as z: z.writestr('Aeris/AERIS.EXE', b'bad')
        with self.assertRaises(ValueError): verify_portable(self.zip)

    def test_tampered_content(self):
        build_portable(self.bundle, self.zip)
        with zipfile.ZipFile(self.zip) as z: content = {n:z.read(n) for n in z.namelist()}
        content['Aeris/PREVIEW.txt'] = b'tampered'
        with zipfile.ZipFile(self.zip, 'w') as z:
            for n, data in content.items(): z.writestr(n, data)
        with self.assertRaises(ValueError): verify_portable(self.zip)

    def test_release_checksums(self):
        build_portable(self.bundle, self.zip)
        sums = self.root / 'SHA256SUMS.txt'
        sums.write_text(hashlib.sha256(self.zip.read_bytes()).hexdigest() + '  ' + self.zip.name + '\n', encoding='ascii')
        self.assertEqual(verify_release(self.root, self.version, True), 6)
        with self.assertRaises(ValueError): verify_release(self.root, self.version)
        sums.write_text('0'*64 + '  ' + self.zip.name + '\n', encoding='ascii')
        with self.assertRaises(ValueError): verify_release(self.root, self.version, True)

    def test_no_overwrite(self):
        self.zip.write_bytes(b'existing')
        with self.assertRaises(ValueError): build_portable(self.bundle, self.zip)
        self.assertEqual(self.zip.read_bytes(), b'existing')

    def test_candidate_version_checksums(self):
        version = '1.0.0rc1'
        archive = self.root / f'Aeris-{version}-Windows-x64-portable.zip'
        build_portable(self.bundle, archive)
        sums = self.root / 'SHA256SUMS.txt'
        sums.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n', encoding='ascii')
        self.assertEqual(verify_release(self.root, version, True), 6)
        for invalid in ('1.0.0', '1.0.0-rc1', '../1.0.0rc1'):
            with self.subTest(version=invalid), self.assertRaises(ValueError):
                verify_release(self.root, invalid, True)
