import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.settings import Settings

class SettingsTests(unittest.TestCase):
    def test_default_and_roundtrip(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            settings = Settings(path)
            self.assertFalse(settings.capture_enabled)
            self.assertFalse(path.exists())
            settings.set_capture(True)
            self.assertTrue(Settings(path).capture_enabled)
            settings.set_capture(False)
            self.assertFalse(Settings(path).capture_enabled)

    def test_invalid_defaults_to_disabled(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            path.write_text('{"schema":1,"capture_enabled":"yes"}')
            settings = Settings(path)
            self.assertFalse(settings.capture_enabled)
            self.assertTrue(settings.warning)
