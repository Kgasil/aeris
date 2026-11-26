import unittest
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from aeris.bridge import Bridge
from aeris.content import CaptureStore, SnippetStore
from aeris.permissions import Permissions, BRIDGE_CAPTURE, BRIDGE_SNIPPETS, BRIDGE_RUN, BRIDGE_SAVE
from aeris.settings import Settings

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.enabled={'Bridge','Expand','Text','Translate','Email','Capture','Snippets'}
        self.h=SimpleNamespace(enabled=lambda n:n in self.enabled,permissions=Permissions(),capture_store=CaptureStore(),snippets_store=SnippetStore(),expand_store=None,capture_window=None,alive=lambda w:False,invalidate_search=lambda:None)
        self.b=Bridge(self.h)
    def test_denied_and_disabled(self):
        with self.assertRaises(PermissionError): self.b.run('Expand → Text',';att')
        self.h.permissions.set(BRIDGE_RUN,True); self.enabled.remove('Expand')
        with self.assertRaises(PermissionError): self.b.run('Expand → Text',';att')
    def test_import_grants(self):
        note=self.h.capture_store.save('A','Bom dia!')
        self.h.permissions.set(BRIDGE_CAPTURE,True)
        self.assertEqual(self.b.records('Capture'),(note,))
        with self.assertRaises(PermissionError): self.b.records('Snippets')
        self.h.permissions.set(BRIDGE_RUN,True); self.h.permissions.set(BRIDGE_CAPTURE,False)
        with self.assertRaises(PermissionError): self.b.run('Translate → Email',note.body,'Capture')
    def test_expand_text(self):
        self.h.permissions.set(BRIDGE_RUN,True)
        self.assertEqual(self.b.run('Expand → Text','  ;att   ').text,'Atenciosamente,')
        self.h.expand_store.save(';test','Olá  mundo')
        self.assertEqual(self.b.run('Expand → Text',';test').text,'Olá mundo')
    def test_translate_email(self):
        self.h.permissions.set(BRIDGE_RUN,True)
        p=self.b.run('Translate → Email','Bom dia!')
        self.assertEqual(p.subject,'Update'); self.assertIn('Good morning!',p.text)
        with self.assertRaises(ValueError): self.b.run('Translate → Email','Uma frase desconhecida.')
    def test_capture_write(self):
        self.h.permissions.set(BRIDGE_RUN,True)
        p=self.b.run('Text → Capture','Olá   mundo')
        self.assertEqual(self.h.capture_store.list(),())
        with self.assertRaises(PermissionError): self.b.save_capture(p,'A')
        self.h.permissions.set(BRIDGE_SAVE,True)
        self.assertEqual(self.b.save_capture(p,'A').body,'Olá mundo')
        self.h.permissions.set(BRIDGE_RUN,False)
        with self.assertRaises(PermissionError): self.b.save_capture(p,'B')
    def test_migrate(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Expand',True)
            data=json.loads(p.read_text()); data['schema']=17; del data['bridge_enabled']; p.write_text(json.dumps(data))
            s=Settings(p); self.assertTrue(s.expand_enabled); self.assertFalse(s.bridge_enabled)
            s.set_module('Bridge',True); self.assertTrue(Settings(p).bridge_enabled)
