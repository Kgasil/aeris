import unittest
from aeris.capture import CaptureStore

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.store = CaptureStore()

    def test_create_edit_delete(self):
        note = self.store.save('Exemplo', 'Texto fictício')
        edited = self.store.save('Novo', 'Conteúdo', note.id)
        self.assertEqual(self.store.list(), (edited,))
        self.store.delete(note.id)
        self.assertEqual(self.store.list(), ())

    def test_empty(self):
        with self.assertRaises(ValueError):
            self.store.save(' ', 'abc')

    def test_limits(self):
        with self.assertRaises(ValueError):
            self.store.save('x'*121, 'abc')
        with self.assertRaises(ValueError):
            self.store.save('abc', 'x'*100001)

    def test_session_isolation(self):
        self.store.save('A', 'B')
        self.assertEqual(CaptureStore().list(), ())
        self.store.clear()
        self.assertEqual(self.store.list(), ())
