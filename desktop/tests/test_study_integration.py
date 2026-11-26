import unittest
from types import SimpleNamespace
from aeris.integration import prepare_study, execute_study
from aeris.learn import LearnStore
from aeris.research import ResearchStore
from aeris.flashcards import FlashcardsStore
from aeris.permissions import Permissions, INTEGRATION_RUN
from aeris.copilot import parse_command
from datetime import datetime

class StudyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.enabled={'Learn','Research','Flashcards'}
        self.h=SimpleNamespace(permissions=Permissions(),enabled=self.enabled.__contains__,learn_store=LearnStore(),research_store=ResearchStore(),flashcards_store=FlashcardsStore())
        self.h.permissions.set(INTEGRATION_RUN,True)
        p=self.h.learn_store.create('Python');self.t=self.h.learn_store.add(p.id,'O que é uma API?',30);self.p=self.h.learn_store.get(p.id)
        self.r=self.h.research_store.add('Estruturas de dados','Projeto','Livro',notes='Privado')
    def test_card_and_duplicate(self):
        x=prepare_study(self.h,'Learn-Flashcards',self.p,'Interface',self.t)
        self.assertFalse(self.h.flashcards_store.list())
        c=execute_study(self.h,x,'Interface');self.assertEqual((c.deck,c.question,c.answer),('Python',self.t.title,'Interface'))
        with self.assertRaises(ValueError):execute_study(self.h,x,'Interface')
    def test_reference(self):
        v=(self.p.id,45);x=prepare_study(self.h,'Research-Learn',self.r,v)
        t=execute_study(self.h,x,v);self.assertEqual((t.title,t.minutes),(self.r.title,45));self.assertNotIn('Privado',x.preview)
        with self.assertRaises(ValueError):execute_study(self.h,x,v)
    def test_revocation_and_invalid_answer(self):
        with self.assertRaises(ValueError):prepare_study(self.h,'Learn-Flashcards',self.p,'',self.t)
        x=prepare_study(self.h,'Learn-Flashcards',self.p,'Interface',self.t);self.h.permissions.set(INTEGRATION_RUN,False)
        with self.assertRaises(PermissionError):execute_study(self.h,x,'Interface')
        self.assertFalse(self.h.flashcards_store.list())
    def test_changed_source(self):
        x=prepare_study(self.h,'Learn-Flashcards',self.p,'Interface',self.t);self.h.learn_store.edit(self.p.id,self.t.id,'Alterado',30)
        with self.assertRaises(ValueError):execute_study(self.h,x,'Interface')
    def test_changed_target_and_values(self):
        v=(self.p.id,45);x=prepare_study(self.h,'Research-Learn',self.r,v)
        with self.assertRaises(ValueError):execute_study(self.h,x,(self.p.id,60))
        self.h.learn_store.rename(self.p.id,'Outro')
        with self.assertRaises(ValueError):execute_study(self.h,x,v)
    def test_natural_aliases(self):
        now=datetime(2026,11,25,10).timestamp()
        self.assertEqual(parse_command('Aeris, marque reunião amanhã às 14h30',now).args[1],datetime(2026,11,26,14,30).timestamp())
        self.assertEqual(parse_command('Aeris, me lembre de estudar em 20 minutos',now).tool,'Reminder')
        self.assertEqual(parse_command('Aeris comece uma concentração de 25 minutos',now).tool,'Focus')
        with self.assertRaises(ValueError):parse_command('Aeris, execute powershell',now)
