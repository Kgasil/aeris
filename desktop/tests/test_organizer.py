import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.organizer import category, scan_folder, safe_name, Cancelled
from aeris.settings import Settings, Appearance

class OrganizerTests(unittest.TestCase):
    def test_category(self):
        for name,kind in [('REPORT.PDF','Documentos'),('pic.JPG','Imagens'),('data.csv','Planilhas e dados'),('a.tar.gz','Compactados'),('clip.mp4','Áudio e vídeo'),('main.py','Código'),('README','Outros')]:
            self.assertEqual(category(name),kind)
    def test_inventory_and_originals(self):
        with TemporaryDirectory() as d:
            p=Path(d);(p/'a.txt').write_bytes(b'abc');(p/'b.TXT').write_bytes(b'12');(p/'x.png').write_bytes(b'!');(p/'sub').mkdir();(p/'sub'/'inside.txt').write_text('nested')
            r=scan_folder(p)
            self.assertEqual(r.totals,(('Documentos',2,5),('Imagens',1,1)))
            self.assertEqual(r.skipped,1);self.assertFalse(r.truncated)
            self.assertEqual((p/'a.txt').read_bytes(),b'abc');self.assertTrue((p/'sub'/'inside.txt').exists());self.assertEqual(len(list(p.iterdir())),4)
    def test_bound_and_cancel(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            for n in range(4):(p/f'{n}.txt').touch()
            with patch('aeris.organizer.MAX_ENTRIES',2):
                r=scan_folder(p);self.assertTrue(r.truncated);self.assertEqual(len(r.files),2)
            calls=iter([False,False,True])
            with self.assertRaises(Cancelled):scan_folder(p,cancelled=lambda:next(calls))
    def test_links_and_invalid(self):
        with TemporaryDirectory() as d:
            p=Path(d);f=p/'file.txt';f.touch()
            with self.assertRaises(ValueError):scan_folder(f)
            try:(p/'link.txt').symlink_to(f);(p/'alias').symlink_to(p,target_is_directory=True)
            except (OSError,NotImplementedError):return
            r=scan_folder(p);self.assertEqual(len(r.files),1);self.assertEqual(r.skipped,2)
            with self.assertRaises(ValueError):scan_folder(p/'alias')
    def test_safe_display(self):
        self.assertEqual(safe_name('a\n\u202eb.txt'),'a\\u000a\\u202eb.txt')
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Documents',True)
            raw=json.loads(p.read_text());raw['schema']=25;raw.pop('organizer_enabled');p.write_text(json.dumps(raw));s=Settings(p)
            self.assertFalse(s.warning);self.assertTrue(s.documents_enabled);self.assertFalse(s.organizer_enabled)
            s.set_module('Organizer',True);s.set_appearance(Appearance(favorites=('Organizer',)))
            self.assertTrue(Settings(p).organizer_enabled);self.assertEqual(Settings(p).appearance.favorites,('Organizer',))
