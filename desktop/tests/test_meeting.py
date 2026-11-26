import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.meeting import Action, MeetingStore, minutes
from aeris.settings import Settings, Appearance

class MeetingTests(unittest.TestCase):
    def test_records(self):
        s=MeetingStore(); a=Action('Revisar','Equipe','2028-02-29',True)
        m=s.add(' Reunião ','2026-11-25','Ana\nBruno','Pauta','Decisão',[a]); self.assertEqual(m.title,'Reunião'); self.assertEqual(m.completed,1)
        self.assertEqual(s.search('reuniao equipe'),(m,)); self.assertEqual(s.search('decisao'),(m,))
        n=s.edit(m.id,'Outra','','','','',()); self.assertEqual(n.id,m.id); self.assertEqual(n.completed,0)
        s.delete(m.id); self.assertEqual(s.list(),()); s.add('Nova','','','','',()); s.clear(); self.assertEqual(s.list(),())
    def test_validation(self):
        for vals in [('','','','','',()),('A','2026-02-29','','','',()),('A','20261125','','','',()),('A','','','','x'*8001,()),('A','','','','',[{}]),('A','','','','',[Action('A')]*51)]:
            with self.assertRaises(ValueError): MeetingStore().add(*vals)
        for vals in [('',),('A','B','2026-13-01'),('A','B','',1),('A\nB',),('A','x'*121)]:
            with self.assertRaises(ValueError): Action(*vals)
    def test_atomicity(self):
        s=MeetingStore(); a=[Action('A')]; m=s.add('A','','','','',a); a.clear(); self.assertEqual(len(m.actions),1)
        with self.assertRaises(ValueError): s.edit(m.id,'','','','','',())
        self.assertIs(s.get(m.id),m)
    def test_capacity(self):
        s=MeetingStore()
        for i in range(50): s.add(str(i),'','','','',())
        with self.assertRaises(ValueError): s.add('51','','','','',())
        s.delete(1); self.assertEqual(s.add('51','','','','',()).id,51)
    def test_minutes(self):
        m=MeetingStore().add('Projeto','','','Indicadores','Aprovar',[Action('Revisar','Ana','2026-12-01'),Action('Enviar',done=True)])
        t=minutes(m); self.assertIn('1/2 atividades concluídas',t); self.assertIn('[ ] Revisar | Responsável: Ana | Prazo: 2026-12-01',t); self.assertIn('[x] Enviar | Responsável: Não definido',t); self.assertIn('Data: Não informada',t)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Debug',True); old=json.loads(p.read_text()); old['schema']=48; old.pop('meeting_enabled'); p.write_text(json.dumps(old)); s=Settings(p)
            self.assertTrue(s.debug_enabled); self.assertFalse(s.meeting_enabled); self.assertFalse(s.warning)
            s.set_module('Meeting',True); s.set_appearance(Appearance(favorites=('Meeting',))); s=Settings(p); self.assertTrue(s.meeting_enabled); self.assertEqual(s.appearance.favorites,('Meeting',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
