import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.dashboard import dataset_text,dataset_file,aggregate,Cancelled
from aeris.settings import Settings,Appearance
import json

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.d=dataset_text('grupo;valor\nA;1,5\nA;2,5\nB;-3\nB;\n;9\n',';',',')
    def test_count(self):
        r=aggregate(self.d,0,'Contagem');self.assertEqual((r.included,r.skipped,r.overall),(4,1,4));self.assertEqual([g.value for g in r.groups],[2,2])
    def test_sum_negative(self):
        r=aggregate(self.d,0,'Soma',1);self.assertEqual((r.included,r.skipped,r.overall),(3,2,1));self.assertEqual([(g.name,g.value) for g in r.groups],[('A',4),('B',-3)])
    def test_mean_weighted(self):
        r=aggregate(self.d,0,'Média',1);self.assertEqual(r.groups[0].value,2);self.assertAlmostEqual(float(r.overall),1/3)
    def test_empty_invalid(self):
        self.assertIsNone(aggregate(dataset_text('x\n'),0,'Contagem').overall)
        for args in ((-1,'Contagem'),(0,'Soma',0),(0,'bad'),(0,'Média',None)):
            with self.assertRaises(ValueError):aggregate(self.d,*args)
    def test_group_limit_and_csv_validation(self):
        with patch('aeris.dashboard.MAX_GROUPS',1),self.assertRaises(ValueError):aggregate(self.d,0,'Contagem')
        with self.assertRaises(ValueError):dataset_text('a,b\n1')
        with self.assertRaises(Cancelled):dataset_text('a\n1',cancelled=lambda:True)
    def test_file_and_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'demo.csv';raw=b'group,value\nA,2\nA,2\n';p.write_bytes(raw)
            self.assertEqual(aggregate(dataset_file(p),0,'Soma',1).overall,Decimal(4));self.assertEqual(p.read_bytes(),raw)
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Data',True);old=json.loads(p.read_text());old['schema']=35;old.pop('dashboard_enabled');p.write_text(json.dumps(old));s=Settings(p);self.assertTrue(s.data_enabled);self.assertFalse(s.dashboard_enabled);self.assertFalse(s.warning);s.set_module('Dashboard',True);s.set_appearance(Appearance(favorites=('Dashboard',)));self.assertTrue(Settings(p).dashboard_enabled)
