import unittest
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from dataclasses import asdict
from aeris.text import transform, stats
from aeris.permissions import Permissions, COPY_TEXT
from aeris.settings import Settings, Appearance, FLAGS

class TextTests(unittest.TestCase):
    def test_case(self):
        self.assertEqual(transform('Olá, ação!', 'Maiúsculas'),'OLÁ, AÇÃO!')
        self.assertEqual(transform('AÇÃO','Minúsculas'),'ação')
    def test_whitespace(self):
        self.assertEqual(transform('  a  b\t\r\n\r\n  c ', 'Remover espaços excedentes'),'a b\n\nc')
        self.assertEqual(transform('  a\n \t\nb\n','Remover linhas vazias'),'  a\nb')
    def test_deduplicate(self):
        self.assertEqual(transform('a\nb\na\nA','Remover linhas duplicadas'),'a\nb\nA')
    def test_newlines_and_stats(self):
        self.assertEqual(transform('a\r\nb\rc','Padronizar quebras de linha'),'a\nb\nc')
        self.assertEqual((stats('Olá mundo\nOi').words,stats('Olá mundo\nOi').lines),(3,2))
        self.assertEqual(stats('').lines,0)
    def test_validation(self):
        for value,op in [('x'*20001,'Maiúsculas'),('ß'*20000,'Maiúsculas'),('a\0','Minúsculas'),('a','inválida')]:
            with self.assertRaises(ValueError): transform(value,op)
    def test_permission_migration(self):
        p=Permissions(); self.assertFalse(p.allowed(COPY_TEXT)); p.set(COPY_TEXT,True); p.revoke_all(); self.assertFalse(p.allowed(COPY_TEXT))
        with TemporaryDirectory() as d:
            f=Path(d)/'settings.json'; data={k:k=='voice_enabled' for k in FLAGS if k!='text_enabled'}; data.update(schema=12,appearance=asdict(Appearance(favorites=('Voice',))))
            f.write_text(json.dumps(data)); s=Settings(f); self.assertTrue(s.voice_enabled); self.assertFalse(s.text_enabled); self.assertFalse(s.warning)
            s.set_module('Text',True); self.assertTrue(Settings(f).text_enabled); self.assertTrue(Settings(f).voice_enabled)
