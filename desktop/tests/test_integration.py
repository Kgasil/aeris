import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta
from aeris.integration import prepare, execute
from aeris.meeting import MeetingStore, Action
from aeris.checklist import ChecklistStore
from aeris.reminder import ReminderStore
from aeris.permissions import Permissions, INTEGRATION_RUN

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,25,10).timestamp()
        self.enabled={'Meeting','Checklist','Reminder'}
        self.h=SimpleNamespace(permissions=Permissions(),enabled=self.enabled.__contains__,meeting_store=MeetingStore(),checklist_store=ChecklistStore(),reminder_store=ReminderStore(lambda:self.now))
        self.h.checklist_store.create('Projeto')
        self.h.permissions.set(INTEGRATION_RUN,True)
        self.m=self.h.meeting_store.add('Reunião','','','','',(Action('Revisar','Ana','2026-11-26'),Action('Finalizada',done=True),Action('Sem data')))
    def test_task_and_duplicate(self):
        p=prepare(self.h,self.m,0,'Checklist','Projeto')
        self.assertFalse(self.h.checklist_store.list())
        self.assertIn('não serão transferidos',p.preview)
        t=execute(self.h,p,'Projeto')
        self.assertEqual((t.title,t.priority,t.done),('Revisar','Normal',False))
        self.assertIs(self.h.meeting_store.get(self.m.id),self.m)
        with self.assertRaises(ValueError): execute(self.h,p,'Projeto')
    def test_reminder_time_and_duplicate(self):
        p=prepare(self.h,self.m,0,'Reminder','14:00')
        r=execute(self.h,p,'14:00')
        self.assertEqual(r.due,datetime(2026,11,26,14).timestamp())
        self.assertTrue(r.alert)
        with self.assertRaises(ValueError): execute(self.h,p,'14:00')
    def test_permission_rechecked(self):
        p=prepare(self.h,self.m,0,'Checklist','Projeto')
        self.h.permissions.set(INTEGRATION_RUN,False)
        with self.assertRaises(PermissionError): execute(self.h,p,'Projeto')
        self.assertFalse(self.h.checklist_store.list())
    def test_source_changed(self):
        p=prepare(self.h,self.m,0,'Checklist','Projeto')
        self.h.meeting_store.edit(self.m.id,'Alterada','','','','',self.m.actions)
        with self.assertRaises(ValueError): execute(self.h,p,'Projeto')
        self.assertFalse(self.h.checklist_store.list())
    def test_disabled_and_destination_changed(self):
        p=prepare(self.h,self.m,0,'Checklist','Projeto')
        self.enabled.remove('Checklist')
        with self.assertRaises(ValueError): execute(self.h,p,'Projeto')
        self.enabled.add('Checklist'); self.h.checklist_store=ChecklistStore(); self.h.checklist_store.create('Projeto')
        with self.assertRaises(ValueError): execute(self.h,p,'Projeto')
    def test_invalid_records_and_time(self):
        for i,target,value in [(1,'Checklist','Projeto'),(2,'Reminder','14:00'),(0,'Reminder','25:00'),(0,'Reminder','14h'),(0,'Checklist','Ausente'),(-1,'Checklist','Projeto')]:
            with self.subTest(i=i,target=target,value=value),self.assertRaises(ValueError): prepare(self.h,self.m,i,target,value)
        p=prepare(self.h,self.m,0,'Reminder','14:00'); self.now+=3*86400
        with self.assertRaises(ValueError): execute(self.h,p,'14:00')
    def test_changed_arguments_and_capacity(self):
        self.h.checklist_store.create('Outra')
        p=prepare(self.h,self.m,0,'Checklist','Projeto')
        with self.assertRaises(ValueError): execute(self.h,p,'Outra')
        for i in range(100): self.h.checklist_store.add('Projeto',str(i))
        with self.assertRaises(ValueError): execute(self.h,p,'Projeto')
