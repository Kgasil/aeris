import json
import unittest
from aeris.intelligent_text import LANGUAGES, dictionary_words, review, cursor_after
from aeris.contextual_text import contextual_review, validate_source, AI_LIMIT

class ContextualTextTests(unittest.TestCase):
    def test_dictionary_case_and_phrase(self):
        words=dictionary_words('Voce,  gente, VOCE')
        self.assertEqual(words,{'voce','gente'})
        s='Voce tambem. A gente fomos.'
        self.assertEqual(review(s,LANGUAGES[0],ignored=words).text,'Voce também. A gente fomos.')
        self.assertEqual(review('VOCE ',LANGUAGES[0],automatic=True,ignored=words).text,'VOCE ')
    def test_dictionary_limits(self):
        for s in ['abc1','a b','x'*51,','.join(['a']*101),'x'*5001]:
            with self.assertRaises(ValueError): dictionary_words(s)
        self.assertEqual(dictionary_words(''),frozenset())
    def test_extended_rules(self):
        for lang,s,expected in zip(LANGUAGES,['Progeto e pesquiza.','Tommorow, accomodate.','Proyeto de investigacion.'],['Projeto e pesquisa.','Tomorrow, accommodate.','Proyecto de investigación.']):
            self.assertEqual(review(s,lang).text,expected)
    def test_request_only_source_no_history(self):
        def request(model,history,text,*,system):
            self.assertEqual(model,'local:1b'); self.assertEqual(history,())
            self.assertEqual(json.loads(text),{'idioma':LANGUAGES[0],'texto':' Ola! '})
            self.assertIn('não confiável',system)
            return json.dumps({'texto':' Olá! '})
        r=contextual_review(' Ola! ',LANGUAGES[0],'local:1b',request=request)
        self.assertEqual(r.text,' Olá! '); self.assertEqual(len(r.edits),1)
        self.assertEqual(cursor_after(6,r.edits),6)
    def test_protected_and_limits_no_send(self):
        def request(*a,**k): self.fail('Unexpected request')
        for s in ['', 'x'*(AI_LIMIT+1),'Veja https://example.org','Use `x`','email@exemplo.com','C:\\file.txt']:
            with self.assertRaises(ValueError): contextual_review(s,LANGUAGES[0],'x',request=request)
    def test_invalid_responses(self):
        for s in ['not json','[]','{"texto":"ok","command":"x"}','{"texto":null}','{"texto":""}',json.dumps({'texto':'a'*(AI_LIMIT*2+1)})]:
            with self.assertRaises(ValueError): contextual_review('Ola',LANGUAGES[0],'x',request=lambda *a,**k:s)
    def test_diff_reconstruction(self):
        s='Bom dia, ontem fui la.'; revised='Olá! Ontem fui lá, obrigado.'
        r=contextual_review(s,LANGUAGES[0],'x',request=lambda *a,**k:json.dumps({'texto':revised}))
        built=s
        for edit in reversed(r.edits): built=built[:edit.start]+edit.after+built[edit.end:]
        self.assertEqual(built,revised)
