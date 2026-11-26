import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile
from aeris.documents import extract_file, MAX_PREVIEW, MAX_TEXT_BYTES, MAX_XML, W, Cancelled
from aeris.settings import Settings, Appearance


def sample_docx(path, xml=None):
    if xml is None:
        xml=f'<w:document xmlns:w="{W[1:-1]}"><w:body><w:p><w:r><w:t>Olá</w:t><w:tab/><w:t>mundo</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Célula</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types/>'); z.writestr('word/document.xml',xml)

class DocumentsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.dir=Path(self.tmp.name)
    def test_plain_formats(self):
        for ext in ('txt','md','csv'):
            p=self.dir/('sample.'+ext); raw='Olá mundo\r\nlinha 2'.encode('utf-8-sig');p.write_bytes(raw)
            r=extract_file(p);self.assertEqual((r.format,r.text,r.words,r.lines),(ext.upper(),'Olá mundo\nlinha 2',4,2));self.assertEqual(p.read_bytes(),raw)
        p.write_bytes('Olá'.encode('utf-16'));self.assertEqual(extract_file(p).text,'Olá')
    def test_docx(self):
        p=self.dir/'sample.docx';sample_docx(p);raw=p.read_bytes();self.assertEqual(extract_file(p).text,'Olá\tmundo\nCélula');self.assertEqual(p.read_bytes(),raw)
    def test_limit_and_control(self):
        p=self.dir/'sample.txt';p.write_text('x'*(MAX_PREVIEW+1),encoding='utf-8');r=extract_file(p);self.assertTrue(r.truncated);self.assertEqual(len(r.text),MAX_PREVIEW)
        p.write_text('a\u202eb',encoding='utf-8');self.assertEqual(extract_file(p).text,'a\ufffdb')
        p.write_bytes(b'a'*(MAX_TEXT_BYTES+1));self.assertRaises(ValueError,extract_file,p)
    def test_invalid(self):
        p=self.dir/'binary.txt';p.write_bytes(b'\0abc');self.assertRaises(ValueError,extract_file,p)
        p.write_bytes(b'\xff');self.assertRaises(ValueError,extract_file,p)
        p=self.dir/'sample.pdf';p.write_bytes(b'%PDF-1.4');self.assertRaises(ValueError,extract_file,p)
        p=self.dir/'invalid.docx';p.write_bytes(b'not zip');self.assertRaises(ValueError,extract_file,p)
    def test_xml_rejection(self):
        p=self.dir/'sample.docx';sample_docx(p,'<!DOCTYPE x [<!ENTITY y "secret">]><x>&y;</x>');self.assertRaises(ValueError,extract_file,p)
        sample_docx(p,'x'*(MAX_XML+1));self.assertRaises(ValueError,extract_file,p)
    def test_cancel(self):
        p=self.dir/'sample.txt';p.write_text('abc');self.assertRaises(Cancelled,lambda:extract_file(p,cancelled=lambda:True))
        p=self.dir/'sample.docx';sample_docx(p); checks=iter([False,False,True]);self.assertRaises(Cancelled,lambda:extract_file(p,cancelled=lambda:next(checks,True)))
    def test_schema_migration(self):
        p=self.dir/'settings.json';s=Settings(p);self.assertFalse(s.documents_enabled);s.set_module('Health',True)
        raw=json.loads(p.read_text());raw['schema']=24;raw.pop('documents_enabled');p.write_text(json.dumps(raw));s=Settings(p);self.assertFalse(s.warning);self.assertTrue(s.health_enabled);self.assertFalse(s.documents_enabled)
        s.set_module('Documents',True);s.set_appearance(Appearance(favorites=('Documents',)));self.assertTrue(Settings(p).documents_enabled)
