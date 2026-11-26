import unittest
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
from dataclasses import asdict
import json
from aeris.flashcards import FlashcardsStore, MAX_CARDS, MAX_INTERVAL, DAY
from aeris.settings import Settings, FLAGS, Appearance

class FlashcardsTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,1,1,tzinfo=timezone.utc)
        self.s=FlashcardsStore(lambda:self.now)
    def test_creation_search_edit_delete(self):
        c=self.s.add('Ciência','O que é automação?','Uma técnica útil')
        self.assertEqual(self.s.search('automacao util','CIENCIA',True),(c,))
        self.assertFalse(self.s.search('ausente'))
        self.assertEqual(self.s.edit(c.id,'Outra',c.question,c.answer).deck,'Outra')
        self.s.delete(c.id); self.assertFalse(self.s.list())
    def test_intervals_and_duplicate(self):
        c=self.s.add('Geral','Q','A')
        c=self.s.review(c.id,'Médio'); self.assertEqual(c.interval,DAY); self.assertEqual(c.due,self.now+timedelta(days=1)); self.assertEqual(c.reviews,1)
        with self.assertRaises(ValueError): self.s.review(c.id,'Fácil')
        self.assertFalse(self.s.search(due_only=True)); self.now=c.due
        c=self.s.review(c.id,'Médio'); self.assertEqual(c.interval,2*DAY)
        self.now=c.due; c=self.s.review(c.id,'Fácil'); self.assertEqual(c.interval,6*DAY)
        self.now=c.due; c=self.s.review(c.id,'Difícil'); self.assertEqual(c.interval,600); self.assertEqual(c.reviews,4)
    def test_cap(self):
        c=self.s.add('G','Q','A')
        for _ in range(20):
            self.now=c.due; c=self.s.review(c.id,'Fácil')
        self.assertEqual(c.interval,MAX_INTERVAL)
    def test_edit_resets_content_not_deck(self):
        c=self.s.add('G','Q','A'); c=self.s.review(c.id,'Fácil')
        moved=self.s.edit(c.id,'Novo','Q','A'); self.assertEqual(moved.due,c.due); self.assertEqual(moved.reviews,1)
        edited=self.s.edit(c.id,'Novo','Q','B'); self.assertEqual(edited.due,self.now); self.assertEqual(edited.reviews,0); self.assertEqual(edited.interval,0)
    def test_limits_and_validation(self):
        for args in [('', 'Q','A'),('G','','A'),('G','Q',' '),('G','Q','x'*4001),('G','Q\x00','A')]:
            with self.assertRaises(ValueError): self.s.add(*args)
        for _ in range(MAX_CARDS): c=self.s.add('G','Q','A')
        with self.assertRaises(ValueError): self.s.add('G','Q','A')
        with self.assertRaises(ValueError): self.s.review(c.id,'wrong')
        self.s.clear(); self.assertFalse(self.s.list()); self.assertGreater(self.s.add('G','Q','A').id,MAX_CARDS)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; data={k:False for k in FLAGS[:-1]}; data.update(schema=41,research_enabled=True,appearance=asdict(Appearance(favorites=('Research',)))); p.write_text(json.dumps(data))
            s=Settings(p); self.assertFalse(s.flashcards_enabled); self.assertTrue(s.research_enabled)
            s.set_module('Flashcards',True); s.set_appearance(Appearance(favorites=('Flashcards',))); s=Settings(p)
            self.assertTrue(s.flashcards_enabled and s.research_enabled); self.assertEqual(s.appearance.favorites,('Flashcards',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
