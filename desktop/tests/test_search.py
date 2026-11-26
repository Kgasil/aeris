import unittest
from types import SimpleNamespace as Item
from aeris.search import search

class SearchTests(unittest.TestCase):
    def setUp(self):
        self.modules = [Item(id=1,name='Hub',category='Core',description='gestão de ferramentas')]
        self.notes = [Item(id=1,title='Reunião',body='SQL e Python')]
        self.snippets = [Item(id=1,title='SQL',category='Código',body='SELECT 1')]

    def run_search(self, q, sources):
        return search(q, sources, self.modules, self.notes, self.snippets)

    def test_default_scope(self):
        self.assertEqual(self.run_search('sql', {'Ferramentas'}), ())
        self.assertEqual(self.run_search('gestao', {'Ferramentas'})[0].title, 'Hub')

    def test_explicit_scope_and_rank(self):
        matches = self.run_search('SQL', {'Capture','Snippets'})
        self.assertEqual([m.source for m in matches], ['Snippets','Capture'])
        self.assertEqual(self.run_search('reuniao python', {'Capture'})[0].id, 1)
        self.assertEqual(self.run_search('codigo select', {'Snippets'})[0].title, 'SQL')

    def test_empty_and_no_matches(self):
        self.assertEqual(self.run_search('   ', {'Capture'}), ())
        self.assertEqual(self.run_search('xyz', {'Capture'}), ())

    def test_no_persistence_or_stale_index(self):
        self.assertTrue(self.run_search('sql', {'Capture'}))
        self.notes.clear()
        self.assertFalse(self.run_search('sql', {'Capture'}))
