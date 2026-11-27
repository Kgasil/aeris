import unittest
from aeris.ai_setup import setup_stage

class SetupProgressTests(unittest.TestCase):
    def test_download_steps_are_completed_counts_not_percentages(self):
        messages=['Instalando Ollama pela fonte oficial do WinGet…','Iniciando IA local (sem nuvem)…','Baixando modelo local.','Testando a IA com uma mensagem fictícia…']
        for i,message in enumerate(messages):
            count,label=setup_stage(message,download=True)
            self.assertEqual(count,i)
            self.assertIn(f'Etapa {i+1} de 4',label)
    def test_restore_has_no_download_or_inference_claim(self):
        self.assertEqual(setup_stage('Iniciando IA local (sem nuvem)…',download=False)[0],0)
        self.assertEqual(setup_stage('Verificando modelo local existente…',download=False)[0],1)
    def test_unknown_status_is_bounded_and_conservative(self):
        count,label=setup_stage('x'*500,download=True)
        self.assertEqual(count,0)
        self.assertEqual(len(label),180)
