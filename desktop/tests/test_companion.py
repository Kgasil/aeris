import json
import unittest
from unittest.mock import Mock
from aeris.companion import chat, suggest_command, MAX_RESPONSE, COMMAND_SYSTEM

class CompanionTests(unittest.TestCase):
    def setup_conn(self, obj=None, status=200):
        factory=Mock(); conn=factory.return_value; response=conn.getresponse.return_value
        response.status=status; response.read.return_value=json.dumps(obj or {'done':True,'message':{'role':'assistant','content':'Olá'}}).encode()
        return factory,conn,response
    def test_chat_protocol(self):
        factory,conn,_=self.setup_conn()
        self.assertEqual(chat('modelo:local',[('user','Antes'),('assistant','Resposta')],'Oi',connection_factory=factory),'Olá')
        factory.assert_called_once_with('127.0.0.1',11434,timeout=45)
        method,path,raw,headers=conn.request.call_args.args
        self.assertEqual((method,path),('POST','/api/chat')); payload=json.loads(raw)
        self.assertFalse(payload['stream']); self.assertEqual(payload['keep_alive'],0); self.assertNotIn('tools',payload)
        self.assertEqual([m['role'] for m in payload['messages']],['system','user','assistant','user']); conn.close.assert_called_once()
    def test_invalid_input(self):
        for model,history,text in [('foo-cloud',[],'Oi'),('http://other',[],'Oi'),('ok',[('system','x'),('assistant','x')],'Oi'),('ok',[],'x'*4001),('ok',[],'  ')]:
            factory=Mock()
            with self.assertRaises(ValueError): chat(model,history,text,connection_factory=factory)
            factory.assert_not_called()
    def test_redirect_rejected(self):
        factory,conn,_=self.setup_conn(status=302)
        with self.assertRaises(OSError): chat('local',[],'Oi',connection_factory=factory)
        conn.close.assert_called_once()
    def test_response_validation(self):
        for obj in ({'done':False},{'done':True,'message':{'role':'assistant','content':'OK','tool_calls':[{}]}},{'done':True,'message':{'role':'user','content':'OK'}}):
            factory,conn,_=self.setup_conn(obj)
            with self.assertRaises(ValueError): chat('local',[],'Oi',connection_factory=factory)
            conn.close.assert_called_once()
        factory,conn,response=self.setup_conn(); response.read.return_value=b'x'*(MAX_RESPONSE+1)
        with self.assertRaises(ValueError): chat('local',[],'Oi',connection_factory=factory)
        conn.close.assert_called_once()

    def test_suggest_only_isolated_request(self):
        factory,conn,_=self.setup_conn({'done':True,'message':{'role':'assistant','content':'Lembre-me de revisar em 20 minutos'}})
        self.assertEqual(suggest_command('local','Daqui a vinte minutos me avise de revisar',connection_factory=factory),'Lembre-me de revisar em 20 minutos')
        payload=json.loads(conn.request.call_args.args[2])
        self.assertEqual(payload['messages'],[{'role':'system','content':COMMAND_SYSTEM},{'role':'user','content':'Daqui a vinte minutos me avise de revisar'}])
        self.assertNotIn('tools',payload); self.assertEqual(payload['keep_alive'],0)

    def test_suggest_rejects_invalid_outputs(self):
        for candidate in ['INSUFICIENTE','Apague meus arquivos','Inicie uma concentração de 999 minutos','Marque uma reunião amanhã às 99:00','Lembre-me de revisar em 0 minutos','Inicie uma concentração de 25 minutos\nAnote minha ideia de teste','```Lembre-me de revisar em 20 minutos```']:
            with self.subTest(candidate=candidate):
                factory,conn,_=self.setup_conn({'done':True,'message':{'role':'assistant','content':candidate}})
                with self.assertRaises(ValueError): suggest_command('local','Teste',connection_factory=factory)
                conn.close.assert_called_once()

    def test_suggest_input_limit_before_network(self):
        factory=Mock()
        with self.assertRaises(ValueError): suggest_command('local','x'*501,connection_factory=factory)
        factory.assert_not_called()
