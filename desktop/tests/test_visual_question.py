import unittest
from aeris.visual_question import VisualQuestion


class VisualQuestionTests(unittest.TestCase):
    def setUp(self):
        self.image = bytes(bytearray(b'example'))
        self.q = VisualQuestion(self.image, 'vision-local')
        self.options = dict(mic_allowed=True, screen_allowed=True, empty_editor=True)

    def test_reviewable_draft(self):
        self.assertEqual(self.q.draft('  O que aparece?  ', self.image, 'vision-local', **self.options), 'O que aparece?')

    def test_image_identity(self):
        other = bytes(bytearray(self.image))
        self.assertEqual(other, self.image)
        self.assertFalse(self.q.matches(other, 'vision-local'))
        with self.assertRaises(ValueError):
            self.q.draft('Pergunta', other, 'vision-local', **self.options)

    def test_model_changed(self):
        with self.assertRaises(ValueError):
            self.q.draft('Pergunta', self.image, 'other', **self.options)

    def test_revocation_and_existing_draft(self):
        for key in self.options:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.q.draft('Pergunta', self.image, 'vision-local', **dict(self.options, **{key:False}))

    def test_invalid_text(self):
        for text in ('', ' ', 'x'*4001, 'a\0b', None):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.q.draft(text, self.image, 'vision-local', **self.options)


if __name__=='__main__':
    unittest.main()
