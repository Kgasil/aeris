import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.compare import compare_texts, compare_files, Cancelled, MAX_CHARS, MAX_LINES
from aeris.settings import Settings, Appearance

class CompareTests(unittest.TestCase):
    def test_replace_and_numbering(self):
        r=compare_texts('a\nb\nc\n','a\nB\nc\nd\n')
        self.assertEqual((r.kept,r.removed,r.added),(2,1,2))
        self.assertEqual([(x.kind,x.old,x.new) for x in r.rows],[(' ',1,1),('-',2,None),('+',None,2),(' ',3,3),('+',None,4)])
    def test_empty_and_repeated(self):
        self.assertEqual(compare_texts('','').rows,())
        r=compare_texts('a\n'*300,'a\n'*301);self.assertEqual((r.kept,r.removed,r.added),(300,0,1))
    def test_whitespace_and_final_newline(self):
        self.assertEqual(compare_texts('a\r\nb\r','a\nb\n').kept,2)
        self.assertEqual(compare_texts('a','a\n').removed,1)
        self.assertEqual(compare_texts('a ','a').added,1)
        self.assertEqual(compare_texts('\n','').removed,1)
    def test_bounds_and_cancel(self):
        for text in ('a'*(MAX_CHARS+1),'\n'*(MAX_LINES+1)):
            with self.assertRaises(ValueError):compare_texts(text,'')
        with self.assertRaises(Cancelled):compare_texts('a','b',cancelled=lambda:True)
    def test_files_unchanged(self):
        with TemporaryDirectory() as d:
            a=Path(d)/'a.txt';b=Path(d)/'b.md';a.write_bytes(b'a\r\nb');b.write_bytes(b'a\nB')
            self.assertEqual(compare_files(a,b).kept,1);self.assertEqual(a.read_bytes(),b'a\r\nb');self.assertEqual(b.read_bytes(),b'a\nB')
    def test_reject_truncation_and_unsupported(self):
        with TemporaryDirectory() as d:
            a=Path(d)/'a.txt';b=Path(d)/'b.txt';a.write_text('a'*(MAX_CHARS+1));b.write_text('b')
            with self.assertRaisesRegex(ValueError,'truncado'):compare_files(a,b)
            c=Path(d)/'c.pdf';c.write_bytes(b'abc')
            with self.assertRaises(ValueError):compare_files(b,c)
    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Drop',True)
            data=json.loads(p.read_text());data['schema']=27;data.pop('compare_enabled');p.write_text(json.dumps(data));s=Settings(p)
            self.assertFalse(s.warning);self.assertTrue(s.drop_enabled);self.assertFalse(s.compare_enabled)
            s.set_module('Compare',True);s.set_appearance(Appearance(favorites=('Compare',)))
            self.assertTrue(Settings(p).compare_enabled);self.assertEqual(Settings(p).appearance.favorites,('Compare',))
