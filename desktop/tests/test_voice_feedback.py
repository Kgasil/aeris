import unittest
from aeris.voice_feedback import parse_event


class FeedbackTests(unittest.TestCase):
    def test_real_level_and_states(self):
        self.assertEqual(parse_event('{"kind":"level","value":47}'),('level',47))
        self.assertEqual(parse_event('{"kind":"state","value":"Speech"}'),('state','Speech'))
        self.assertEqual(parse_event('{"kind":"partial","value":"Olá"}'),('partial','Olá'))
        self.assertEqual(parse_event('{"kind":"error","value":"recognizer"}'),('error','recognizer'))

    def test_invalid_events(self):
        for event in ('{"kind":"level","value":101}','{"kind":"level","value":true}',
                      '{"kind":"state","value":"invented"}','{"kind":"partial","value":""}',
                      '{"kind":"error","value":"remote"}','{"kind":"final","value":"x","extra":1}'):
            with self.subTest(event=event),self.assertRaises(ValueError): parse_event(event)
