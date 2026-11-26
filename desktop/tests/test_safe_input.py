import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock
from aeris.safe_input import bounded_read, strict_json
from aeris.settings import Settings, MAX_SETTINGS
from aeris.vault import Vault, MAGIC
from aeris.backup import parse, BackupService
from aeris.permissions import Permissions, RESTORE_BACKUP
from aeris.companion import chat
from aeris.protected_storage import ProtectedStorage, MAGIC as STORAGE_MAGIC
from tests.test_vault import TestBackend

class SafeInputTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
    def test_json_boundaries(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":{"a":1,"a":2}}', b'NaN', b'Infinity', b'-Infinity', b'1e999', b'\xff', b'['*2000+b']'*2000):
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError): strict_json(raw, 10000)
        with self.assertRaises(ValueError): strict_json('"é"', 3)
        self.assertEqual(strict_json(b'{"a":1.5}', 20), {'a':1.5})
    def test_regular_and_oversize(self):
        p = self.folder/'sample'; p.write_bytes(b'123')
        self.assertEqual(bounded_read(p,3), b'123')
        with self.assertRaises(ValueError): bounded_read(p,2)
        with self.assertRaises(ValueError): bounded_read(self.folder,100)
    @unittest.skipUnless(hasattr(os,'mkfifo'), 'FIFO test requires POSIX')
    def test_fifo_rejected_before_open(self):
        p = self.folder/'fifo'; os.mkfifo(p)
        with self.assertRaises(ValueError): bounded_read(p,100)
    def test_symlink_rejected(self):
        target=self.folder/'target'; target.write_bytes(b'abc'); link=self.folder/'link'
        try: link.symlink_to(target)
        except (OSError, NotImplementedError): self.skipTest('Symlink unavailable')
        with self.assertRaises(ValueError): bounded_read(link,100)
        self.assertEqual(target.read_bytes(),b'abc')
    def test_settings_fail_closed(self):
        p=self.folder/'settings.json'; Settings(p).set_module('Vault',True)
        valid=p.read_bytes()
        for raw in (valid.replace(b'"schema": 49',b'"schema": 49, "schema": 49'), b' '* (MAX_SETTINGS+1), b'['*2000+b']'*2000):
            p.write_bytes(raw); s=Settings(p)
            self.assertFalse(s.vault_enabled); self.assertTrue(s.warning); self.assertEqual(p.read_bytes(),raw)
    def test_vault_rejects_ambiguous_schema_and_preserves_bytes(self):
        p=self.folder/'vault.bin'; vault=Vault(p,TestBackend()); self.addCleanup(vault.lock)
        for raw in (b'{"schema":true,"entries":[]}',b'{"schema":1,"entries":[],"entries":[]}',b'{"schema":1,"entries":[],"extra":0}',b'{"schema":1,"entries":[{"id":1,"title":"A","body":"B","id":2}]}'):
            blob=MAGIC+raw[::-1]; p.write_bytes(blob)
            with self.assertRaises(ValueError): vault.unlock()
            self.assertFalse(vault.unlocked); self.assertEqual(p.read_bytes(),blob)
        vault.decode(MAGIC+b'{"schema":1,"entries":[]}'[::-1])
    def test_storage_rejects_nonfinite_json(self):
        storage=ProtectedStorage(self.folder,TestBackend())
        raw=b'{"schema":1,"module":"Ideas","records":NaN}'
        with self.assertRaises(ValueError): storage.decode('Ideas',STORAGE_MAGIC+raw[::-1])
    def test_backup_rejects_duplicate_and_special_file(self):
        with self.assertRaises(ValueError): parse(b'{"format":"AERIS-BACKUP-1","items":{},"items":{}}')
        permissions=Permissions(); permissions.set(RESTORE_BACKUP,True)
        with self.assertRaises(ValueError): BackupService(Settings(self.folder/'settings.json'),permissions,TestBackend()).inspect(self.folder)
    def test_companion_rejects_duplicate_response(self):
        factory=Mock(); conn=factory.return_value; response=conn.getresponse.return_value
        response.status=200; response.read.return_value=b'{"done":false,"done":true,"message":{"role":"assistant","content":"Oi"}}'
        with self.assertRaises(ValueError): chat('local',(), 'Oi',connection_factory=factory)
        conn.close.assert_called_once()
