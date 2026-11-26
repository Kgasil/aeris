import unittest
from aeris.theme import background_role, PALETTES

class ThemeRoleTests(unittest.TestCase):
    def test_legacy(self):
        for color,role in (('#F6FAF7','air'),('#DCEFE3','soft'),('#CFDFD5','muted'),('#FFFFFF','field')):
            self.assertEqual(background_role(color),role)

    def test_current(self):
        for role in ('air','soft','muted','field'):
            self.assertEqual(background_role(PALETTES['Claro'][role]),role)

    def test_case_and_fallback(self):
        self.assertEqual(background_role('#f6FaF7'),'air')
        self.assertEqual(background_role('#123456'),'air')

if __name__=='__main__':
    unittest.main()
