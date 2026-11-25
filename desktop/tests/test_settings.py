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

    def test_snippets_preferences_and_migration(self):
        import json
        from dataclasses import asdict
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            appearance = Appearance(icon_size=44)
            path.write_text(json.dumps({'schema': 2, 'capture_enabled': True, 'appearance': asdict(appearance)}))
            settings = Settings(path)
            self.assertTrue(settings.capture_enabled)
            self.assertFalse(settings.snippets_enabled)
            settings.set_snippets(True)
            settings.set_capture(False)
            settings.set_appearance(appearance)
            loaded = Settings(path)
            self.assertTrue(loaded.snippets_enabled)
            self.assertFalse(loaded.capture_enabled)
            self.assertEqual(loaded.appearance, appearance)

    def test_invalid_snippets_defaults_to_disabled(self):
        import json
        from dataclasses import asdict
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            path.write_text(json.dumps({'schema': 3, 'capture_enabled': True, 'snippets_enabled': 1, 'appearance': asdict(Appearance())}))
            settings = Settings(path)
            self.assertFalse(settings.snippets_enabled)
            self.assertFalse(settings.capture_enabled)
            self.assertTrue(settings.warning)
