import json
import tempfile
import unittest
from pathlib import Path
from aeris.meeting_intelligence import prepare_minutes
from aeris.meeting_audio import model_path


class MeetingIntelligenceTests(unittest.TestCase):
    def test_isolated_draft(self):
        def fake(model, history, text, *, system):
            self.assertEqual(history, ())
            self.assertEqual(text, 'Revisar relatório.')
            return json.dumps({'resumo':'Revisão discutida','decisoes':[],'acoes':['Revisar relatório']})
        draft=prepare_minutes('local','Revisar relatório.',chat_fn=fake)
        self.assertEqual(draft.actions[0].title,'Revisar relatório')
        self.assertEqual(draft.actions[0].owner,'')
        self.assertEqual(draft.actions[0].due,'')
        self.assertIn('Revisão discutida',draft.notes)

    def test_invalid_output(self):
        for raw in ('not json','{"resumo":"x","decisoes":[],"acoes":[],"extra":true}',
                    '{"resumo":"x","decisoes":[],"acoes":[1]}',
                    '{"resumo":"x","decisoes":[],"acoes":[""]}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                prepare_minutes('local','texto',chat_fn=lambda *a,**k:raw)

    def test_input_limit(self):
        def forbidden(*a,**k):
            self.fail('Model should not be called')
        with self.assertRaises(ValueError):
            prepare_minutes('local','x'*4001,chat_fn=forbidden)

    def test_local_model_directory(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(ValueError):
                model_path(p)
            for name in ('model.bin','config.json','tokenizer.json'):
                (p/name).touch()
            self.assertEqual(model_path(p),p.resolve())


if __name__=='__main__':
    unittest.main()
