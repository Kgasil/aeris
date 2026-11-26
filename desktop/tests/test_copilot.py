import unittest
from datetime import datetime
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from unittest.mock import patch
from aeris.copilot import parse_command, CopilotSession, EXAMPLES
from aeris.permissions import Permissions, COPILOT_RUN
from aeris.reminder import ReminderStore
from aeris.checklist import ChecklistStore
from aeris.focus import FocusTimer
from aeris.settings import Settings, Appearance

class CopilotTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,25,10,0).timestamp()
        self.enabled={'Copilot','Reminder','Ideas','Checklist','Focus'}
        self.h=SimpleNamespace(permissions=Permissions(),enabled=lambda name:name in self.enabled,reminder_store=ReminderStore(lambda:self.now),checklist_store=ChecklistStore(),ideas_store=None,focus_timer=FocusTimer(),alive=lambda x:False,reminder_window=None,checklist_window=None,ideas_window=None,privacy_window=None,schedule_reminders=lambda:None)
        self.h.checklist_store.create('Estudos'); self.h.permissions.set(COPILOT_RUN,True)
        self.s=CopilotSession(self.h)
        self.clock=patch('aeris.copilot.time',lambda:self.now);self.clock.start();self.addCleanup(self.clock.stop)
    def test_examples(self):
        self.assertEqual([parse_command(t,self.now).tool for t in EXAMPLES],['Reminder','Reminder','Checklist','Focus','Ideas','Reminder','Reminder','Focus'])
        self.assertEqual(parse_command(EXAMPLES[1],self.now).args[1],datetime(2026,11,26,14,0).timestamp())
        self.assertEqual(parse_command(EXAMPLES[2],self.now).args,('Estudos','estudar Python'))
    def test_reject_invalid(self):
        for t in ['execute powershell','marque reunião hoje às 09:00','marque reunião amanhã às 25:00','inicie uma concentração de 121 minutos','lembre-me de teste em 0 minutos','anote minha ideia de '+ 'a'*161,'\x00','anote minha ideia de a\u202eb']:
            with self.subTest(t=t),self.assertRaises(ValueError): parse_command(t,self.now)
    def test_preview_single_use(self):
        p=self.s.prepare(EXAMPLES[0]);self.assertFalse(self.h.reminder_store.list());self.now+=10;self.s.confirm()
        self.assertEqual(self.h.reminder_store.list()[0].due,p.args[1]);self.assertTrue(self.h.reminder_store.list()[0].alert)
        with self.assertRaises(ValueError): self.s.confirm()
        self.assertEqual(len(self.h.reminder_store.list()),1)
    def test_permission_and_disable(self):
        self.s.prepare(EXAMPLES[4]);self.h.permissions.set(COPILOT_RUN,False)
        with self.assertRaises(PermissionError):self.s.confirm()
        self.assertIsNone(self.h.ideas_store);self.h.permissions.set(COPILOT_RUN,True)
        self.s.prepare(EXAMPLES[4]);self.enabled.remove('Ideas')
        with self.assertRaises(ValueError):self.s.confirm()
        self.assertIsNone(self.h.ideas_store)
    def test_expired_and_cancelled(self):
        self.s.prepare('Lembre-me de teste em 1 minuto');self.now+=60
        with self.assertRaises(ValueError):self.s.confirm()
        self.s.prepare(EXAMPLES[4]);self.s.cancel()
        with self.assertRaises(ValueError):self.s.confirm()
        self.assertFalse(self.h.reminder_store.list());self.assertIsNone(self.h.ideas_store)
    def test_real_records_and_missing_list(self):
        self.s.prepare(EXAMPLES[2]);self.s.confirm();self.assertEqual(self.h.checklist_store.tasks('Estudos')[0].title,'estudar Python')
        self.s.prepare(EXAMPLES[4]);self.s.confirm();self.assertEqual(self.h.ideas_store.list()[0].title,'automatizar relatórios')
        self.s.prepare(EXAMPLES[2]);self.h.checklist_store.delete_list('Estudos')
        with self.assertRaises(ValueError):self.s.confirm()
        self.assertFalse(self.h.checklist_store.names())
    def test_focus_conflict_and_invalidated_preview(self):
        self.s.prepare(EXAMPLES[3]);self.h.focus_timer.start()
        with self.assertRaises(ValueError):self.s.confirm()
        self.assertEqual(self.h.focus_timer.state,'running');self.s.prepare(EXAMPLES[4])
        with self.assertRaises(ValueError):self.s.prepare('não reconhecido')
        with self.assertRaises(ValueError):self.s.confirm()
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Decision',True)
            data=json.loads(p.read_text());data['schema']=44;data.pop('copilot_enabled');p.write_text(json.dumps(data));s=Settings(p)
            self.assertTrue(s.decision_enabled);self.assertFalse(s.copilot_enabled);self.assertFalse(s.warning)
            s.set_module('Copilot',True);s.set_appearance(Appearance(favorites=('Copilot',)));s=Settings(p)
            self.assertTrue(s.copilot_enabled);self.assertEqual(s.appearance.favorites,('Copilot',))
