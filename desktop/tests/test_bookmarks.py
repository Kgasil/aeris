import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.bookmarks import BookmarkStore, validate_url
from aeris.permissions import Permissions, OPEN_BOOKMARK
from aeris.settings import Appearance, Settings
from tests.test_vault import TestBackend

class BookmarksTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'bookmarks.bin'
        self.permissions=Permissions(); self.opened=[]
        self.store=BookmarkStore(self.path,self.permissions,TestBackend(),self.opened.append)
        self.addCleanup(self.store.lock)

    def test_valid_urls(self):
        for url in ('https://example.com/docs?q=abc#item','http://localhost:8000','https://[::1]/','https://exemplo.com.br/','https://exemplo.com/a%20b'):
            self.assertEqual(validate_url(url),url)

    def test_invalid_urls(self):
        for url in ('file:///C:/test','javascript:alert(1)','mailto:a@example.com','data:text/html,x','ftp://example.com','https://user:pass@example.com','https://','https://example.com\\@evil.test','https://example.com\n','https://exa mple.com','https://example.com:99999','https://%65xample.com','https://a..b','https://-abc.com','https://a\u202eb.com'):
            with self.subTest(url=url), self.assertRaises(ValueError): validate_url(url)

    def test_persist_edit_search_delete_and_lock(self):
        with self.assertRaises(PermissionError): self.store.list()
        self.store.unlock(); first=self.store.save('Documentação','Estudos','https://example.com')
        self.assertEqual(self.store.list('documentacao ESTUDOS'),(first,))
        self.assertEqual(self.store.list(category='Estudos'),(first,))
        self.assertEqual(self.store.list(category='Trabalho'),())
        self.store.lock(); self.store.unlock(); self.assertEqual(self.store.get(first.id),first)
        edited=self.store.save('Novo','Trabalho','https://example.org',first.id)
        self.assertEqual(self.store.list(),(edited,))
        self.store.delete(first.id); self.store.lock(); self.store.unlock(); self.assertEqual(self.store.list(),())

    def test_duplicate_and_bad_fields(self):
        self.store.unlock(); item=self.store.save('Exemplo','Geral','https://example.com')
        for args in [('Outro','Geral',item.url),('','Geral',item.url),('A','','https://example.org'),('A','Geral','file:///test')]:
            with self.assertRaises(ValueError): self.store.save(*args)
        self.assertEqual(self.store.list(),(item,))

    def test_launch_permission_and_revocation(self):
        self.store.unlock(); item=self.store.save('A','B','https://example.com')
        with self.assertRaises(PermissionError): self.store.open(item.id)
        self.assertEqual(self.opened,[])
        self.permissions.set(OPEN_BOOKMARK,True); self.store.open(item.id)
        self.assertEqual(self.opened,[item.url]); self.permissions.revoke_all()
        with self.assertRaises(PermissionError): self.store.open(item.id)
        self.assertEqual(self.opened,[item.url])

    def test_corrupt_record_does_not_overwrite(self):
        self.store.vault.unlock(); self.store.vault.save('A','not JSON'); self.store.lock()
        original=self.path.read_bytes()
        with self.assertRaises(ValueError): self.store.unlock()
        self.assertFalse(self.store.unlocked); self.assertEqual(self.path.read_bytes(),original)

    def test_migrate_settings8(self):
        path=self.path.parent/'settings.json'
        path.write_text(json.dumps(dict(schema=8,capture_enabled=True,snippets_enabled=False,search_enabled=True,vault_enabled=True,clipboard_enabled=True,appearance={'favorites':['Clipboard']})))
        settings=Settings(path); self.assertFalse(settings.bookmarks_enabled); self.assertTrue(settings.clipboard_enabled)
        settings.set_module('Bookmarks',True); settings.set_appearance(Appearance(favorites=('Bookmarks','Clipboard')))
        loaded=Settings(path); self.assertTrue(loaded.bookmarks_enabled and loaded.capture_enabled and loaded.clipboard_enabled)
        self.assertEqual(loaded.appearance.favorites,('Bookmarks','Clipboard'))
        self.assertEqual(json.loads(path.read_text())['schema'],49)
