import json, struct, unittest, zipfile, zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.metadata import inspect_file, MAX_FILE, MAX_XML, Cancelled
from aeris.settings import Settings, Appearance

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
def png_sample():
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',12,34,8,2,0,0,0))+chunk(b'tEXt',b'Author\0Example')+chunk(b'zTXt',b'ignored')+chunk(b'IEND',b'')
def segment(marker,data): return b'\xff'+bytes([marker])+struct.pack('>H',len(data)+2)+data
CORE=b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>Example</dc:creator><cp:lastModifiedBy>Editor</cp:lastModifiedBy></cp:coreProperties>'
class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.p=Path(self.temp.name)/'sample.bin'
    def put(self,data): self.p.write_bytes(data); return self.p
    def package(self,entry,xml=CORE):
        with zipfile.ZipFile(self.p,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml','fake'); z.writestr(entry,'fake'); z.writestr('docProps/core.xml',xml)
        return self.p
    def test_png_read_only(self):
        data=png_sample(); result=inspect_file(self.put(data)); self.assertEqual(result.format,'PNG'); self.assertIn(('Dimensões','12 × 34'),result.fields); self.assertIn(('Texto PNG: Author','Example'),result.fields); self.assertTrue(result.notes); self.assertEqual(self.p.read_bytes(),data)
    def test_jpeg_exif_both_byte_orders(self):
        for order,marker in [('<',b'II'),('>',b'MM')]:
            t=marker+struct.pack(order+'HIH',42,8,2)+struct.pack(order+'HHI',0x010f,2,4)+b'Cam\0'+struct.pack(order+'HHII',0x8825,4,1,38)+struct.pack(order+'I',0)
            r=inspect_file(self.put(b'\xff\xd8'+segment(0xe1,b'Exif\0\0'+t)+segment(0xc0,b'\x08\x00\x22\x00\x0c')+b'\xff\xd9'))
            self.assertIn(('Fabricante','Cam'),r.fields); self.assertIn(('Dimensões','12 × 34'),r.fields); self.assertTrue(any('GPS' in n for n in r.notes))
    def test_office_variants(self):
        for entry,fmt in [('word/document.xml','DOCX'),('xl/workbook.xml','XLSX'),('ppt/presentation.xml','PPTX')]:
            r=inspect_file(self.package(entry)); self.assertEqual(r.format,fmt); self.assertIn(('Autor','Example'),r.fields); self.assertIn(('Última edição por','Editor'),r.fields)
    def test_xml_limits_and_dtd(self):
        for xml in [b' '* (MAX_XML+1),b'<!DOCTYPE a [<!ENTITY b "secret">]>'+CORE,CORE.decode().encode('utf-16')]:
            with self.assertRaises(ValueError): inspect_file(self.package('word/document.xml',xml))
    def test_invalid_and_cancel(self):
        for data in [b'abc',png_sample()[:-2],b'\xff\xd8\xff\xe1\xff\xff',b'PK\x03\x04invalid']:
            with self.assertRaises(ValueError): inspect_file(self.put(data))
        with self.assertRaises(Cancelled): inspect_file(self.put(png_sample()),cancelled=lambda:True)
    def test_file_cap(self):
        with self.p.open('wb') as f: f.truncate(MAX_FILE+1)
        with self.assertRaises(ValueError): inspect_file(self.p)
    def test_migrate_settings(self):
        s=Settings(self.p); s.set_module('Verify',True); data=json.loads(self.p.read_text()); data['schema']=22; del data['metadata_enabled']; self.p.write_text(json.dumps(data))
        s=Settings(self.p); self.assertFalse(s.warning); self.assertTrue(s.verify_enabled); self.assertFalse(s.metadata_enabled); s.set_module('Metadata',True); s.set_appearance(Appearance(favorites=('Metadata',))); self.assertTrue(Settings(self.p).metadata_enabled)
