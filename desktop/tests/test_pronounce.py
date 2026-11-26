import json
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.pronounce import LANGUAGES, EXERCISES, practice_payload
from aeris.permissions import Permissions, PLAY_VOICE, PLAY_PRONOUNCE
from aeris.settings import Settings, FLAGS, Appearance

class PronounceTests(unittest.TestCase):
    def test_exercises(self):
        self.assertEqual(set(LANGUAGES.values()),set(EXERCISES))
        for code, phrases in EXERCISES.items():
            self.assertEqual(len(phrases),4)
            for phrase in phrases:
                self.assertEqual(practice_payload(phrase,code,'Test voice')['text'],phrase)

    def test_payload(self):
        p=practice_payload('¡Hola!','es','Test voice',-3,70,5)
        self.assertEqual(p,{'action':'speak','text':'¡Hola!','voice':'Test voice','rate':-3,'volume':70,'language':'es','repeat':5})

    def test_invalid(self):
        for params in ({'text':'x'*501},{'text':' '},{'language':'fr'},{'voice':''},{'repeat':0},{'repeat':6},{'repeat':True},{'rate':-6},{'volume':101}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                practice_payload(**({'text':'Hi','language':'en','voice':'Test voice'}|params))

    def test_permissions_independent(self):
        p=Permissions(); p.set(PLAY_VOICE,True)
        self.assertFalse(p.allowed(PLAY_PRONOUNCE)); p.set(PLAY_PRONOUNCE,True)
        p.set(PLAY_VOICE,False); self.assertTrue(p.allowed(PLAY_PRONOUNCE))
        p.revoke_all(); self.assertFalse(p.allowed(PLAY_PRONOUNCE))

    def test_migration(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'settings.json'
            data={k:k=='voice_enabled' for k in FLAGS if k!='pronounce_enabled'}
            path.write_text(json.dumps(dict(data,schema=14,appearance=asdict(Appearance(favorites=('Voice',))))))
            s=Settings(path); self.assertFalse(s.warning); self.assertTrue(s.voice_enabled); self.assertFalse(s.pronounce_enabled)
            s.set_module('Pronounce',True)
            self.assertTrue(Settings(path).pronounce_enabled); self.assertTrue(Settings(path).voice_enabled)
            self.assertEqual(json.loads(path.read_text())['schema'],49)
