import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict
from aeris.settings import Appearance, Settings
from aeris.hub import Hub
from types import SimpleNamespace

class RefinementTests(unittest.TestCase):
    def test_roundtrip_schema12(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p)
            prefs=Appearance(theme='Escuro',favorites=('Search','Capture'),favorites_only=True)
            s.set_appearance(prefs); s.set_capture(True)
            self.assertEqual(Settings(p).appearance,prefs)
            self.assertEqual(json.loads(p.read_text())['schema'],49)
            self.assertTrue(Settings(p).capture_enabled)
    def test_migrate_schema5(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; a=asdict(Appearance(icon_size=44))
            for key in ('theme','favorites','favorites_only'): a.pop(key)
            p.write_text(json.dumps(dict(schema=5,capture_enabled=True,snippets_enabled=False,search_enabled=True,appearance=a)))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.capture_enabled and s.search_enabled)
            self.assertEqual(s.appearance,Appearance(icon_size=44))
    def test_invalid_preferences(self):
        for kw in ({'theme':'?','favorites':()},{'favorites':('Capture','Capture')},{'favorites':('Inexistente',)},{'favorites':'Search'},{'favorites_only':1}):
            with self.subTest(kw=kw),self.assertRaises(ValueError): Appearance(**kw)
    def test_favorites_filter_does_not_activate(self):
        fake=SimpleNamespace(settings=SimpleNamespace(appearance=Appearance(favorites=('Search','Snippets'),favorites_only=True)),enabled=lambda n:False,workspace_store=None,active_tools=lambda:[('Capture',None),('Search',None)])
        self.assertEqual(Hub.quick_tools(fake),[('Search',None)])
        fake.settings.appearance=Appearance(favorites=('Search',))
        self.assertEqual(Hub.quick_tools(fake),[('Search',None),('Capture',None)])
