import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
from aeris.backup import BackupService, parse
from aeris.settings import Settings, Appearance
from aeris.permissions import Permissions, CREATE_BACKUP, RESTORE_BACKUP
from aeris.vault import Vault
from aeris.bookmarks import BookmarkStore
from tests.test_vault import TestBackend

class BackupTests(unittest.TestCase):
    def setUp(self):
        d=TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.folder=Path(d.name); self.path=self.folder/'copy.aerisbackup'
        self.settings=Settings(self.folder/'settings.json'); self.permissions=Permissions()
        self.backend=TestBackend(); self.service=BackupService(self.settings,self.permissions,self.backend)
        self.vault=Vault(self.folder/'vault.bin',self.backend); self.addCleanup(self.vault.lock)
        self.permissions.set(CREATE_BACKUP,True); self.permissions.set(RESTORE_BACKUP,True)
    def seed(self):
        self.vault.unlock(); self.vault.save('Original','Fictício'); self.vault.lock()
    def test_restore_and_recovery(self):
        self.seed(); original=self.vault.path.read_bytes(); self.service.create(self.path)
        self.vault.unlock(); self.vault.save('Novo','Teste'); self.vault.lock(); latest=self.vault.path.read_bytes()
        recovery=self.service.restore(self.path,'Vault')
        self.assertEqual(recovery.read_bytes(),latest); self.assertEqual(self.vault.path.read_bytes(),original)
        self.vault.unlock(); self.assertEqual(len(self.vault.list()),1)
    def test_permissions(self):
        self.permissions.set(CREATE_BACKUP,False)
        with self.assertRaises(PermissionError): self.service.create(self.path)
        self.permissions.set(CREATE_BACKUP,True); self.service.create(self.path)
        self.permissions.set(RESTORE_BACKUP,False)
        with self.assertRaises(PermissionError): self.service.inspect(self.path)
        with self.assertRaises(PermissionError): self.service.restore(self.path,'Aparência')
    def test_appearance_only_and_no_overwrite(self):
        self.settings.set_appearance(Appearance(theme='Escuro')); self.service.create(self.path)
        self.assertEqual(self.service.inspect(self.path),('Aparência',)); original=self.path.read_bytes()
        with self.assertRaises(FileExistsError): self.service.create(self.path)
        self.assertEqual(self.path.read_bytes(),original)
        self.settings.set_appearance(Appearance()); self.settings.set_module('Vault',True)
        self.service.restore(self.path,'Aparência'); self.assertEqual(self.settings.appearance.theme,'Escuro'); self.assertTrue(self.settings.vault_enabled)
    def test_hash_corruption_and_unknown_target(self):
        self.seed(); self.service.create(self.path); before=self.vault.path.read_bytes()
        data=json.loads(self.path.read_bytes()); data['items']['Vault']['sha256']='0'*64; self.path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.service.restore(self.path,'Vault')
        self.assertEqual(self.vault.path.read_bytes(),before)
        data['items']['../../other']=data['items'].pop('Vault')
        with self.assertRaises(ValueError): parse(json.dumps(data))
    def test_wrong_account_and_failed_replace_preserve_original(self):
        self.seed(); self.service.create(self.path); before=self.vault.path.read_bytes()
        with patch.object(self.backend,'unprotect',side_effect=OSError('wrong account')):
            with self.assertRaises(OSError): self.service.restore(self.path,'Vault')
        self.assertEqual(self.vault.path.read_bytes(),before)
        with patch('aeris.backup.os.replace',side_effect=OSError('blocked')):
            with self.assertRaises(OSError): self.service.restore(self.path,'Vault')
        self.assertEqual(self.vault.path.read_bytes(),before)
    def test_lease(self):
        self.seed(); self.vault.unlock()
        with self.assertRaises(OSError): self.service.create(self.path)
        self.assertFalse(self.path.exists()); self.vault.lock(); self.service.create(self.path)
        self.vault.unlock()
        with self.assertRaises(OSError): self.service.restore(self.path,'Vault')
    def test_bookmarks_roundtrip(self):
        b=BookmarkStore(self.folder/'bookmarks.bin',self.permissions,self.backend); self.addCleanup(b.lock)
        b.unlock(); item=b.save('Site','Geral','https://example.com'); b.lock()
        self.service.create(self.path); b.unlock(); b.delete(item.id); b.lock()
        self.service.restore(self.path,'Bookmarks'); b.unlock(); self.assertEqual(b.list(),(item,))
    def test_migration(self):
        p=self.settings.path; self.settings.set_module('Backup',True); self.assertTrue(Settings(p).backup_enabled)
        old=json.loads(p.read_text()); old['schema']=9; del old['backup_enabled']; p.write_text(json.dumps(old))
        self.assertFalse(Settings(p).backup_enabled)

    @unittest.skipUnless(__import__('sys').platform == 'win32', 'Backup DPAPI real requer Windows')
    def test_native_windows_backup(self):
        vault=Vault(self.folder/'vault.bin'); self.addCleanup(vault.lock)
        service=BackupService(self.settings,self.permissions)
        vault.unlock(); item=vault.save('Fictício','Texto de teste'); vault.lock()
        service.create(self.path)
        vault.unlock(); vault.delete(item.id); vault.lock()
        service.restore(self.path,'Vault'); vault.unlock()
        self.assertEqual(vault.list(),(item,))
