import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.ideas import IdeasStore, MAX_IDEAS, STATUSES
from aeris.settings import Settings, Appearance


class IdeasTests(unittest.TestCase):
    def setUp(self): self.s=IdeasStore()

    def test_create_and_edit(self):
        a=self.s.add('  Projeto  ','Trabalho','Linha 1\nLinha 2')
        self.assertEqual((a.title,a.category,a.status),('Projeto','Trabalho','Nova'))
        b=self.s.edit(a.id,'Projeto novo','Estudos','Descrição','Em desenvolvimento')
        self.assertEqual(b.id,a.id); self.assertEqual(self.s.get(a.id),b)
        self.assertEqual(self.s.list(),(b,))

    def test_search_and_filters(self):
        a=self.s.add('Automação','Tecnologia','Relatórios mensais')
        b=self.s.add('Relatórios','Trabalho','Automação','Arquivada')
        self.assertEqual(self.s.search('AUTOMACAO relatorios'),(a,b))
        self.assertEqual(self.s.search('relatorio',status='Arquivada'),(b,))
        self.assertEqual(self.s.search(category='TECNOLOGIA'),(a,))
        self.assertEqual(self.s.search('inexistente'),())

    def test_validation_and_atomic_edit(self):
        a=self.s.add('Ideia','Geral')
        for args in [('', 'Geral','','Nova'),('x'*161,'Geral','','Nova'),('a','x'*61,'','Nova'),('a','','','Nova'),('a','Geral','x'*4001,'Nova'),('a','Geral','\x00','Nova'),('a','Geral','','Inválido'),(None,'Geral','','Nova')]:
            with self.subTest(args=args), self.assertRaises(ValueError): self.s.edit(a.id,*args)
        self.assertEqual(self.s.get(a.id),a)
        with self.assertRaises(ValueError): self.s.search('x'*201)
        with self.assertRaises(ValueError): self.s.search(status='Inválido')

    def test_statuses_and_deletion(self):
        items=[self.s.add(str(i),'Geral',status=status) for i,status in enumerate(STATUSES)]
        for item in items: self.assertEqual(self.s.search(status=item.status),(item,))
        self.s.delete(items[0].id)
        with self.assertRaises(KeyError): self.s.get(items[0].id)
        self.s.clear(); self.assertEqual(self.s.list(),())
        self.assertGreater(self.s.add('Nova','Geral').id,items[-1].id)

    def test_limit(self):
        for i in range(MAX_IDEAS): self.s.add(str(i),'Geral')
        with self.assertRaises(ValueError): self.s.add('Excesso','Geral')
        self.assertEqual(len(self.s.list()),MAX_IDEAS)

    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Reminder',True)
            old=json.loads(p.read_text()); old['schema']=32; old.pop('ideas_enabled'); p.write_text(json.dumps(old))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.reminder_enabled); self.assertFalse(s.ideas_enabled)
            s.set_module('Ideas',True); s.set_appearance(Appearance(favorites=('Ideas',)))
            s=Settings(p); self.assertTrue(s.ideas_enabled); self.assertEqual(s.appearance.favorites,('Ideas',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
