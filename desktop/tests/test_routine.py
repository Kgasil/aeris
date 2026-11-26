import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from aeris.permissions import Permissions, ROUTINE_RUN, BRIDGE_RUN
from aeris.routine import RoutineEngine, RoutineStore, Routine
from aeris.settings import Settings

class RoutineTests(unittest.TestCase):
    def setUp(self):
        self.active = {'Routine','Bridge','Expand','Text','Capture','Translate','Email'}
        self.hub = SimpleNamespace(enabled=lambda n:n in self.active, permissions=Permissions(), expand_store=None)
        self.store = RoutineStore(); self.engine = RoutineEngine(self.hub)
        self.item = self.store.save('Estudo', ['Expand → Text','Text → Capture'])

    def grant(self):
        for cap in (ROUTINE_RUN, BRIDGE_RUN): self.hub.permissions.set(cap,True)

    def test_sequence(self):
        self.grant(); previews=self.engine.run(self.item,'  ;att   ')
        self.assertEqual([p.text for p in previews],['Atenciosamente,','Atenciosamente,'])
        self.assertFalse(hasattr(self.hub,'capture_store'))

    def test_denied_and_revoked(self):
        with self.assertRaises(PermissionError): self.engine.run(self.item,';att')
        self.grant(); self.hub.permissions.set(BRIDGE_RUN,False)
        with self.assertRaises(PermissionError): self.engine.run(self.item,';att')
        self.grant(); self.active.remove('Capture')
        with self.assertRaises(PermissionError): self.engine.run(self.item,';att')
        self.assertIsNone(self.hub.expand_store)

    def test_validation(self):
        for steps in ([],['Shell'],['Expand → Text']*6,['Text → Capture','Expand → Text']):
            with self.assertRaises(ValueError): self.store.save('Demo',steps)
        self.grant()
        with self.assertRaises(ValueError): self.engine.run(Routine('Demo',('Shell',)), 'A')

    def test_store(self):
        self.store.save('Estudo',['Expand → Text']); self.assertEqual(len(self.store.list()),1)
        for i in range(29): self.store.save(str(i),['Expand → Text'])
        with self.assertRaises(ValueError): self.store.save('31',['Expand → Text'])
        self.store.delete('Estudo'); self.assertEqual(len(self.store.list()),29)
        self.store.clear(); self.assertEqual(self.store.list(),())

    def test_translate_final(self):
        self.grant(); item=self.store.save('Email',['Expand → Text','Translate → Email'])
        preview=self.engine.run(item,'Bom dia!')[-1]
        self.assertEqual(preview.subject,'Update'); self.assertIn('Good morning!',preview.text)
        with self.assertRaises(ValueError): self.engine.run(item,'Frase não cadastrada.')

    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Bridge',True)
            data=json.loads(p.read_text()); data['schema']=18; del data['routine_enabled']; p.write_text(json.dumps(data))
            s=Settings(p); self.assertTrue(s.bridge_enabled); self.assertFalse(s.routine_enabled)
            s.set_module('Routine',True); self.assertTrue(Settings(p).routine_enabled)
