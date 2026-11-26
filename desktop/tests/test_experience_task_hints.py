import unittest

from aeris.experience import task_hint, TASK_HINTS, NAMES
from aeris.experience_help import HELP


class TaskHintTests(unittest.TestCase):
    def test_all_rules_have_help_and_names(self):
        for name, phrases in TASK_HINTS:
            with self.subTest(name=name):
                self.assertIn(name, NAMES)
                self.assertIn(name, HELP)
                for phrase in phrases:
                    self.assertEqual(task_hint(phrase), name)

    def test_accents_and_case(self):
        self.assertEqual(task_hint('Preciso de uma ATA DE REUNIÃO.'), 'Meeting')
        self.assertEqual(task_hint('Quero corrigir um texto.'), 'Text')

    def test_ambiguous_request(self):
        self.assertIsNone(task_hint('Quero traduzir e criar dashboard'))

    def test_unrelated_and_partial_words(self):
        self.assertIsNone(task_hint('Olá, tudo bem?'))
        self.assertIsNone(task_hint('retraduzir'))

    def test_invalid_input(self):
        self.assertIsNone(task_hint(None))
        self.assertIsNone(task_hint('x' * 4001))
        self.assertIsNone(task_hint(''))


if __name__ == '__main__':
    unittest.main()
