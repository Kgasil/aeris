import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.reminder import ReminderStore, MAX_REMINDERS, MAX_MINUTES
from aeris.settings import Settings, Appearance

class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.now=1000.0
        self.store=ReminderStore(lambda:self.now)

    def test_due_once_in_order(self):
        b=self.store.add('Segundo',2,True); a=self.store.add('Primeiro',1)
        self.assertEqual(self.store.list(),(a,b)); self.assertEqual(self.store.next_delay_ms(),30000)
        self.now+=59.5; self.assertEqual(self.store.next_delay_ms(),500); self.assertEqual(self.store.collect_due(),())
        self.now+=.5; self.assertEqual([r.id for r in self.store.collect_due()],[a.id]); self.assertEqual(self.store.collect_due(),())
        self.now+=60; self.assertEqual([r.id for r in self.store.collect_due()],[b.id]); self.assertIsNone(self.store.next_delay_ms())

    def test_edit_cancel_delete(self):
        a=self.store.add('A',1); b=self.store.edit(a.id,'B',2,True)
        self.assertEqual((b.id,b.title,b.due,b.alert),(a.id,'B',1120,True))
        self.store.cancel(b.id); self.now+=200; self.assertEqual(self.store.collect_due(),()); self.assertIsNone(self.store.next_delay_ms())
        with self.assertRaises(ValueError): self.store.edit(b.id,'C',1)
        with self.assertRaises(ValueError): self.store.cancel(b.id)
        self.store.delete(b.id); self.assertEqual(self.store.list(),())

    def test_validation(self):
        for args in [('',1,False),('x\n',1,False),('x'*201,1,False),('A',0,False),('A',MAX_MINUTES+1,False),('A',True,False),('A',1,1)]:
            with self.subTest(args=args),self.assertRaises(ValueError): self.store.add(*args)
        self.assertEqual(self.store.list(),())

    def test_limit_clear(self):
        for i in range(MAX_REMINDERS): self.store.add(str(i),1)
        with self.assertRaises(ValueError): self.store.add('Excesso',1)
        self.store.clear(); self.assertEqual(self.store.list(),()); self.assertIsNone(self.store.next_delay_ms())

    def test_overdue_and_clock_change(self):
        a=self.store.add('A',1); self.now-=300; self.assertEqual(self.store.collect_due(),()); self.assertEqual(self.store.next_delay_ms(),30000)
        self.now=1061; self.assertEqual(self.store.next_delay_ms(),1); self.assertEqual(self.store.collect_due()[0].state,'due')
        with self.assertRaises(ValueError): self.store.edit(a.id,'B',1)

    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Checklist',True)
            old=json.loads(p.read_text()); old['schema']=31; old.pop('reminder_enabled'); p.write_text(json.dumps(old))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.checklist_enabled); self.assertFalse(s.reminder_enabled)
            s.set_module('Reminder',True); s.set_appearance(Appearance(favorites=('Reminder',)))
            s=Settings(p); self.assertTrue(s.reminder_enabled); self.assertEqual(s.appearance.favorites,('Reminder',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
