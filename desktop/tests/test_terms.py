import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aeris.terms import accepted, require_acceptance, read_terms

class TermsTests(unittest.TestCase):
    def test_decline_no_data(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"new"/"receipt.json"
            self.assertFalse(require_acceptance(p,lambda t,h:False))
            self.assertFalse(p.parent.exists())
    def test_accept_and_reuse(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"receipt.json"
            self.assertTrue(require_acceptance(p,lambda t,h:True))
            self.assertTrue(accepted(p,read_terms()[1]))
            self.assertEqual(set(json.loads(p.read_text())),{"schema","terms_sha256","accepted_utc"})
            self.assertTrue(require_acceptance(p,lambda t,h:self.fail("unexpected prompt")))
    def test_new_terms_require_consent(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"receipt.json"
            require_acceptance(p,lambda t,h:True)
            with patch("aeris.terms.read_terms",return_value=("changed","a"*64)):
                self.assertFalse(require_acceptance(p,lambda t,h:False))
                self.assertTrue(require_acceptance(p,lambda t,h:True))
                self.assertTrue(accepted(p,"a"*64))
    def test_corrupt_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"receipt.json";p.write_text("bad")
            self.assertFalse(require_acceptance(p,lambda t,h:False))
    def test_missing_terms_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"receipt.json"
            with patch("aeris.terms.terms_path",return_value=Path(root)/"missing"):
                with self.assertRaises(OSError): require_acceptance(p,lambda t,h:self.fail("unexpected prompt"))
