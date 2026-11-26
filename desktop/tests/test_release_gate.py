import importlib.util
import json
from pathlib import Path
import unittest

from aeris import __version__

ROOT = Path(__file__).resolve().parents[2] / 'distribution'
spec = importlib.util.spec_from_file_location('release_gate', ROOT / 'release-gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'release-gate.json').read_text(encoding='utf-8'))

    def test_pending_record_blocks_release(self):
        for value in self.record['checks'].values():
            value.update(status='pending', evidence='')
        self.assertEqual(set(gate.pending_checks(self.record, __version__)), gate.REQUIRED)

    def test_missing_check_and_wrong_version(self):
        with self.assertRaises(ValueError):
            gate.pending_checks(self.record, 'invalid')
        self.record['checks'].pop('windows_build_x64')
        with self.assertRaises(ValueError):
            gate.pending_checks(self.record, __version__)

    def test_pass_without_evidence_does_not_clear_gate(self):
        for value in self.record['checks'].values():
            value.update(status='passed', evidence='synthetic fixture')
        self.assertEqual(gate.pending_checks(self.record, __version__), [])
        self.record['checks']['native_dpapi_mutex']['evidence'] = '  '
        self.assertEqual(gate.pending_checks(self.record, __version__), ['native_dpapi_mutex'])
