"""Fail-closed OSV audit tests with synthetic mocked responses; no network."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / "distribution" / "audit-dependencies.py"
spec = importlib.util.spec_from_file_location("audit_dependencies", PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class Response:
    def __init__(self, data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def geturl(self): return audit.URL
    def read(self,limit): return json.dumps(self.data).encode("utf-8")

class DependencyEvidenceTests(unittest.TestCase):
    def verify(self,response,status,code):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=root/"inventory.txt"
            dest=root/"report.json"
            source.write_text("example==1.0\n",encoding="utf-8")
            with patch.object(audit.urllib.request,"urlopen",return_value=Response(response)):
                self.assertEqual(audit.main(source,dest),code)
            report=json.loads(dest.read_text())
            self.assertEqual(report["status"],status)
            self.assertFalse(report["release_approved"])
    def test_complete_no_advisories(self):
        self.verify({"results":[{}]},"NO_REPORTED_ADVISORIES",0)
    def test_known_advisory(self):
        self.verify({"results":[{"vulns":[{"id":"SYNTHETIC-1"}]}]},"ADVISORIES_FOUND",1)
    def test_incomplete_response(self):
        self.verify({"results":[]},"INCONCLUSIVE",2)
    def test_unavailable_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=root/"inventory.txt"
            dest=root/"report.json"
            source.write_text("example==1.0\n",encoding="utf-8")
            with patch.object(audit.urllib.request,"urlopen",side_effect=OSError("synthetic offline")):
                self.assertEqual(audit.main(source,dest),2)
            self.assertEqual(json.loads(dest.read_text())["status"],"INCONCLUSIVE")
if __name__=="__main__":
    unittest.main()
