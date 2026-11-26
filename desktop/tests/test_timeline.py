import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from aeris.timeline import TimelineStore, MAX_EVENTS
from aeris.settings import Settings, Appearance


class TimelineTests(unittest.TestCase):
    def setUp(self): self.store=TimelineStore()

    def test_order_and_ties(self):
        a=self.store.add('2026-11-25 09:00','Primeiro','Trabalho')
        b=self.store.add('2026-11-24 20:00','Ontem','Pessoal')
        c=self.store.add('2026-11-25 09:00','Segundo','Estudos')
        self.assertEqual(self.store.list(),(c,a,b))

    def test_filters(self):
        a=self.store.add('2026-11-25 09:00','Revisão','Trabalho','Relatório mensal')
        self.store.add('2026-11-24 20:00','Revisão','Trabalho','Relatório mensal')
        self.store.add('2026-11-25 09:00','Revisão','Estudos','Relatório mensal')
        self.assertEqual(self.store.search('REVISAO relatorio','trabalho','2026-11-25','2026-11-25'),(a,))
        self.assertEqual(len(self.store.search(day_to='2026-11-24')),1)
        with self.assertRaises(ValueError): self.store.search(day_from='2026-11-25',day_to='2026-11-24')
        with self.assertRaises(ValueError): self.store.search(day_from='2026-02-30')

    def test_validation(self):
        for value in ('2026-02-30 09:00','2026-11-25 24:00','2026-11-25T09:00','2026-11-25 09:00+03:00','2026-1-1 01:01'):
            with self.assertRaises(ValueError): self.store.add(value,'Teste','Geral')
        for title,cat,body in (('', 'Geral',''),('Teste','', ''),('a'*161,'Geral',''),('Teste','Geral','x'*2001),('Teste','Geral','\x00')):
            with self.assertRaises(ValueError): self.store.add('2026-11-25 09:00',title,cat,body)
        self.assertFalse(self.store.list())

    def test_edit_delete_and_clear(self):
        a=self.store.add('2026-11-25 09:00','A','Geral')
        b=self.store.add('2026-11-25 10:00','B','Geral')
        with self.assertRaises(ValueError): self.store.edit(a.id,'bad','A','Geral','')
        self.assertEqual(self.store.get(a.id),a)
        c=self.store.edit(a.id,'2026-11-26 10:00','C','Geral','Nota')
        self.assertEqual(self.store.list(),(c,b))
        self.store.delete(c.id); self.assertEqual(self.store.list(),(b,))
        self.store.clear(); self.assertFalse(self.store.list())
        self.assertGreater(self.store.add('2026-11-25 09:00','D','Geral').id,b.id)

    def test_limit(self):
        for i in range(MAX_EVENTS): self.store.add('2026-11-25 09:00',str(i),'Geral')
        with self.assertRaises(ValueError): self.store.add('2026-11-25 09:00','Extra','Geral')
        self.assertEqual(len(self.store.list()),MAX_EVENTS)

    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Ideas',True)
            old=json.loads(p.read_text()); old['schema']=33; old.pop('timeline_enabled'); p.write_text(json.dumps(old))
            s=Settings(p); self.assertTrue(s.ideas_enabled); self.assertFalse(s.timeline_enabled); self.assertFalse(s.warning)
            s.set_module('Timeline',True); s.set_appearance(Appearance(favorites=('Timeline',)))
            s=Settings(p); self.assertTrue(s.timeline_enabled); self.assertEqual(s.appearance.favorites,('Timeline',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
