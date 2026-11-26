import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.accessibility import Reader, ReadingOptions, MAX_TEXT, PALETTES
from aeris.settings import Settings, Appearance, FLAGS

class AccessibilityTests(unittest.TestCase):
    def test_defaults_and_bounds(self):
        self.assertEqual(ReadingOptions().size,16)
        for size in (12,30): self.assertEqual(ReadingOptions(size).size,size)
        for size in (11,31,True,16.5):
            with self.assertRaises(ValueError): ReadingOptions(size)
    def test_invalid_options(self):
        for kwargs in ({'palette':'unknown'},{'spacious':1},{'guide':'sim'}):
            with self.assertRaises(ValueError): ReadingOptions(**kwargs)
        self.assertEqual(PALETTES['Alto contraste'][:2],('#000000','#FFFFFF'))
    def test_normalization_and_guide(self):
        r=Reader(); r.load('Olá\r\n\rTexto\n'); self.assertEqual(r.text,'Olá\n\nTexto\n'); self.assertEqual(r.lines,4)
        self.assertEqual([r.move(1) for _ in range(5)],[2,3,4,4,4])
        self.assertEqual([r.move(-1) for _ in range(5)],[3,2,1,1,1])
        with self.assertRaises(ValueError): r.move(True)
    def test_reject_input_atomically(self):
        r=Reader(); r.load('x'*MAX_TEXT)
        for bad in ('x'*(MAX_TEXT+1),'\x00',None):
            with self.assertRaises(ValueError): r.load(bad)
            self.assertEqual(r.text,'x'*MAX_TEXT)
    def test_clear_and_reload(self):
        r=Reader(); r.load('a\nb'); r.move(1); r.load('c'); self.assertEqual(r.line,1)
        r.clear(); self.assertEqual((r.text,r.lines,r.move(1)),('',0,1))
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Flashcards',True)
            data=json.loads(p.read_text()); data['schema']=42; data.pop('accessibility_enabled'); p.write_text(json.dumps(data))
            s=Settings(p); self.assertTrue(s.flashcards_enabled); self.assertFalse(s.accessibility_enabled); self.assertFalse(s.warning)
            s.set_module('Accessibility',True); s.set_appearance(Appearance(favorites=('Accessibility',))); s=Settings(p)
            self.assertTrue(s.accessibility_enabled and s.flashcards_enabled); self.assertEqual(s.appearance.favorites,('Accessibility',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
