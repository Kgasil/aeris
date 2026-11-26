import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.learn import LearnStore,MAX_PLANS,MAX_TOPICS
from aeris.settings import Settings,Appearance

class LearnTests(unittest.TestCase):
    def setUp(self):
        self.s=LearnStore();self.p=self.s.create('Python').id
    def test_progress(self):
        a=self.s.add(self.p,'Fundamentos',30);b=self.s.add(self.p,'APIs',90)
        self.assertEqual(self.s.progress(self.p),(0,2,0,120))
        self.s.toggle(self.p,b.id);self.assertEqual(self.s.progress(self.p),(1,2,90,120))
        self.s.toggle(self.p,b.id);self.assertEqual(self.s.progress(self.p),(0,2,0,120))
    def test_edit_and_order(self):
        a=self.s.add(self.p,'A',10);b=self.s.add(self.p,'B',20)
        self.assertFalse(self.s.move(self.p,a.id,-1));self.assertTrue(self.s.move(self.p,b.id,-1))
        self.s.toggle(self.p,b.id);self.s.edit(self.p,b.id,'Novo',25)
        self.assertEqual([(t.title,t.minutes,t.done) for t in self.s.get(self.p).topics],[('Novo',25,True),('A',10,False)])
        self.s.delete_topic(self.p,a.id);self.assertEqual(self.s.progress(self.p),(1,1,25,25))
    def test_unique_names(self):
        self.s.rename(self.p,'Ciência');self.assertEqual(self.s.get(self.p).title,'Ciência')
        with self.assertRaises(ValueError):self.s.create(' ciencia ')
        p2=self.s.create('SQL').id
        with self.assertRaises(ValueError):self.s.rename(p2,'CIÊNCIA')
        self.assertEqual(self.s.get(p2).title,'SQL')
    def test_isolation_and_clear(self):
        p2=self.s.create('SQL').id;t=self.s.add(self.p,'A',10)
        with self.assertRaises(KeyError):self.s.toggle(p2,t.id)
        self.s.delete_plan(self.p);self.assertEqual(self.s.progress(p2),(0,0,0,0));self.s.clear();self.assertFalse(self.s.list())
        self.assertGreater(self.s.create('Nova').id,t.id)
    def test_validation_and_limits(self):
        for name in ('','x'*101,'a\n'):
            with self.assertRaises(ValueError):self.s.create(name)
        for title,mins in [('A',True),('A',0),('A',1441),('A',1.5),('',20),('x'*201,10)]:
            with self.assertRaises(ValueError):self.s.add(self.p,title,mins)
        for n in range(MAX_TOPICS):self.s.add(self.p,str(n),1)
        with self.assertRaises(ValueError):self.s.add(self.p,'Extra',1)
        for n in range(MAX_PLANS-1):self.s.create(str(n))
        with self.assertRaises(ValueError):self.s.create('Extra')
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Convert',True)
            data=json.loads(p.read_text());data['schema']=39;data.pop('learn_enabled');p.write_text(json.dumps(data))
            s=Settings(p);self.assertFalse(s.learn_enabled);self.assertTrue(s.convert_enabled)
            s.set_module('Learn',True);s.set_appearance(Appearance(favorites=('Learn',)))
            s=Settings(p);self.assertTrue(s.learn_enabled);self.assertEqual(s.appearance.favorites,('Learn',));self.assertEqual(json.loads(p.read_text())['schema'],49)
