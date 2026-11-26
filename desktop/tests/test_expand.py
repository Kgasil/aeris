import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from aeris.expand import ExpandStore, Expansion
from aeris.settings import Settings

class ExpandTests(unittest.TestCase):
    def setUp(self): self.store=ExpandStore()
    def test_defaults_and_boundaries(self):
        self.assertEqual(self.store.expand(';att\n;obg!'),Expansion('Atenciosamente,\nMuito obrigado pela atenção!!',2))
        text='x;att ;;att ;att-extra ;atté ;ATT ;unknown'
        self.assertEqual(self.store.expand(text),Expansion(text,0))
    def test_edit_delete_non_recursive(self):
        self.store.save(';demo',';att'); self.assertEqual(self.store.expand(';demo'),Expansion(';att',1))
        self.store.save(';demo','Olá\nMundo'); self.assertEqual(self.store.expand(';demo ;demo').count,2)
        self.store.delete(';demo'); self.assertEqual(self.store.expand(';demo').count,0)
    def test_invalid_rules(self):
        for code,text in [('abc','x'),(';1','x'),(';UP','x'),(';a'*34,'x'),(';a',' '),(';a','x'*2001)]:
            with self.assertRaises(ValueError): self.store.save(code,text)
    def test_limits(self):
        self.store.save(';big','a'*2000)
        with self.assertRaises(ValueError): self.store.expand(';big '*51)
        with self.assertRaises(ValueError): self.store.expand('a'*20001)
        self.store.clear()
        for i in range(100): self.store.save(f';a{i}','x')
        with self.assertRaises(ValueError): self.store.save(';overflow','x')
    def test_session_and_settings(self):
        self.store.save(';private','test'); self.assertNotIn(';private',dict(ExpandStore().list()))
        self.store.clear(); self.assertEqual(self.store.list(),())
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Autofill',True)
            data=json.loads(p.read_text()); data['schema']=16; del data['expand_enabled']; p.write_text(json.dumps(data))
            s=Settings(p); self.assertTrue(s.autofill_enabled); self.assertFalse(s.expand_enabled)
            s.set_module('Expand',True); self.assertTrue(Settings(p).expand_enabled)
            self.assertNotIn('private',p.read_text())
