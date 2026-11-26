import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.autosave import AutoSave
from aeris.protected_storage import ProtectedStorage
from aeris.checklist import ChecklistStore
from tests.test_protected_storage import FakeBackend

class AutoSaveTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.storage=ProtectedStorage(tmp.name,FakeBackend()); self.store=ChecklistStore(); self.store.create('A'); self.store.add('A','Primeira'); self.allowed=True
        self.auto=AutoSave(self.storage,lambda:self.allowed,lambda m:self.store)
    def test_opt_in_and_unchanged(self):
        self.auto.tick(); self.assertFalse(self.storage.path('Checklist').exists())
        self.auto.arm('Checklist'); self.auto.tick(); raw=self.storage.path('Checklist').read_bytes()
        with patch.object(self.storage,'save_if_current') as save:
            self.auto.tick(); save.assert_not_called()
        self.store.add('A','Segunda'); self.auto.tick(); self.assertEqual(len(self.storage.load('Checklist').list()),2); self.assertEqual(self.storage.previous_path('Checklist').read_bytes(),raw)
    def test_divergence(self):
        self.storage.save('Checklist',self.store); self.store.add('A','Não substituir')
        with self.assertRaises(ValueError): self.auto.arm('Checklist')
        self.assertFalse(self.auto.armed)
    def test_empty(self):
        self.storage.save('Checklist',self.store); self.auto.arm('Checklist'); raw=self.storage.path('Checklist').read_bytes(); self.store.clear(); self.assertEqual(self.auto.tick(),['Checklist']); self.assertEqual(self.storage.path('Checklist').read_bytes(),raw)
        with self.assertRaises(ValueError): self.auto.arm('Checklist')
    def test_conflict(self):
        self.storage.save('Checklist',self.store); self.auto.arm('Checklist'); self.store.add('A','Local')
        other=ChecklistStore(); other.create('Outro'); self.storage.save('Checklist',other,overwrite=True)
        raw=self.storage.path('Checklist').read_bytes(); self.assertEqual(self.auto.tick(),['Checklist']); self.assertEqual(self.storage.path('Checklist').read_bytes(),raw)
    def test_external_delete(self):
        self.storage.save('Checklist',self.store); self.auto.arm('Checklist'); self.storage.delete('Checklist'); self.store.add('A','Novo'); self.assertEqual(self.auto.tick(),['Checklist']); self.assertFalse(self.storage.path('Checklist').exists())
    def test_revocation_and_replacement(self):
        self.auto.arm('Checklist'); self.allowed=False; self.auto.tick(); self.assertFalse(self.auto.armed); self.assertFalse(self.storage.path('Checklist').exists())
        with self.assertRaises(PermissionError): self.auto.arm('Checklist')
        self.allowed=True; self.auto.arm('Checklist'); self.store=ChecklistStore(); self.store.create('B'); self.auto.tick(); self.assertFalse(self.auto.armed)
    def test_failure(self):
        self.storage.save('Checklist',self.store); self.auto.arm('Checklist'); raw=self.storage.path('Checklist').read_bytes(); self.store.add('A','Novo')
        with patch.object(self.storage.backend,'protect',side_effect=OSError('falha')): self.assertEqual(self.auto.tick(),['Checklist'])
        self.assertEqual(self.storage.path('Checklist').read_bytes(),raw)
    def test_stop_all(self):
        self.auto.arm('Checklist'); self.auto.stop_all(); self.auto.tick(); self.assertFalse(self.storage.path('Checklist').exists())
