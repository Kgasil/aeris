import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.context import ContextStore
from aeris.permissions import Permissions, CONTEXT_PREVIEW
from aeris.settings import Settings, Appearance

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.p=Permissions(); self.s=ContextStore(self.p)
    def test_default_denied_and_private(self):
        item=self.s.add('Objetivo','Estudos','Aprender Python')
        with self.assertRaises(PermissionError): self.s.select(item.id,True)
        with self.assertRaises(PermissionError): self.s.preview()
        self.p.set(CONTEXT_PREVIEW,True)
        with self.assertRaises(ValueError): self.s.preview()
    def test_select_only_explicit_items(self):
        self.p.set(CONTEXT_PREVIEW,True)
        a=self.s.add('Objetivo','Estudos','Aprender Python'); b=self.s.add('Privado','Outros','não incluir')
        self.s.select(a.id,True)
        self.assertEqual(self.s.preview(),'[Estudos] Objetivo\nAprender Python')
        self.assertFalse(self.s.selected(b.id)); self.s.select(a.id,False)
        with self.assertRaises(ValueError): self.s.preview()
    def test_edit_and_delete_revoke(self):
        self.p.set(CONTEXT_PREVIEW,True); a=self.s.add('Título','Agenda','Amanhã'); self.s.select(a.id,True)
        self.s.edit(a.id,'Título','Agenda','Hoje'); self.assertFalse(self.s.selected(a.id))
        self.s.select(a.id,True); self.s.delete(a.id); self.assertFalse(self.s.list())
        with self.assertRaises(ValueError): self.s.preview()
    def test_validation_and_bounds(self):
        for args in [('', 'Outros','x'),('x','Inválida','x'),('x','Outros',''),('x','Outros','\x00'),('x','Outros','x'*4001)]:
            with self.assertRaises(ValueError): self.s.add(*args)
        self.p.set(CONTEXT_PREVIEW,True)
        for i in range(50):
            a=self.s.add(str(i),'Outros','x'*4000); self.s.select(a.id,True)
        with self.assertRaises(ValueError): self.s.add('x','Outros','x')
        with self.assertRaises(ValueError): self.s.preview()
    def test_revoke_and_clear(self):
        self.p.set(CONTEXT_PREVIEW,True); a=self.s.add('x','Outros','x'); self.s.select(a.id,True)
        self.s.revoke(); self.assertFalse(self.s.selected(a.id)); self.assertEqual(len(self.s.list()),1)
        self.s.select(a.id,True); self.p.set(CONTEXT_PREVIEW,False)
        with self.assertRaises(PermissionError): self.s.preview()
        self.s.clear(); self.assertFalse(self.s.list())
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Copilot',True)
            data=json.loads(p.read_text()); data['schema']=45; data.pop('context_enabled'); p.write_text(json.dumps(data)); s=Settings(p)
            self.assertTrue(s.copilot_enabled); self.assertFalse(s.context_enabled); self.assertFalse(s.warning)
            s.set_module('Context',True); s.set_appearance(Appearance(favorites=('Context',))); s=Settings(p)
            self.assertTrue(s.context_enabled); self.assertEqual(s.appearance.favorites,('Context',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
