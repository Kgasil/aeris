import unittest
from aeris.vision_session import VisionSession, MAX_SECONDS, MAX_FRAMES


class VisionSessionTests(unittest.TestCase):
    def setUp(self):
        self.now=100
        self.session=VisionSession(lambda:self.now)

    def test_disabled_by_default(self):
        self.assertFalse(self.session.active)
        self.assertFalse(self.session.allowed())
        with self.assertRaises(ValueError):
            self.session.record()

    def test_expiration(self):
        self.session.begin()
        self.now+=MAX_SECONDS-1
        self.assertTrue(self.session.allowed())
        self.now+=1
        self.assertFalse(self.session.allowed())
        with self.assertRaises(ValueError):
            self.session.record()

    def test_frame_limit(self):
        self.session.begin()
        for _ in range(MAX_FRAMES):
            self.session.record()
        self.assertFalse(self.session.allowed())
        with self.assertRaises(ValueError):
            self.session.record()

    def test_stop_and_restart(self):
        self.session.begin()
        self.session.record()
        with self.assertRaises(ValueError):
            self.session.begin()
        self.session.stop()
        self.assertFalse(self.session.allowed())
        self.session.begin()
        self.assertEqual(self.session.frames,0)
        self.assertTrue(self.session.allowed())


if __name__=='__main__':
    unittest.main()
