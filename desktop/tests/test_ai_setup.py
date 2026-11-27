import tempfile
import io
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from aeris.ai_setup import (MODELS, ManagedRuntime, load_choice, save_choice, runtime_env,
                            local_port, select_managed, reset_endpoint, check_cancel, pull_model)


class SetupTests(unittest.TestCase):
    def tearDown(self):
        reset_endpoint()

    def test_pull_uses_real_layer_bytes_and_requires_success(self):
        factory=Mock(); response=factory.return_value.getresponse.return_value; response.status=200
        rows=[{'status':'pulling','digest':'sha256:'+'a'*64,'total':100,'completed':100},{'status':'success'}]
        response.readline.side_effect=io.BytesIO(b''.join(json.dumps(row).encode()+b'\n' for row in rows)).readline
        updates=[]
        pull_model('qwen2.5:1.5b',threading.Event(),updates.append,connection_factory=factory)
        self.assertEqual(updates[0][2:],(100,100))
        self.assertEqual(updates[-1][2:],(None,None))
        factory.assert_called_once_with('127.0.0.1',11435,timeout=30)
        self.assertFalse(json.loads(factory.return_value.request.call_args.args[2])['insecure'])
        factory.return_value.close.assert_called_once()

    def test_pull_rejects_incomplete_and_unknown_model(self):
        factory=Mock(); response=factory.return_value.getresponse.return_value; response.status=200
        response.readline.return_value=b''
        with self.assertRaises(OSError): pull_model('qwen2.5:1.5b',threading.Event(),lambda _:None,connection_factory=factory)
        with self.assertRaises(ValueError): pull_model('remote',threading.Event(),lambda _:None,connection_factory=factory)

    def test_choice_roundtrip_and_reject_arbitrary_models(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'choice.json'
            self.assertIsNone(load_choice(p))
            for model in MODELS:
                save_choice(p,model)
                self.assertEqual(load_choice(p),model)
            with self.assertRaises(ValueError):
                save_choice(p,'anything-cloud')
            p.write_text('{"model":"anything-cloud"}')
            self.assertIsNone(load_choice(p))

    def test_isolated_environment_and_fixed_loopback(self):
        with patch.dict('os.environ',{'OLLAMA_HOST':'0.0.0.0:11434','OLLAMA_NO_CLOUD':'0','OLLAMA_MODELS':'elsewhere'}):
            env=runtime_env(Path('private-models'))
        self.assertEqual(env['OLLAMA_HOST'],'127.0.0.1:11435')
        self.assertEqual(env['OLLAMA_NO_CLOUD'],'1')
        self.assertEqual(env['OLLAMA_MODELS'],'private-models')
        self.assertEqual(local_port(),11434)
        select_managed()
        self.assertEqual(local_port(),11435)

    def test_cancellation_and_non_windows_never_install(self):
        cancel=threading.Event()
        cancel.set()
        with self.assertRaises(InterruptedError): check_cancel(cancel)
        with tempfile.TemporaryDirectory() as d:
            r=ManagedRuntime(Path(d)/'settings.json')
            with patch('aeris.ai_setup.os.name','posix'),patch('aeris.ai_setup.subprocess.Popen') as run:
                with self.assertRaises(OSError): r.prepare('qwen2.5:1.5b',cancel,lambda _:None,download=True)
                run.assert_not_called()
            self.assertIsNone(r.process)
