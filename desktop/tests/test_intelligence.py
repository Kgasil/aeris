import unittest

from aeris.intelligence import recommend_tool, TOOLS


class IntelligenceTests(unittest.TestCase):
    def test_only_current_request(self):
        def fake(model, history, text, *, system):
            self.assertEqual(model, 'local')
            self.assertEqual(history, ())
            self.assertEqual(text, 'Preciso comparar versões')
            self.assertIn('Compare:', system)
            return 'Compare'
        self.assertEqual(recommend_tool('local','Preciso comparar versões',chat_fn=fake),'Compare')

    def test_allowlisted_identifiers(self):
        for name in TOOLS:
            with self.subTest(name=name):
                self.assertEqual(recommend_tool('local','pedido',chat_fn=lambda *a, **k: name),name)

    def test_no_recommendation(self):
        self.assertIsNone(recommend_tool('local','Olá',chat_fn=lambda *a, **k:'NONE'))

    def test_reject_unexpected_output(self):
        for value in ('shell','Compare; execute','{"tool":"Compare"}','compare','Capture\nText'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    recommend_tool('local','pedido',chat_fn=lambda *a, **k:value)

    def test_limits_before_model_call(self):
        def forbidden(*a, **k):
            self.fail('Model must not be called for invalid input')
        for text in ('', 'x'*1001, 'a\0b'):
            with self.assertRaises(ValueError):
                recommend_tool('local',text,chat_fn=forbidden)


if __name__=='__main__':
    unittest.main()
