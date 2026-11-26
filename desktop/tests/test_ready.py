import unittest
from aeris.ready import inspect_environment, model_selection, check_model


class ReadyTests(unittest.TestCase):
    def test_missing_optional(self):
        result=inspect_environment(platform='win32',frozen=False,find_spec=lambda name: object() if name=='numpy' else None)
        self.assertEqual(result.optional_missing,('soundcard','faster_whisper'))
        self.assertFalse(result.loopback_candidate)

    def test_discovery_without_import(self):
        result=inspect_environment(platform='win32',frozen=False,find_spec=lambda name:object())
        self.assertTrue(result.loopback_candidate)

    def test_other_platform_or_frozen(self):
        def forbidden(name):
            self.fail('Optional imports must not be checked')
        for platform,frozen in (('linux',False),('win32',True)):
            result=inspect_environment(platform=platform,frozen=frozen,find_spec=forbidden)
            self.assertFalse(result.loopback_candidate)

    def test_selection(self):
        self.assertEqual(model_selection('',('one',)),'one')
        self.assertEqual(model_selection('',('one','two')),'')
        self.assertEqual(model_selection('',()),'')
        self.assertEqual(model_selection('chosen',('one',)),'chosen')

    def test_synthetic_request(self):
        def fake(model,history,text):
            self.assertEqual(model,'local:latest')
            self.assertEqual(history,())
            self.assertEqual(text,'Responda com uma saudação curta em português.')
            return 'Olá!'
        self.assertTrue(check_model('local:latest',chat_fn=fake))

    def test_invalid_model_no_request(self):
        def forbidden(*args):
            self.fail('Invalid model must not be contacted')
        for name in ('','cloud-model','../file','http://remote',None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_model(name,chat_fn=forbidden)

    def test_invalid_response(self):
        for response in ('',None,'x'*4001):
            with self.subTest(response=response), self.assertRaises(ValueError):
                check_model('local',chat_fn=lambda *args:response)


if __name__=='__main__':
    unittest.main()
