import unittest
from collections import Counter
from aeris.registry import load_catalog, filter_catalog

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.modules = load_catalog()

    def test_catalog_integrity(self):
        self.assertEqual([m.id for m in self.modules], list(range(1,51)))
        self.assertEqual(len({m.name for m in self.modules}), 50)
        self.assertEqual(sorted(Counter(m.category for m in self.modules).values()), [5]*10)

    def test_only_hub_is_prototype(self):
        self.assertEqual([m.name for m in self.modules if m.status == 'prototype'], ['Hub'])
        self.assertEqual(sum(m.status == 'planned' for m in self.modules), 49)

    def test_case_insensitive(self):
        self.assertIn('Snippets', [m.name for m in filter_catalog(self.modules, 'SNIPPETS')])

    def test_accent_insensitive(self):
        self.assertEqual(filter_catalog(self.modules, 'informacoes'), filter_catalog(self.modules, 'informações'))
        self.assertTrue(filter_catalog(self.modules, 'informações'))

    def test_category(self):
        self.assertEqual(len(filter_catalog(self.modules, category='Core')), 5)

    def test_combined_filter(self):
        self.assertEqual([m.name for m in filter_catalog(self.modules, 'hub', 'Core')], ['Hub'])

    def test_no_results(self):
        self.assertEqual(filter_catalog(self.modules, 'xxxxxxxxxx'), ())
