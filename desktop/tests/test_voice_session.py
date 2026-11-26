import unittest
from aeris.voice_session import VoiceSession, MAX_TURNS


class VoiceSessionTests(unittest.TestCase):
    def test_initial_and_stop(self):
        s=VoiceSession()
        self.assertFalse(s.active)
        s.begin('local')
        self.assertTrue(s.active)
        self.assertEqual(s.phase,'listen')
        s.stop()
        self.assertFalse(s.active)
        self.assertIsNone(s.model)
        self.assertIsNone(s.phase)

    def test_order(self):
        s=VoiceSession()
        s.begin('local')
        self.assertEqual(s.advance('listen'),'chat')
        self.assertEqual(s.advance('chat'),'speak')
        self.assertEqual(s.advance('speak'),'listen')
        self.assertEqual(s.turns,1)

    def test_invalid_transition(self):
        s=VoiceSession()
        s.begin('local')
        with self.assertRaises(ValueError):
            s.advance('speak')
        self.assertEqual(s.phase,'listen')
        s.stop()
        with self.assertRaises(ValueError):
            s.advance('listen')

    def test_bounded_session(self):
        s=VoiceSession()
        s.begin('local')
        for _ in range(MAX_TURNS):
            s.advance('listen')
            s.advance('chat')
            result=s.advance('speak')
        self.assertIsNone(result)
        self.assertFalse(s.active)

    def test_invalid_start_and_restart(self):
        s=VoiceSession()
        with self.assertRaises(ValueError):
            s.begin('')
        s.begin('one')
        with self.assertRaises(ValueError):
            s.begin('two')
        s.stop()
        s.begin('two')
        self.assertEqual(s.model,'two')
        self.assertEqual(s.turns,0)


if __name__=='__main__':
    unittest.main()
