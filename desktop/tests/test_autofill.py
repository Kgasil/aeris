import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.autofill import ProfileStore,validate,preview
from aeris.permissions import Permissions,COPY_AUTOFILL
from tests.test_vault import TestBackend
from aeris.settings import Settings

class AutofillTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'autofill.bin'
        self.p=Permissions(); self.store=ProfileStore(self.path,self.p,TestBackend()); self.addCleanup(self.store.lock)
    def test_persistence(self):
        self.store.unlock(); item=self.store.save('Demo',{'name':'Alex Example','email':'alex@example.com'})
        self.store.lock(); self.store.unlock(); self.assertEqual(self.store.get(item.id),item)
        self.store.save('Demo2',{'tel':'123'},item.id); self.store.delete(item.id); self.assertEqual(self.store.list(),())
    def test_field_allowlist(self):
        for fields in ({'password':'test'},{'cc-number':'1234'},{'name':'\n'}, {'name':'x'*251}, {'name':' '}):
            with self.assertRaises(ValueError): validate('Demo',fields)
        self.assertEqual(preview({'name':'Alex','email':'a@example.com'},['name','password']), (('name','Alex'),))
    def test_permission(self):
        self.store.unlock(); item=self.store.save('Demo',{'name':'Alex'})
        with self.assertRaises(PermissionError): self.store.copy_value(item.id,'name')
        self.p.set(COPY_AUTOFILL,True); self.assertEqual(self.store.copy_value(item.id,'name'),'Alex')
        self.p.revoke_all()
        with self.assertRaises(PermissionError): self.store.copy_value(item.id,'name')
    def test_lock(self):
        with self.assertRaises(PermissionError): self.store.list()
    def test_settings(self):
        s=Settings(self.path.parent/'settings.json'); self.assertFalse(s.autofill_enabled); s.set_module('Autofill',True)
        self.assertTrue(Settings(s.path).autofill_enabled)
