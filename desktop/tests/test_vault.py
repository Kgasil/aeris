import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.vault import Vault, MAGIC
from aeris.dpapi import WindowsDPAPI
from aeris.settings import Settings

class TestBackend:
    """Test double only. NOT encryption and never used by the application."""
    def protect(self, data): return data[::-1]
    def unprotect(self, data): return data[::-1]

class VaultTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'vault.bin'
        self.v=Vault(self.path,TestBackend()); self.addCleanup(self.v.lock)
    def test_locked_and_roundtrip(self):
        with self.assertRaises(PermissionError): self.v.list()
        self.v.unlock(); item=self.v.save('Título fictício','conteúdo de exemplo')
        self.assertTrue(self.path.read_bytes().startswith(MAGIC))
        self.v.lock()
        with self.assertRaises(PermissionError): self.v.save('a','b')
        self.v.unlock(); self.assertEqual(self.v.list(),(item,))
        self.v.save('Editado','texto',item.id); self.v.delete(item.id)
        self.v.lock(); self.v.unlock(); self.assertEqual(self.v.list(),())
    def test_failed_protection_preserves_old_data(self):
        self.v.unlock(); item=self.v.save('A','B'); original=self.path.read_bytes()
        def fail(_): raise OSError('simulated')
        self.v.backend.protect=fail
        with self.assertRaises(OSError): self.v.save('C','D')
        self.assertEqual(self.path.read_bytes(),original); self.assertEqual(self.v.list(),(item,))
    def test_corruption_fails_closed(self):
        self.path.write_bytes(MAGIC+b'broken')
        with self.assertRaises(ValueError): self.v.unlock()
        self.assertFalse(self.v.unlocked); self.assertEqual(self.path.read_bytes(),MAGIC+b'broken')
    def test_exclusive_lock(self):
        self.v.unlock(); other=Vault(self.path,TestBackend()); self.addCleanup(other.lock)
        with self.assertRaises(OSError): other.unlock()
        self.v.lock(); other.unlock(); self.assertTrue(other.unlocked)
    def test_limits(self):
        self.v.unlock()
        for title,body in [('', 'a'),('a',''),('x'*121,'a'),('a','x'*20001)]:
            with self.assertRaises(ValueError): self.v.save(title,body)
        self.assertFalse(self.path.exists())
    def test_setting(self):
        p=self.path.parent/'settings.json'; s=Settings(p)
        self.assertFalse(s.vault_enabled); s.set_module('Vault',True)
        self.assertTrue(Settings(p).vault_enabled)
    @unittest.skipUnless(sys.platform=='win32','DPAPI native requires Windows')
    def test_real_windows_dpapi(self):
        vault=Vault(self.path); self.addCleanup(vault.lock); vault.unlock()
        item=vault.save('Aeris fictício','exemplo de texto DPAPI')
        self.assertNotIn(item.body.encode(),self.path.read_bytes())
        vault.lock(); vault.unlock(); self.assertEqual(vault.list(),(item,))
    @unittest.skipIf(sys.platform=='win32','Non-Windows safeguard')
    def test_non_windows_fails_closed(self):
        with self.assertRaises(OSError): WindowsDPAPI()
