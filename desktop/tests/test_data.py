import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.data import profile_file, profile_text, Cancelled
from aeris.settings import Settings, Appearance

class DataTests(unittest.TestCase):
    def test_profile(self):
        p=profile_text('Nome;Valor;Vazio\nA;1,5;\nB;2,5; \nB;2,5; \nC;;\n',';',',')
        self.assertEqual((p.rows,p.duplicates,p.missing),(4,1,5))
        name,value,empty=p.columns
        self.assertEqual((name.kind,name.distinct),('Texto/mista',3))
        self.assertEqual((value.minimum,value.maximum,value.distinct,value.missing),(Decimal('1.5'),Decimal('2.5'),2,1))
        self.assertAlmostEqual(float(value.mean),6.5/3)
        self.assertEqual((empty.kind,empty.distinct,empty.mean),('Vazia',0,None))
    def test_quoted_and_multiline(self):
        p=profile_text('text,value\n"hello, world\nnext line",-2\n"hello, world\nnext line",4\n')
        self.assertEqual((p.rows,p.columns[0].distinct,p.columns[1].mean),(2,1,Decimal(1)))
    def test_invalid(self):
        for text in ('','a,a\n1,2','a, \n1,2','a,b\n1','a\n"unclosed','a\n'+('x'*4097),'a\n'+('1\n'*5001)):
            with self.subTest(text=text[:40]),self.assertRaises(ValueError):profile_text(text)
        with self.assertRaises(ValueError):profile_text('a\n1', '|')
    def test_empty_and_mixed(self):
        self.assertEqual(profile_text('a,b\n').rows,0)
        p=profile_text('a,b\n1,NA\n2,2\n3,=1+1\n')
        self.assertEqual(p.columns[0].mean,Decimal(2));self.assertEqual(p.columns[1].kind,'Texto/mista');self.assertIsNone(p.columns[1].mean)
    def test_file_encoding_unchanged(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'example.csv'; raw='Mês;Valor\nJaneiro;2,5\n'.encode('utf-16');p.write_bytes(raw)
            self.assertEqual(profile_file(p,';',',').columns[1].mean,Decimal('2.5'));self.assertEqual(p.read_bytes(),raw)
            p.write_bytes(b'\xff');self.assertRaises(ValueError,profile_file,p)
            p.write_bytes(b'x'*(1024*1024+1));self.assertRaises(ValueError,profile_file,p)
    def test_cancel_and_limits(self):
        with self.assertRaises(Cancelled):profile_text('a\n1',cancelled=lambda:True)
        with patch('aeris.data.MAX_CELLS',3):
            with self.assertRaises(ValueError):profile_text('a,b\n1,2\n3,4')
    def test_settings(self):
        import json
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Timeline',True)
            raw=json.loads(p.read_text());raw['schema']=34;raw.pop('data_enabled');p.write_text(json.dumps(raw))
            s=Settings(p);self.assertTrue(s.timeline_enabled);self.assertFalse(s.data_enabled);self.assertFalse(s.warning)
            s.set_module('Data',True);s.set_appearance(Appearance(favorites=('Data',)));self.assertTrue(Settings(p).data_enabled);self.assertEqual(Settings(p).appearance.favorites,('Data',))
