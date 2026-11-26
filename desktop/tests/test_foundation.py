import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict
from aeris.settings import Settings,Appearance
from aeris.content import CaptureStore,SnippetStore
from aeris.quick_panel import panel_bounds

class PreferencesTests(unittest.TestCase):
    def test_defaults_and_roundtrip(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p)
            self.assertFalse(p.exists()); self.assertFalse(s.capture_enabled); self.assertFalse(s.appearance.floating_enabled)
            s.set_capture(True); s.set_snippets(True); s.set_search(True); s.set_appearance(Appearance(icon_size=48,floating_enabled=True))
            t=Settings(p); self.assertTrue(t.capture_enabled and t.snippets_enabled and t.search_enabled); self.assertEqual(t.appearance,s.appearance)
    def test_migrations(self):
        for schema in range(1,6):
            with self.subTest(schema=schema), TemporaryDirectory() as d:
                p=Path(d)/'settings.json'; data={'schema':schema,'capture_enabled':True}
                if schema>=2: data['appearance']={'icon_size':40}
                if schema>=3: data['snippets_enabled']=True
                if schema>=4: data['search_enabled']=True
                p.write_text(json.dumps(data)); s=Settings(p)
                self.assertFalse(s.warning); self.assertTrue(s.capture_enabled); self.assertEqual(s.snippets_enabled,schema>=3); self.assertEqual(s.search_enabled,schema>=4)
    def test_corrupt_settings(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; p.write_text('{"schema":3,"capture_enabled":true,"snippets_enabled":1,"appearance":{}}')
            s=Settings(p); self.assertTrue(s.warning); self.assertFalse(s.capture_enabled or s.snippets_enabled or s.search_enabled)
    def test_invalid_appearance(self):
        for kw in ({'icon_size':65},{'opacity':79},{'floating_enabled':1},{'corner':'?'}):
            with self.assertRaises(ValueError): Appearance(**kw)
    def test_panel_bounds(self):
        self.assertEqual(panel_bounds('Inferior direito',(320,420),(100,100,800,600),(1920,1080)),(320,420,580,280))
        self.assertEqual(panel_bounds('Superior esquerdo',(420,520),(-100,-200,500,500),(300,400)),(300,400,0,0))

class ContentTests(unittest.TestCase):
    def test_capture_crud_callback(self):
        calls=[]; s=CaptureStore(lambda:calls.append(1)); a=s.save('Reunião','SQL'); b=s.save('Novo','Texto',a.id); self.assertEqual(s.list(),(b,)); s.delete(b.id); self.assertEqual(s.list(),()); self.assertEqual(len(calls),3)
    def test_snippets_search_exact_content(self):
        s=SnippetStore(); a=s.save(' Consulta ',' Código ','  SELECT 1;\n '); self.assertEqual(a.body,'  SELECT 1;\n '); self.assertEqual(s.list('codigo select'),(a,)); self.assertEqual(s.list(category='Código'),(a,)); s.clear(); self.assertFalse(s.list())
    def test_invalid_and_limits(self):
        s=SnippetStore()
        for args in [('', 'Geral','abc'),('A','','abc'),('A','Geral',' '),('x'*121,'Geral','abc'),('A','Geral','x'*20001)]:
            with self.assertRaises(ValueError): s.save(*args)
        for i in range(100): s.save(str(i),'Geral','abc')
        with self.assertRaises(ValueError): s.save('101','Geral','abc')
    def test_isolation(self):
        s=CaptureStore(); s.save('A','B'); self.assertEqual(CaptureStore().list(),()); self.assertEqual(SnippetStore().list(),())
