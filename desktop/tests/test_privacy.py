import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from aeris.privacy import mask_text, inventory, file_status
from aeris.permissions import Permissions, SEARCH_CAPTURE
from aeris.settings import Settings

class PrivacyTests(unittest.TestCase):
    def test_mask_multiple(self):
        original='Contato: pessoa@example.com / 000.000.000-00 / 00.000.000/0000-00 / (00) 00000-0000'
        result=mask_text(original)
        self.assertEqual(result.text,'Contato: [E-mail ocultado] / [CPF formatado ocultado] / [CNPJ formatado ocultado] / [Telefone BR formatado ocultado]')
        self.assertEqual(sum(n for _,n in result.counts),4)
        self.assertIn('pessoa@example.com',original)
    def test_no_match(self):
        text='Texto normal\n1234 e 00000000000'
        self.assertEqual(mask_text(text).text,text)
    def test_repeat_and_limits(self):
        self.assertEqual(dict(mask_text('x@y.example x@y.example').counts)['E-mail'],2)
        for value in (None,'x'*20001):
            with self.assertRaises(ValueError): mask_text(value)
    def test_file_presence(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'test'; self.assertEqual(file_status(p),'Não encontrado')
            p.write_bytes(b'fake'); self.assertIn('não verificado',file_status(p)); p.unlink(); p.mkdir()
            self.assertIn('não regular',file_status(p))
    def test_inventory_no_contents(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; settings=Settings(p)
            (p.parent/'vault.bin').write_text('FICTICIO')
            permissions=Permissions(); permissions.set(SEARCH_CAPTURE,True)
            hub=SimpleNamespace(settings=settings,permissions=permissions,alive=lambda obj:False,capture_store=SimpleNamespace(list=lambda:('CONTEUDO SECRETO',)))
            grants,files,stores,locks=inventory(hub)
            self.assertEqual(sum(v for _,v in grants),1); self.assertEqual(dict(stores)['capture'],1)
            self.assertIn('Presente',dict(files)['vault.bin']); self.assertNotIn('FICTICIO',repr((grants,files,stores,locks)))
            self.assertNotIn('CONTEUDO SECRETO',repr(stores)); self.assertEqual(dict(locks)['Vault'],'Fechado / bloqueado')
