import unittest
from aeris.snippets import SnippetStore

class SnippetTests(unittest.TestCase):
    def setUp(self):
        self.store = SnippetStore()

    def test_crud_and_exact_body(self):
        note = self.store.save(' Assinatura ', ' Trabalho ', '  linha 1\nlinha 2  ')
        self.assertEqual(note.title, 'Assinatura')
        self.assertEqual(note.body, '  linha 1\nlinha 2  ')
        updated = self.store.save('SQL', 'Código', 'SELECT 1;', note.id)
        self.assertEqual(self.store.get(note.id), updated)
        self.store.delete(note.id)
        self.assertEqual(self.store.list(), ())

    def test_search_and_category(self):
        first = self.store.save('Consulta', 'Código', 'SELECT 1')
        self.store.save('Mensagem', 'Geral', 'Olá')
        self.assertEqual(self.store.list('codigo SELECT'), (first,))
        self.assertEqual(self.store.list(category='Código'), (first,))
        self.assertEqual(self.store.list('inexistente'), ())

    def test_invalid_and_session_limits(self):
        for args in [('', 'Geral', 'abc'), ('A', '', 'abc'), ('A', 'Geral', ' '), ('x'*121, 'Geral', 'abc'), ('A', 'x'*61, 'abc'), ('A', 'Geral', 'x'*20001)]:
            with self.assertRaises(ValueError):
                self.store.save(*args)
        for i in range(100):
            self.store.save(str(i), 'Geral', 'abc')
        with self.assertRaises(ValueError):
            self.store.save('101', 'Geral', 'abc')

    def test_isolation_and_clear(self):
        item = self.store.save('A', 'Geral', 'B')
        self.assertEqual(SnippetStore().list(), ())
        self.store.clear()
        with self.assertRaises(KeyError):
            self.store.get(item.id)
