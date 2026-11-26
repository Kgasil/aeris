import unittest
from aeris.clipboard import ClipboardStore
from aeris.permissions import Permissions, READ_CLIPBOARD, WRITE_CLIPBOARD
from aeris.settings import Settings, Appearance
from tempfile import TemporaryDirectory
from pathlib import Path
import json

class ClipboardTests(unittest.TestCase):
    def setUp(self):
        self.p = Permissions(); self.store = ClipboardStore(self.p)

    def test_denied_does_not_read_or_write(self):
        calls=[]
        with self.assertRaises(PermissionError): self.store.capture(lambda: calls.append('read'))
        with self.assertRaises(PermissionError): self.store.copy(1, lambda x: calls.append(x))
        self.assertEqual(calls, [])

    def test_search_dedup_pin_and_copy(self):
        self.p.set(READ_CLIPBOARD, True); self.p.set(WRITE_CLIPBOARD, True)
        item=self.store.capture(lambda:'  Olá, Python\n ')
        self.store.pin(item.id)
        self.store.capture(lambda:'Outro')
        self.assertEqual(self.store.capture(lambda:item.text).id,item.id)
        self.assertEqual(len(self.store.list()),2)
        self.assertEqual(self.store.list('ola python')[0].id,item.id)
        self.assertTrue(self.store.list()[0].pinned)
        output=[]; self.store.copy(item.id,output.append); self.assertEqual(output,[item.text])
        self.p.set(WRITE_CLIPBOARD,False)
        with self.assertRaises(PermissionError): self.store.copy(item.id,output.append)
        self.store.delete(item.id); self.assertEqual(len(self.store.list()),1)
        self.store.clear(); self.assertFalse(self.store.list())

    def test_limit_and_pinned_eviction(self):
        self.p.set(READ_CLIPBOARD,True)
        for i in range(50): self.store.capture(lambda:str(i))
        oldest=self.store.list('0')[-1]; self.assertEqual(oldest.text,'0'); self.store.pin(oldest.id)
        self.store.capture(lambda:'new')
        self.assertEqual(len(self.store.list()),50); self.assertTrue(any(x.text=='0' for x in self.store.list())); self.assertFalse(any(x.text=='1' for x in self.store.list()))
        for x in self.store.list():
            if not x.pinned: self.store.pin(x.id)
        with self.assertRaises(ValueError): self.store.capture(lambda:'another')
        self.assertEqual(len(self.store.list()),50)

    def test_invalid_text(self):
        self.p.set(READ_CLIPBOARD,True)
        for value in (' ', None, 'x'*20001):
            with self.assertRaises(ValueError): self.store.capture(lambda:value)
        self.assertFalse(self.store.list())

    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; p.write_text(json.dumps(dict(schema=7,capture_enabled=True,snippets_enabled=True,search_enabled=False,vault_enabled=True,appearance={'favorites':['Vault']})))
            s=Settings(p); self.assertFalse(s.clipboard_enabled); self.assertTrue(s.vault_enabled)
            s.set_module('Clipboard',True); s.set_appearance(Appearance(favorites=('Clipboard','Vault')))
            self.assertTrue(Settings(p).clipboard_enabled); self.assertEqual(Settings(p).appearance.favorites,('Clipboard','Vault'))
            self.assertEqual(json.loads(p.read_text())['schema'],49)
