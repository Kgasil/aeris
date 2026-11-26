import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.checklist import ChecklistStore, MAX_LISTS, MAX_TASKS
from aeris.settings import Settings, Appearance

class ChecklistTests(unittest.TestCase):
    def setUp(self):
        self.s=ChecklistStore(); self.s.create('Trabalho')

    def test_independent_lists_and_progress(self):
        self.s.create('Estudos')
        a=self.s.add('Trabalho','Relatório','Alta'); b=self.s.add('Estudos','Python')
        self.assertNotEqual(a.id,b.id)
        self.s.toggle('Trabalho',a.id)
        self.assertEqual(self.s.progress('Trabalho'),(1,1)); self.assertEqual(self.s.progress('Estudos'),(0,1))
        self.assertEqual(len(self.s.list()),2)
        self.s.toggle('Trabalho',a.id); self.assertEqual(self.s.progress('Trabalho'),(0,1))

    def test_edit_preserves_id_and_state(self):
        a=self.s.add('Trabalho','Relatório'); self.s.toggle('Trabalho',a.id)
        b=self.s.edit('Trabalho',a.id,'Relatório final','Baixa')
        self.assertEqual((b.id,b.title,b.priority,b.done),(a.id,'Relatório final','Baixa',True))
        self.s.delete('Trabalho',a.id); self.assertEqual(self.s.progress('Trabalho'),(0,0))

    def test_rename_and_delete(self):
        a=self.s.add('Trabalho','A'); self.s.create('Estudos')
        with self.assertRaises(ValueError): self.s.rename('Trabalho','Estudos')
        self.assertEqual(self.s.rename('Trabalho','Projetos'),'Projetos'); self.assertEqual(self.s.tasks('Projetos'),(a,))
        self.s.delete_list('Projetos'); self.assertEqual(self.s.list(),()); self.assertEqual(self.s.names(),('Estudos',))

    def test_validation(self):
        for value in ('','   ','a'*81,'a\n','Trabalho',None):
            with self.subTest(value=value),self.assertRaises(ValueError): self.s.create(value)
        for title,priority in [('', 'Normal'),('x'*201,'Alta'),('x\0','Normal'),('ok','Urgente'),(None,'Normal')]:
            with self.subTest(title=title,priority=priority),self.assertRaises(ValueError): self.s.add('Trabalho',title,priority)
        self.assertEqual(self.s.list(),())

    def test_limits_and_clear(self):
        for i in range(MAX_LISTS-1): self.s.create(str(i))
        with self.assertRaises(ValueError): self.s.create('Excesso')
        for i in range(MAX_TASKS): self.s.add('Trabalho',str(i))
        with self.assertRaises(ValueError): self.s.add('Trabalho','Excesso')
        self.s.clear(); self.assertEqual(self.s.names(),()); self.assertEqual(self.s.list(),())

    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Focus',True)
            old=json.loads(p.read_text()); old['schema']=30; old.pop('checklist_enabled'); p.write_text(json.dumps(old))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.focus_enabled); self.assertFalse(s.checklist_enabled)
            s.set_module('Checklist',True); s.set_appearance(Appearance(favorites=('Checklist',)))
            s=Settings(p); self.assertTrue(s.checklist_enabled); self.assertEqual(s.appearance.favorites,('Checklist',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
