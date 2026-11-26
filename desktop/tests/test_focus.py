import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.focus import FocusTimer, MODES
from aeris.settings import Settings, Appearance

class FocusTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.timer = FocusTimer(lambda: self.now)

    def test_deadline_and_completion_once(self):
        t=self.timer; t.configure(MODES[0],1); t.start()
        self.now+=59.2; self.assertFalse(t.tick()); self.assertEqual(t.seconds,1)
        self.now+=5; self.assertTrue(t.tick()); self.assertEqual(t.seconds,0)
        self.assertFalse(t.tick()); self.assertEqual(t.completed[MODES[0]],1)
        self.assertEqual(t.state,'finished')

    def test_pause_resume_does_not_count_paused_time(self):
        t=self.timer; t.configure(MODES[0],1); t.start(); self.now+=12.5; t.pause()
        self.assertEqual(t.state,'paused'); self.assertEqual(t.seconds,48)
        self.now+=3600; t.tick(); self.assertEqual(t.seconds,48)
        t.start(); self.now+=47; self.assertFalse(t.tick()); self.now+=1; self.assertTrue(t.tick())

    def test_reset_discards_incomplete_and_preserves_counts(self):
        t=self.timer; t.configure(MODES[1],1); t.start(); self.now+=60; t.tick()
        t.start(); self.now+=15; t.reset(); self.now+=100; self.assertFalse(t.tick())
        self.assertEqual(t.state,'ready'); self.assertEqual(t.seconds,60)
        self.assertEqual(t.completed,{MODES[0]:0,MODES[1]:1})

    def test_validation(self):
        for mode,minutes in [('x',1),(MODES[0],0),(MODES[0],121),(MODES[0],True),(MODES[0],1.5)]:
            with self.subTest(mode=mode,minutes=minutes),self.assertRaises(ValueError): self.timer.configure(mode,minutes)
        self.timer.start()
        with self.assertRaises(ValueError): self.timer.configure(MODES[1],5)
        self.timer.pause()
        with self.assertRaises(ValueError): self.timer.configure(MODES[1],5)

    def test_duplicate_start_and_pause_at_deadline(self):
        t=self.timer; t.configure(MODES[0],1); t.start(); self.now+=30; t.start(); self.now+=30
        self.assertTrue(t.pause()); self.assertFalse(t.pause()); self.assertEqual(t.completed[MODES[0]],1)

    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Lens',True)
            old=json.loads(p.read_text()); old['schema']=29; old.pop('focus_enabled'); p.write_text(json.dumps(old))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.lens_enabled); self.assertFalse(s.focus_enabled)
            s.set_module('Focus',True); s.set_appearance(Appearance(favorites=('Focus',)))
            s=Settings(p); self.assertTrue(s.focus_enabled and s.lens_enabled); self.assertEqual(s.appearance.favorites,('Focus',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
