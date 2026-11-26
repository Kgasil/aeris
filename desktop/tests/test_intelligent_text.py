import unittest
from aeris.intelligent_text import LANGUAGES, review, cursor_after

class IntelligentTextTests(unittest.TestCase):
    def test_pt_preserves_case_and_layout(self):
        r=review('Ola, VOCE!\n  tambem  nao.\n',LANGUAGES[0])
        self.assertEqual(r.text,'Olá, VOCÊ!\n  também  não.\n')
        self.assertEqual(len(r.edits),4)
        self.assertEqual(r.edits[0].before,'Ola')
    def test_english_spanish(self):
        self.assertEqual(review('Teh adress is seperate.',LANGUAGES[1]).text,'The address is separate.')
        self.assertEqual(review('Tambien la informacion.',LANGUAGES[2]).text,'También la información.')
    def test_grammar_preview_only(self):
        text='A gente fomos na reuniao.'
        self.assertEqual(review(text,LANGUAGES[0]).text,'A gente foi na reunião.')
        self.assertEqual(review(text,LANGUAGES[0],automatic=True).text,'A gente fomos na reunião.')
    def test_incomplete_token(self):
        self.assertEqual(review('voce',LANGUAGES[0],automatic=True).text,'voce')
        self.assertEqual(review('voce ',LANGUAGES[0],automatic=True).text,'você ')
        self.assertEqual(review('voce',LANGUAGES[0]).text,'você')
    def test_protected(self):
        s='https://example.org/voce voce@example.org `voce` ```\nvoce\n``` C:\\voce.txt /tmp/voce voce.txt minha_voce vOcE'
        self.assertEqual(review(s,LANGUAGES[0]).text,s)
    def test_boundaries_and_cursor(self):
        r=review('concerteza voce',LANGUAGES[0]); self.assertEqual(r.text,'com certeza você')
        self.assertEqual(cursor_after(10,r.edits),11)
        self.assertEqual(cursor_after(15,r.edits),16)
        self.assertEqual(review('minhavoces',LANGUAGES[0]).text,'minhavoces')
    def test_invalid_and_limit(self):
        for s,lang in [('x'*20001,LANGUAGES[0]),('x\0',LANGUAGES[0]),('abc','invalid'),('concerteza '*1818,LANGUAGES[0])]:
            with self.assertRaises(ValueError): review(s,lang)
    def test_idempotence(self):
        for lang,s in zip(LANGUAGES,['Ola voce, a gente fomos.','Teh adress.','Tambien la informacion.']):
            r=review(s,lang); self.assertEqual(review(r.text,lang).edits,())
