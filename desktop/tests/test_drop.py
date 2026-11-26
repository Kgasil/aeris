import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from aeris.drop import DropStore, Reference, inspect_paths, Cancelled
from aeris.settings import Settings, Appearance

class DropTests(unittest.TestCase):
    def test_metadata_only(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'example.csv';p.write_bytes(b'a,b')
            with patch('pathlib.Path.open',side_effect=AssertionError('content read')):
                items=inspect_paths([str(p)])
            self.assertEqual(items,(Reference(str(p),3,'Planilhas e dados'),))
            self.assertEqual(p.read_bytes(),b'a,b')
    def test_invalid_paths(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a';p.touch()
            with self.assertRaises(ValueError):inspect_paths([d])
            with self.assertRaises(ValueError):inspect_paths(['relative.txt'])
            with self.assertRaises(OSError):inspect_paths([str(Path(d)/'absent')])
            with self.assertRaises(ValueError):inspect_paths([str(p)]*101)
    def test_symlink(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a';p.touch();link=Path(d)/'link'
            try:link.symlink_to(p)
            except OSError:self.skipTest('Symlink unavailable')
            with self.assertRaises(ValueError):inspect_paths([str(link)])
    def test_cancel(self):
        with self.assertRaises(Cancelled):inspect_paths(['unused'],cancelled=lambda:True)
    def test_store(self):
        s=DropStore();a=Reference('/a',1,'Outros');b=Reference('/b',2,'Outros');s.add((a,b,a));self.assertEqual(s.list(),(a,b));s.remove(['/a']);self.assertEqual(s.list(),(b,))
        with self.assertRaises(ValueError):s.add(tuple(Reference(f'/item{i}',1,'Outros') for i in range(100)))
        self.assertEqual(s.list(),(b,));s.clear();self.assertFalse(s.list())
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Organizer',True)
            data=json.loads(p.read_text());data['schema']=26;data.pop('drop_enabled');p.write_text(json.dumps(data));s=Settings(p)
            self.assertFalse(s.warning);self.assertTrue(s.organizer_enabled);self.assertFalse(s.drop_enabled)
            s.set_module('Drop',True);s.set_appearance(Appearance(favorites=('Drop',)));self.assertTrue(Settings(p).drop_enabled);self.assertEqual(Settings(p).appearance.favorites,('Drop',))
