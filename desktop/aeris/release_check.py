"""Build/validate a portable preview ZIP without extracting untrusted paths."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import zipfile

MAX_TOTAL = 512 * 1024 * 1024
MAX_FILES = 10000
MANIFEST = 'Aeris/BUNDLE-MANIFEST.json'
REQUIRED = {'Aeris/Aeris.exe', 'Aeris/_internal/aeris/catalog.json',
            'Aeris/_internal/python314.dll', 'Aeris/PREVIEW.txt', 'Aeris/PYTHON-LICENSE.txt'}
RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
            *(f'LPT{i}' for i in range(1, 10))}


def safe_name(name):
    parts = name.split('/')
    if len(parts) < 2 or parts[0] != 'Aeris' or any(
        not p or p in {'.', '..'} or p.endswith((' ', '.')) or
        any(ord(c) < 32 or c in '\\:<>"|?*' for c in p) or
        p.split('.')[0].upper() in RESERVED for p in parts
    ):
        raise ValueError('Unsafe archive path')
    return name.casefold()


def digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(chunk)
    return h.hexdigest()


def pe_x64(stream):
    head = stream.read(64)
    if len(head) != 64 or head[:2] != b'MZ':
        raise ValueError('Missing PE header')
    offset = struct.unpack_from('<I', head, 60)[0]
    if not 64 <= offset <= 1024 * 1024:
        raise ValueError('Invalid PE offset')
    stream.seek(offset)
    if stream.read(6) != b'PE\0\0\x64\x86':
        raise ValueError('Expected AMD64 PE')


def pe_installer(stream):
    """Structural sanity check, not signature or executable validation."""
    head = stream.read(64)
    if len(head) != 64 or head[:2] != b'MZ':
        raise ValueError('Missing installer executable header')
    offset = struct.unpack_from('<I', head, 60)[0]
    if not 64 <= offset <= 1024 * 1024:
        raise ValueError('Invalid installer PE offset')
    stream.seek(offset)
    header = stream.read(24)
    if len(header) != 24 or header[:4] != b'PE\0\0' or struct.unpack_from('<H',header,4)[0] not in (0x14c,0x8664):
        raise ValueError('Invalid installer PE header')


def build_portable(bundle, output):
    bundle, output = Path(bundle), Path(output)
    if bundle.name != 'Aeris' or bundle.is_symlink() or getattr(bundle.lstat(),'st_file_attributes',0) & 0x400 or output.exists() or output.resolve().is_relative_to(bundle.resolve()):
        raise ValueError('Expected new ZIP outside Aeris bundle')
    files = {}
    seen = set()
    total = 0
    for p in sorted(bundle.rglob('*')):
        if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0) & 0x400:
            raise ValueError('Symlinks and reparse points are not allowed')
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError('Nonregular bundle member')
        name = 'Aeris/' + p.relative_to(bundle).as_posix()
        key = safe_name(name)
        if key in seen or key == MANIFEST.casefold():
            raise ValueError('Duplicate or reserved bundle member')
        seen.add(key)
        total += p.stat().st_size
        if total > MAX_TOTAL or len(files) >= MAX_FILES - 1:
            raise ValueError('Bundle limit exceeded')
        with p.open('rb') as f:
            files[name] = (p, digest(f))
    if not REQUIRED <= files.keys():
        raise ValueError('Incomplete bundle')
    created = False
    try:
        with output.open('xb') as stream:
            created = True
            with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
                for name, (p, _) in files.items():
                    z.write(p, name)
                z.writestr(MANIFEST, json.dumps({name: h for name, (_, h) in files.items()}, sort_keys=True))
        return verify_portable(output)
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise


def verify_portable(path):
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_TOTAL:
            raise ValueError('Archive limit exceeded')
        names = set()
        folded = set()
        for i in entries:
            key = safe_name(i.filename)
            if key in folded or i.is_dir() or i.flag_bits & 1 or stat.S_IFMT(i.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ValueError('Duplicate or nonregular archive member')
            folded.add(key)
            names.add(i.filename)
        if not REQUIRED | {MANIFEST} <= names:
            raise ValueError('Incomplete portable archive')
        # Reject path-as-file ancestor conflicts before a consumer extracts.
        for name in names:
            if any(str(p).casefold() in folded for p in PurePosixPath(name).parents):
                raise ValueError('Archive file/directory conflict')
        if z.getinfo(MANIFEST).file_size > 2 * 1024 * 1024:
            raise ValueError('Manifest too large')
        from aeris.safe_input import strict_json
        manifest = strict_json(z.read(MANIFEST), 2 * 1024 * 1024)
        if not isinstance(manifest, dict) or set(manifest) != names - {MANIFEST}:
            raise ValueError('Manifest does not match archive')
        for name, expected in manifest.items():
            if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
                raise ValueError('Invalid digest')
            with z.open(name) as f:
                if digest(f) != expected:
                    raise ValueError('Bundle hash mismatch')
        for name in ('Aeris/Aeris.exe', 'Aeris/_internal/python314.dll'):
            with z.open(name) as f:
                pe_x64(f)
        return len(manifest)


def verify_release(directory, version, portable_only=False):
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:a|rc)\d+', version):
        raise ValueError('Invalid preview version')
    directory = Path(directory)
    base = f'Aeris-{version}-Windows-x64'
    expected = {base + '-portable.zip'}
    if not portable_only:
        expected.add(base + '-Setup.exe')
    sums = directory / 'SHA256SUMS.txt'
    if sums.is_symlink() or not sums.is_file() or getattr(sums.lstat(),'st_file_attributes',0) & 0x400:
        raise ValueError('Invalid checksum manifest file')
    if sums.stat().st_size > 4096:
        raise ValueError('Checksum manifest too large')
    parsed = {}
    for line in sums.read_text(encoding='ascii').splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9.-]+)', line)
        if not m or m[2] in parsed:
            raise ValueError('Invalid checksum manifest')
        parsed[m[2]] = m[1]
    if set(parsed) != expected:
        raise ValueError('Unexpected or missing artifact')
    for name, h in parsed.items():
        p = directory / name
        if p.is_symlink() or not p.is_file() or getattr(p.lstat(),'st_file_attributes',0) & 0x400:
            raise ValueError('Invalid artifact file')
        with p.open('rb') as f:
            if digest(f) != h:
                raise ValueError('Artifact checksum mismatch')
    # Inno Setup's bootstrapper may be 32-bit even for an x64 payload.
    if not portable_only:
        with (directory / (base + '-Setup.exe')).open('rb') as f:
            pe_installer(f)
    return verify_portable(directory / (base + '-portable.zip'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('pack'); build.add_argument('bundle'); build.add_argument('output')
    check = sub.add_parser('verify'); check.add_argument('directory'); check.add_argument('version'); check.add_argument('--portable-only', action='store_true')
    a = parser.parse_args()
    count = build_portable(a.bundle, a.output) if a.command == 'pack' else verify_release(a.directory, a.version, a.portable_only)
    print(f'Portable bundle verified: {count} files (not native execution or authenticity validation).')


if __name__ == '__main__':
    main()
