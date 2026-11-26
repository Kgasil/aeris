import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from unittest.mock import patch
from aeris.link import inspect_url, LIMIT
from aeris.settings import Settings, Appearance

class LinkTests(unittest.TestCase):
    def test_normal(self):
        result=inspect_url('https://example.org/path?x=1')
        self.assertEqual((result.host,result.scheme,result.indicators),('example.org','https',()))
    def test_credentials(self):
        result=inspect_url('http://login.example.com:fakepassword@verification.example.org:8080/')
        self.assertEqual(result.host,'verification.example.org'); self.assertEqual(len(result.indicators),3)
        self.assertNotIn('fakepassword',str(result))
    def test_ip(self):
        for value in ('http://127.0.0.1','https://[::1]:443','https://127.1','https://0x7f000001'):
            self.assertTrue(inspect_url(value).indicators)
        self.assertEqual(inspect_url('https://[::1]').host,'::1')
    def test_international_and_encoded(self):
        result=inspect_url('https://café.example.org/a%20b?%74oken=SECRET')
        self.assertEqual(result.host,'xn--caf-dma.example.org'); self.assertEqual(len(result.indicators),3)
        self.assertNotIn('SECRET',str(result)); self.assertTrue(inspect_url('https://xn--caf-dma.example.org').indicators)
    def test_rejects_ambiguous(self):
        for value in ('','example.org','file:///tmp/test','javascript:alert(1)','https://a.example\\@b.example','https://example.org\n','https://exam\u200bple.org','https://%65xample.org','https://a@@b.org','https://a.org:99999','https://a.org:','https://[::1]junk','https://a..org','https://-a.org','https://example.org/'+('x'*LIMIT)):
            with self.subTest(value=value[:70]), self.assertRaises(ValueError): inspect_url(value)
    def test_no_network(self):
        with patch('socket.getaddrinfo',side_effect=AssertionError('network')),patch('socket.socket',side_effect=AssertionError('network')):
            self.assertEqual(inspect_url('https://example.org').host,'example.org')
    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Workspace',True)
            raw=json.loads(p.read_text()); raw['schema']=20; del raw['link_enabled']; p.write_text(json.dumps(raw))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.workspace_enabled); self.assertFalse(s.link_enabled)
            s.set_module('Link',True); s.set_appearance(Appearance(favorites=('Link',)))
            self.assertTrue(Settings(p).link_enabled); self.assertEqual(Settings(p).appearance.favorites,('Link',))
