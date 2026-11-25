import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.settings import Settings, Appearance

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

    def test_migrate_and_keep_preferences(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            path.write_text('{"schema":1,"capture_enabled":true}')
            settings = Settings(path)
            self.assertTrue(settings.capture_enabled)
            self.assertEqual(settings.appearance, Appearance())
            prefs = Appearance(icon_size=48, opacity=82, quick_enabled=False)
            settings.set_appearance(prefs)
            settings.set_capture(False)
            self.assertEqual(Settings(path).appearance, prefs)

    def test_invalid_appearance(self):
        for args in ({'icon_size': 65}, {'opacity': 79}, {'panel_size': 'XL'}, {'quick_enabled': 1}):
            with self.assertRaises(ValueError):
                Appearance(**args)
