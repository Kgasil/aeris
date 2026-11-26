import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from aeris.lens import recognize, read_image, engine_path, Cancelled, LANGUAGES, MAX_FILE
from aeris.settings import Settings, Appearance
from aeris.permissions import Permissions, LENS_READ

FIXTURES=Path(__file__).parent/'fixtures'

class LensTests(unittest.TestCase):
    def test_png_jpeg_dimensions(self):
        for ext,fmt in [('png','PNG'),('jpg','JPEG')]:
            data,kind,w,h=read_image(FIXTURES/f'lens_eng.{ext}',lambda:None)
            self.assertEqual((kind,w,h),(fmt,900,200));self.assertTrue(data)
    def test_invalid_and_large(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.png';p.write_bytes(b'bad')
            with self.assertRaises(ValueError):read_image(p,lambda:None)
            with p.open('wb') as f:f.truncate(MAX_FILE+1)
            with self.assertRaisesRegex(ValueError,'8 MiB'):read_image(p,lambda:None)
            data=bytearray((FIXTURES/'lens_eng.png').read_bytes());data[16:24]=struct.pack('>II',6000,6000);p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'megapixels'):read_image(p,lambda:None)
    def test_unsupported_language_cancel_missing(self):
        p=FIXTURES/'lens_eng.png'
        with self.assertRaises(ValueError):recognize(p,'unknown')
        with self.assertRaises(Cancelled):recognize(p,'English',cancelled=lambda:True)
        with patch('aeris.lens.engine_path',side_effect=ValueError('Motor indisponível')):
            with self.assertRaisesRegex(ValueError,'Motor'):recognize(p,'English')
    def test_migration(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Compare',True)
            data=json.loads(p.read_text());data['schema']=28;del data['lens_enabled'];p.write_text(json.dumps(data))
            s=Settings(p);self.assertFalse(s.lens_enabled);self.assertTrue(s.compare_enabled)
            s.set_module('Lens',True);s.set_appearance(Appearance(favorites=('Lens',)))
            s=Settings(p);self.assertTrue(s.lens_enabled);self.assertEqual(s.appearance.favorites,('Lens',))
            self.assertEqual(json.loads(p.read_text())['schema'],49)
            self.assertFalse(Permissions().allowed(LENS_READ))
    def test_real_ocr(self):
        try:exe=engine_path()
        except ValueError:self.skipTest('Optional Tesseract not installed')
        args=[str(exe),'--list-langs']
        if __import__('os').name=='nt':args+=['--tessdata-dir',str(exe.parent/'tessdata')]
        available=subprocess.check_output(args,stderr=subprocess.DEVNULL,timeout=10).decode().splitlines()
        if not all(code in available for code in LANGUAGES.values()):self.skipTest('Optional language models absent')
        for lang,code,expected in [('Português','por','Organização e produtividade'),('English','eng','Local text recognition'),('Español','spa','Organización y productividad')]:
            p=FIXTURES/f'lens_{code}.png';before=p.read_bytes();r=recognize(p,lang)
            self.assertIn(expected,r.text);self.assertEqual(p.read_bytes(),before)
        self.assertIn('Local text recognition',recognize(FIXTURES/'lens_eng.jpg','English').text)
    def test_cancel_running(self):
        from unittest.mock import MagicMock
        proc=MagicMock();proc.__enter__.return_value=proc;proc.poll.return_value=None
        state=[False]
        def communicate(*args,**kwargs):
            if kwargs.get('timeout'):
                state[0]=True;raise subprocess.TimeoutExpired('ocr',.1)
            return b'',None
        proc.communicate.side_effect=communicate
        with patch('aeris.lens.engine_path',return_value=Path('/mock/tesseract')),patch('aeris.lens.subprocess.Popen',return_value=proc):
            with self.assertRaises(Cancelled):recognize(FIXTURES/'lens_eng.png','English',cancelled=lambda:state[0])
        proc.kill.assert_called_once()
