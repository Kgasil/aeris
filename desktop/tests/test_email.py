import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict
import json
from aeris.email_draft import compose, LANGUAGES, TONES, PURPOSES
from aeris.settings import Settings, FLAGS, Appearance
from aeris.permissions import Permissions, COPY_EMAIL

class EmailTests(unittest.TestCase):
    def test_all_templates(self):
        for language in LANGUAGES:
            for tone in TONES:
                for purpose in PURPOSES:
                    with self.subTest(language=language,tone=tone,purpose=purpose):
                        draft=compose(language,tone,purpose,'Alex','','Detalhes fictícios.','Equipe')
                        self.assertTrue(draft.subject)
                        self.assertIn('Alex',draft.body)
                        self.assertIn('Detalhes fictícios.',draft.body)
                        self.assertTrue(draft.body.endswith('Equipe'))
    def test_custom_subject_and_tone(self):
        args=('English','Formal','Solicitação','Alex','Custom subject','Please review.','Team')
        a=compose(*args); b=compose(args[0],'Direto',*args[2:])
        self.assertEqual(a.subject,'Custom subject'); self.assertNotEqual(a.body,b.body)
        self.assertIn('Dear Alex,',a.body)
    def test_optional_fields(self):
        a=compose('Español','Formal','Atualização','','','Texto ficticio.','')
        self.assertEqual(a.subject,'Actualización'); self.assertTrue(a.body.startswith('Estimados/as:'))
    def test_invalid_fields(self):
        args=['Português','Formal','Solicitação','Alex','Assunto','Detalhes','Equipe']
        for idx,value in [(0,'fr'),(1,'x'),(2,'x'),(3,'A\nB'),(4,'x'*201),(5,' '),(5,'x'*8001),(5,'x\0'),(6,'x'*1001)]:
            modified=args.copy(); modified[idx]=value
            with self.subTest(index=idx),self.assertRaises(ValueError): compose(*modified)
    def test_schema13_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; data={k:k=='text_enabled' for k in FLAGS if k!='email_enabled'}
            data.update(schema=13,appearance=asdict(Appearance(favorites=('Text',))))
            p.write_text(json.dumps(data)); s=Settings(p)
            self.assertTrue(s.text_enabled); self.assertFalse(s.email_enabled); self.assertFalse(s.warning)
            s.set_module('Email',True); self.assertTrue(Settings(p).email_enabled); self.assertTrue(Settings(p).text_enabled)
            self.assertEqual(json.loads(p.read_text())['schema'],49)
    def test_permission(self):
        p=Permissions(); self.assertFalse(p.allowed(COPY_EMAIL))
        p.set(COPY_EMAIL,True); p.require(COPY_EMAIL); p.revoke_all()
        with self.assertRaises(PermissionError): p.require(COPY_EMAIL)
