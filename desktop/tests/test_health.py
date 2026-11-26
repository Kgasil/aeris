import sys
import time
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from aeris.health import Sample, measure, resident_memory, windows_memory, sample
from aeris.settings import Settings, Appearance

class HealthTests(unittest.TestCase):
    def test_cpu_single_core_scale(self):
        result=measure(Sample(10,2),Sample(12,2.5),1048576)
        self.assertEqual((result.seconds,result.cpu_percent,result.resident_bytes),(2,25,1048576))
        self.assertEqual(measure(Sample(1,1),Sample(2,3),None).cpu_percent,200)

    def test_bad_samples(self):
        for end in (Sample(1,1),Sample(0,1),Sample(2,0),Sample(float('nan'),1)):
            with self.assertRaises(ValueError): measure(Sample(1,1),end,None)
        with self.assertRaises(ValueError): measure(Sample(1,1),Sample(2,1),-1)

    def test_unknown_platform(self):
        with patch('aeris.health.sys.platform','unknown'): self.assertIsNone(resident_memory())

    def test_memory_failure(self):
        with patch('aeris.health.sys.platform','win32'),patch('aeris.health.windows_memory',side_effect=OSError): self.assertIsNone(resident_memory())

    def test_real_sample(self):
        first=sample(); time.sleep(0.02); second=sample(); result=measure(first,second,resident_memory())
        self.assertGreaterEqual(result.cpu_percent,0)
        if sys.platform.startswith('linux'): self.assertGreater(result.resident_bytes,0)

    @unittest.skipUnless(sys.platform=='win32','Windows native working set')
    def test_windows_memory_native(self):
        self.assertGreater(windows_memory(),0)

    def test_migration(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'; s=Settings(path); self.assertFalse(s.health_enabled)
            s.set_module('Metadata',True)
            raw=json.loads(path.read_text()); raw['schema']=23; raw.pop('health_enabled'); path.write_text(json.dumps(raw))
            s=Settings(path); self.assertFalse(s.warning); self.assertTrue(s.metadata_enabled); self.assertFalse(s.health_enabled)
            s.set_module('Health',True); s.set_appearance(Appearance(favorites=('Health',)))
            self.assertEqual(json.loads(path.read_text())['schema'],49); self.assertTrue(Settings(path).health_enabled)
