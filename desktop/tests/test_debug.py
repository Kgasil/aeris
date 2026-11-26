import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from aeris.debug import analyze
from aeris.settings import Settings, Appearance

class DebugTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(analyze('def soma(a,b):\n    return a+b').valid)
        self.assertEqual(analyze('x=1').diagnostics,())
    def test_syntax(self):
        r=analyze('def soma(a,b)\n    return a+b')
        self.assertFalse(r.valid); self.assertEqual(r.diagnostics[0].line,1); self.assertIn('dois-pontos',r.diagnostics[0].suggestion)
        self.assertFalse(analyze('if True:\nprint(1)').valid)
        self.assertFalse(analyze('x = [1,2').valid)
    def test_scope(self):
        for code in ['return 1','break','nonlocal x','await f()']:
            self.assertFalse(analyze(code).valid)
    def test_never_executes(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'should-not-exist'
            self.assertTrue(analyze(f'open({str(p)!r}, "w").write("oops")\nraise RuntimeError()').valid)
            self.assertFalse(p.exists())
            self.assertTrue(analyze('import nonexistent_module').valid)
    def test_hints(self):
        r=analyze('from math import *\ndef f(a=[], *, b={}):\n    try:\n        pass\n    except:\n        pass')
        self.assertTrue(r.valid); self.assertEqual([d.line for d in r.diagnostics],[1,2,2,5]); self.assertEqual(len(r.diagnostics),4)
        r=analyze('def f(á=[]): pass'); self.assertEqual(r.diagnostics[0].column,9)
        r=analyze('\n'.join(f'def f{i}(x=[]): pass' for i in range(51))); self.assertTrue(r.truncated); self.assertEqual(len(r.diagnostics),50)
    def test_limits(self):
        for text in [None,'','   ','x\x00=1','x=1\n'*1001,'#'+'a'*20000,'x='+'1+'*150+'1','\ud800']:
            with self.assertRaises(ValueError): analyze(text)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Interview',True)
            old=json.loads(p.read_text()); old['schema']=47; old.pop('debug_enabled'); p.write_text(json.dumps(old)); s=Settings(p)
            self.assertTrue(s.interview_enabled); self.assertFalse(s.debug_enabled); self.assertFalse(s.warning)
            s.set_module('Debug',True); s.set_appearance(Appearance(favorites=('Debug',))); s=Settings(p)
            self.assertTrue(s.debug_enabled); self.assertEqual(s.appearance.favorites,('Debug',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
