import unittest, json
from tempfile import TemporaryDirectory
from pathlib import Path
from dataclasses import asdict
from aeris.research import ResearchStore, MAX_REFERENCES
from aeris.settings import Settings, FLAGS, Appearance

class ResearchTests(unittest.TestCase):
    def test_crud(self):
        s=ResearchStore(); r=s.add('Título','Projeto','Livro',notes='Anotação'); self.assertEqual(s.get(r.id),r)
        updated=s.edit(r.id,'Título novo','Outro','Artigo','Autoria','2024','DOI fictício','Nota','Consultada')
        self.assertEqual(s.list(),(updated,)); s.delete(r.id); self.assertFalse(s.list())
    def test_search(self):
        s=ResearchStore(); a=s.add('Automação','Ciência','Artigo',notes='Dados úteis',state='Em leitura'); s.add('Automação','Outro','Livro')
        self.assertEqual(s.search('automacao uteis','CIENCIA','Em leitura'),(a,)); self.assertFalse(s.search(project='Cien'))
        with self.assertRaises(ValueError): s.search(state='invalid')
    def test_bibliography(self):
        s=ResearchStore(); r=s.add('Teste','P','Livro'); self.assertEqual(r.bibliography(),'[Autoria não informada] | Teste | [Ano não informado] | Livro')
        r=s.add('Teste','P','Site','Autoria','2020','https://example.invalid'); self.assertEqual(r.bibliography(),'Autoria | Teste | 2020 | Site | https://example.invalid')
    def test_invalid_and_atomic(self):
        s=ResearchStore(); r=s.add('Título','P','Livro')
        for args in [('', 'P','Livro'),('A','','Livro'),('A','P','x'),('A','P','Livro','','0000'),('A','P','Livro','','２０２４'),('A','P','Livro','','20x4'),('A','P','Livro','','2024','x'*501),('A','P','Livro','','','','x'*4001),('A\x00','P','Livro')]:
            with self.assertRaises(ValueError): s.edit(r.id,*args)
        self.assertEqual(s.list(),(r,))
    def test_limits_clear_isolation(self):
        s=ResearchStore()
        for i in range(MAX_REFERENCES): s.add(str(i),'P','Outro')
        with self.assertRaises(ValueError): s.add('Extra','P','Outro')
        self.assertFalse(ResearchStore().list()); s.clear(); self.assertFalse(s.list()); self.assertGreater(s.add('Novo','P','Outro').id,MAX_REFERENCES)
    def test_settings_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; data={k:False for k in FLAGS[:-1]}; data.update(schema=40,appearance=asdict(Appearance(favorites=('Learn',))),learn_enabled=True); p.write_text(json.dumps(data))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.learn_enabled); self.assertFalse(s.research_enabled)
            s.set_module('Research',True); s.set_appearance(Appearance(favorites=('Research',))); s=Settings(p)
            self.assertTrue(s.research_enabled and s.learn_enabled); self.assertEqual(s.appearance.favorites,('Research',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
