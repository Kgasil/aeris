import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict
from aeris.voice import speech_payload, parse_voices, serialize, start_process
from aeris.permissions import Permissions, PLAY_VOICE
from aeris.settings import Settings, Appearance, FLAGS

class VoiceTests(unittest.TestCase):
    def test_payload_plain_text(self):
        text = "Olá! $env:PATH; ' <speak> & \""
        p=speech_payload(text, 'Voz', -5, 100)
        self.assertEqual(json.loads(serialize(p))['text'],text)
        self.assertTrue(serialize(p).isascii())
    def test_invalid(self):
        for args in [('',),('x'*4001,),('a\0b',),('a','',6,80),('a','',True,80),('a','',0,101),('a','x'*257)]:
            with self.subTest(args=args), self.assertRaises(ValueError): speech_payload(*args)
    def test_voices(self):
        self.assertEqual(parse_voices('["A","B","A"]'),('A','B'))
        for value in ['{}','[1]','[""]']:
            with self.assertRaises(ValueError): parse_voices(value)
    def test_permission(self):
        p=Permissions(); self.assertFalse(p.allowed(PLAY_VOICE)); p.set(PLAY_VOICE,True); p.require(PLAY_VOICE); p.revoke_all(); self.assertFalse(p.allowed(PLAY_VOICE))
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; data={k:k=='translate_enabled' for k in FLAGS if k!='voice_enabled'}; data.update(schema=11,appearance=asdict(Appearance(favorites=('Translate',))))
            p.write_text(json.dumps(data)); s=Settings(p); self.assertTrue(s.translate_enabled); self.assertFalse(s.voice_enabled); self.assertFalse(s.warning)
            s.set_module('Voice',True); self.assertTrue(Settings(p).voice_enabled); self.assertTrue(Settings(p).translate_enabled)
    @unittest.skipUnless(os.name=='nt','Requer Windows e System.Speech')
    def test_native_voice_enumeration(self):
        p=start_process()
        try: out,_=p.communicate(serialize({'action':'list'}),timeout=20)
        finally:
            if p.poll() is None: p.kill(); p.communicate()
        self.assertEqual(p.returncode,0); self.assertIsInstance(parse_voices(out),tuple)
