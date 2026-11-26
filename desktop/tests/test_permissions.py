import unittest
from aeris.permissions import Permissions, CAPABILITIES, SEARCH_CAPTURE, COPY_SNIPPETS

class PermissionTests(unittest.TestCase):
    def test_denied_default(self):
        p=Permissions()
        self.assertFalse(any(p.allowed(c) for c in CAPABILITIES))
        with self.assertRaises(PermissionError): p.require(SEARCH_CAPTURE)

    def test_grant_revoke_and_isolation(self):
        calls=[]; p=Permissions(lambda: calls.append(True))
        p.set(SEARCH_CAPTURE, True); p.require(SEARCH_CAPTURE)
        self.assertFalse(p.allowed(COPY_SNIPPETS)); self.assertFalse(Permissions().allowed(SEARCH_CAPTURE))
        p.set(SEARCH_CAPTURE,False); self.assertFalse(p.allowed(SEARCH_CAPTURE)); self.assertEqual(len(calls),2)

    def test_revoke_all_and_invalid(self):
        p=Permissions()
        for cap in CAPABILITIES: p.set(cap,True)
        p.revoke_all(); self.assertFalse(any(p.allowed(c) for c in CAPABILITIES))
        with self.assertRaises(ValueError): p.set('unknown',True)
        with self.assertRaises(ValueError): p.set(COPY_SNIPPETS,1)
