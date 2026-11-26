import unittest
from aeris.translate import phrase_translate, validate
from aeris.settings import Settings
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.permissions import Permissions,COPY_TRANSLATION

class TranslateTests(unittest.TestCase):
    def test_phrase(self):
        self.assertEqual(phrase_translate(' BOM DIA! ','pt','en'),'Good morning!')
        self.assertEqual(phrase_translate('¡Hola!','es','pt'),'Olá!')
    def test_unknown(self):
        with self.assertRaises(ValueError): phrase_translate('texto livre','pt','en')
    def test_invalid(self):
        for args in [('','pt','en'),('x'*4001,'pt','en'),('ok','pt','pt'),('ok','xx','en')]:
            with self.assertRaises(ValueError): validate(*args)
    def test_permission(self):
        p=Permissions(); self.assertFalse(p.allowed(COPY_TRANSLATION)); p.set(COPY_TRANSLATION,True); self.assertTrue(p.allowed(COPY_TRANSLATION)); p.revoke_all(); self.assertFalse(p.allowed(COPY_TRANSLATION))
    def test_preferences(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'settings.json'; s=Settings(path); self.assertFalse(s.translate_enabled); s.set_module('Translate',True); self.assertTrue(Settings(path).translate_enabled)
