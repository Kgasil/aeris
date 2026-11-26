import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.interview import InterviewStore, AREAS, QUESTIONS, CRITERIA
from aeris.settings import Settings, Appearance

class InterviewTests(unittest.TestCase):
    def setUp(self): self.s=InterviewStore()
    def test_bank(self):
        self.assertEqual(len(QUESTIONS),12); self.assertEqual(len(AREAS),4)
        self.assertEqual(len({q.id for q in QUESTIONS}),12)
        self.assertTrue(all(q.prompt and q.hint for q in QUESTIONS))
    def test_save_and_replace(self):
        item=self.s.save('c1','Minha experiência',[True,False,True,False]); self.assertEqual(item.count,2)
        self.assertEqual(self.s.get('c1'),item)
        self.s.save('c1','Revisada',[False]*4); self.assertEqual(len(self.s.list()),1); self.assertEqual(self.s.get('c1').answer,'Revisada')
    def test_progress(self):
        self.assertEqual(self.s.progress(AREAS[0]),(0,3)); self.s.save('c1','Resposta',[False]*4)
        self.assertEqual(self.s.progress(AREAS[0]),(1,3)); self.assertEqual(self.s.progress(AREAS[1]),(0,3))
        with self.assertRaises(ValueError): self.s.progress('Outra')
    def test_validation_atomic(self):
        saved=self.s.save('c1','Original',[False]*4)
        for args in [('x','x',[False]*4),('c1',' ',[False]*4),('c1','a'*4001,[False]*4),('c1','x\x00',[False]*4),('c1','x',[1]*4),('c1','x',[True])]:
            with self.assertRaises(ValueError): self.s.save(*args)
        self.assertEqual(self.s.get('c1'),saved)
    def test_clear(self):
        for q in QUESTIONS: self.s.save(q.id,'Resposta',[True]*4)
        self.assertEqual(len(self.s.list()),12); self.s.delete('c1'); self.assertIsNone(self.s.get('c1')); self.s.clear(); self.assertFalse(self.s.list())
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Context',True)
            data=json.loads(p.read_text()); data['schema']=46; data.pop('interview_enabled'); p.write_text(json.dumps(data)); s=Settings(p)
            self.assertTrue(s.context_enabled); self.assertFalse(s.interview_enabled); self.assertFalse(s.warning)
            s.set_module('Interview',True); s.set_appearance(Appearance(favorites=('Interview',))); s=Settings(p)
            self.assertTrue(s.interview_enabled); self.assertEqual(s.appearance.favorites,('Interview',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
