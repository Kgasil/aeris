import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
from aeris.protected_storage import ProtectedStorage, MAGIC, snapshot, rebuild
from aeris.checklist import ChecklistStore
from aeris.ideas import IdeasStore
from aeris.learn import LearnStore

class FakeBackend:
    """Reversible test double, NOT encryption. Never used in production."""
    def protect(self, data): return bytes(b ^ 0xA5 for b in data)
    def unprotect(self, data): return bytes(b ^ 0xA5 for b in data)

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.storage=ProtectedStorage(self.tmp.name,FakeBackend())
        self.store=ChecklistStore(); self.store.create('Estudos'); self.store.create('Vazia')
        t=self.store.add('Estudos','Dado fictício privado','Alta'); self.store.toggle('Estudos',t.id)

    def test_checklist_roundtrip(self):
        self.storage.save('Checklist',self.store)
        self.assertEqual(snapshot('Checklist',self.storage.load('Checklist')),snapshot('Checklist',self.store))
        self.assertNotIn('Dado fictício privado'.encode(),self.storage.path('Checklist').read_bytes())
        self.assertEqual(self.storage.load('Checklist').names(),('Estudos','Vazia'))

    def test_ideas_roundtrip(self):
        store=IdeasStore(); store.add('Título','Categoria','Texto\nTeste','Arquivada')
        self.storage.save('Ideas',store)
        self.assertEqual(snapshot('Ideas',self.storage.load('Ideas')),snapshot('Ideas',store))

    def test_learn_roundtrip(self):
        store=LearnStore(); p=store.create('Python'); t=store.add(p.id,'Tópico',90); store.toggle(p.id,t.id); store.add(p.id,'Outro',30); store.move(p.id,t.id,1)
        self.storage.save('Learn',store)
        self.assertEqual(snapshot('Learn',self.storage.load('Learn')),snapshot('Learn',store))

    def test_overwrite_and_atomic_failure(self):
        self.storage.save('Checklist',self.store); path=self.storage.path('Checklist'); original=path.read_bytes(); self.store.add('Estudos','Novo')
        with self.assertRaises(FileExistsError): self.storage.save('Checklist',self.store)
        with patch('aeris.protected_storage.os.replace',side_effect=OSError('falha')):
            with self.assertRaises(OSError): self.storage.save('Checklist',self.store,overwrite=True)
        self.assertEqual(path.read_bytes(),original); self.assertEqual(list(path.parent.glob('.storage-*')),[])
        with patch.object(self.storage.backend,'protect',side_effect=OSError('DPAPI falhou')):
            with self.assertRaises(OSError): self.storage.save('Checklist',self.store,overwrite=True)
        self.assertEqual(path.read_bytes(),original)
        self.storage.save('Checklist',self.store,overwrite=True); self.assertEqual(len(self.storage.load('Checklist').tasks('Estudos')),2)

    def test_corruption_and_module_binding(self):
        self.storage.save('Checklist',self.store); raw=self.storage.path('Checklist').read_bytes()
        self.storage.path('Ideas').write_bytes(raw)
        with self.assertRaises(ValueError): self.storage.load('Ideas')
        path=self.storage.path('Checklist'); path.write_bytes(b'bad')
        with self.assertRaises(ValueError): self.storage.save('Checklist',self.store,overwrite=True)
        self.assertEqual(path.read_bytes(),b'bad')
        self.storage.delete('Checklist'); self.assertFalse(path.exists()); self.assertEqual(len(self.store.list()),1)

    def test_strict_schema(self):
        for records in ([{'name':'A','tasks':[{'title':'t','priority':'Normal','done':1}]}], [{'name':'A','tasks':[]},{'name':'A','tasks':[]}], [{'name':'A','tasks':[],'extra':True}], [{'name':'A','tasks':[{'title':'t','priority':'X','done':False}]}]):
            with self.assertRaises(ValueError): rebuild('Checklist',records)
        for raw in (b'{"schema":1,"schema":1,"module":"Checklist","records":[]}',json.dumps({'schema':True,'module':'Checklist','records':[]}).encode()):
            self.storage.path('Checklist').write_bytes(MAGIC+self.storage.backend.protect(raw))
            with self.assertRaises(ValueError): self.storage.load('Checklist')
        with self.assertRaises(ValueError): self.storage.path('../bad')

    def test_lock_contention(self):
        path=self.storage.path('Checklist')
        with self.storage.lease(path):
            with self.assertRaises(OSError): self.storage.save('Checklist',self.store)
        self.storage.save('Checklist',self.store)

    @unittest.skipUnless(sys.platform=='win32','Windows DPAPI real')
    def test_native_dpapi(self):
        storage=ProtectedStorage(self.tmp.name)
        storage.save('Checklist',self.store)
        self.assertEqual(snapshot('Checklist',storage.load('Checklist')),snapshot('Checklist',self.store))
        self.assertNotIn('Dado fictício privado'.encode(),storage.path('Checklist').read_bytes())

    @unittest.skipIf(sys.platform=='win32','Sem DPAPI apenas fora do Windows')
    def test_no_plaintext_fallback(self):
        with self.assertRaises(OSError): ProtectedStorage(self.tmp.name)
        self.assertEqual(list(Path(self.tmp.name).iterdir()),[])

class ExtendedStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.storage=ProtectedStorage(self.tmp.name,FakeBackend())

    def roundtrip(self,module,store):
        self.storage.save(module,store)
        restored=self.storage.load(module)
        self.assertEqual(snapshot(module,restored),snapshot(module,store))
        return restored

    def test_meeting_actions(self):
        from aeris.meeting import MeetingStore, Action, minutes
        s=MeetingStore(); m=s.add('Reunião','2026-11-25','Equipe','Pauta','Decisão\nTeste',[Action('Revisar','Pessoa','2026-12-01',True),Action('Enviar')])
        r=self.roundtrip('Meeting',s)
        self.assertEqual(minutes(r.list()[0]),minutes(m)); self.assertEqual(r.list()[0].completed,1)
        self.assertNotEqual(r.add('Outra','','','','',[]).id,r.list()[0].id)

    def test_research_metadata(self):
        from aeris.research import ResearchStore
        s=ResearchStore(); s.add('Fonte','Projeto','Artigo','Autoria','2026','doi fictício','Anotação','Consultada'); s.add('Outra','Projeto','Livro')
        r=self.roundtrip('Research',s)
        self.assertEqual(len(r.search('anotacao')),1)
        self.assertIn('[Autoria não informada]',r.list()[1].bibliography())

    def test_flashcards_schedule(self):
        from datetime import datetime, timezone, timedelta
        from aeris.flashcards import FlashcardsStore
        now=datetime(2026,11,25,tzinfo=timezone.utc); s=FlashcardsStore(lambda:now)
        card=s.add('Dados','Pergunta','Resposta'); reviewed=s.review(card.id,'Fácil'); s.add('Dados','Outra','Resposta')
        self.roundtrip('Flashcards',s)
        r=rebuild('Flashcards',snapshot('Flashcards',s),clock=lambda:now+timedelta(days=2))
        self.assertEqual(r.get(1).due,reviewed.due); self.assertEqual(r.get(1).reviews,1)
        self.assertEqual([c.id for c in r.search(due_only=True)],[2])
        r=rebuild('Flashcards',snapshot('Flashcards',s),clock=lambda:now+timedelta(days=3))
        self.assertEqual(r.review(1,'Fácil').interval,9*86400)

    def test_reminder_deadlines_and_states(self):
        from aeris.reminder import ReminderStore
        s=ReminderStore(lambda:1000); s.add('Vence',1,True); s.add('Futuro',10,True); cancelled=s.add('Cancelado',5,True); s.cancel(cancelled.id)
        data=snapshot('Reminder',s)
        r=rebuild('Reminder',data,clock=lambda:1100)
        self.assertEqual([(x.title,x.due,x.state) for x in r.list()], [('Vence',1060,'due'),('Cancelado',1300,'cancelled'),('Futuro',1600,'pending')])
        self.assertEqual(r.collect_due(),()); self.assertEqual(r.next_delay_ms(),30000)
        r.clock=lambda:1600; self.assertEqual([x.title for x in r.collect_due()],['Futuro']); self.assertIsNone(r.next_delay_ms())
        # Real envelope roundtrip preserves future times and already-final states.
        import time
        s=ReminderStore(); s.add('Futuro',60,True); s.restore_record('Antigo',time.time()-60,True,'due')
        self.roundtrip('Reminder',s)

    def test_invalid_extended_records(self):
        bad=[('Meeting',[dict(title='A',day='',participants='',agenda='',notes='',actions=[dict(title='A',owner='',due='',done=1)])]),
             ('Research',[dict(title='A',project='B',kind='X',authors='',year='',locator='',notes='',state='A consultar')])]
        card=dict(deck='A',question='Q',answer='A',due='2026-11-25T00:00:00+00:00',interval=600,reviews=1)
        for change in ({'due':'2026-11-25T00:00:00'},{'due':'2026-11-25T00:00:00-03:00'},{'interval':-1},{'reviews':False},{'reviews':0},{'interval':366*86400}):
            bad.append(('Flashcards',[dict(card,**change)]))
        rem=dict(title='A',due=1600,alert=True,state='pending')
        for change in ({'due':float('nan')},{'due':True},{'due':10**500},{'due':-1},{'alert':1},{'state':'unknown'}):
            bad.append(('Reminder',[dict(rem,**change)]))
        for module,records in bad:
            with self.subTest(module=module,records=records):
                with self.assertRaises(ValueError): rebuild(module,records)

    def test_old_schema_compatible_and_module_bound(self):
        store=ChecklistStore(); store.create('Anterior'); self.storage.save('Checklist',store)
        self.assertEqual(self.storage.load('Checklist').names(),('Anterior',))
        self.storage.path('Meeting').write_bytes(self.storage.path('Checklist').read_bytes())
        with self.assertRaises(ValueError): self.storage.load('Meeting')

class RecoveryBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name); self.backend=FakeBackend(); self.storage=ProtectedStorage(self.folder,self.backend)
        self.store=ChecklistStore(); self.store.create('A'); self.store.add('A','Primeiro')
    def test_previous_and_delete(self):
        self.storage.save('Checklist',self.store); self.store.add('A','Segundo')
        self.storage.save('Checklist',self.store,overwrite=True,keep_previous=True)
        self.assertEqual(len(self.storage.load_previous('Checklist').tasks('A')),1)
        self.assertEqual(len(self.storage.load('Checklist').tasks('A')),2)
        self.storage.delete_previous('Checklist'); self.assertFalse(self.storage.previous_path('Checklist').exists()); self.assertTrue(self.storage.path('Checklist').exists())
    def test_backup_roundtrip_and_invalid_blob(self):
        from aeris.backup import BackupService
        from aeris.permissions import Permissions, CREATE_BACKUP, RESTORE_BACKUP
        from aeris.settings import Settings
        p=Permissions(); p.set(CREATE_BACKUP,True); p.set(RESTORE_BACKUP,True)
        b=BackupService(Settings(self.folder/'settings.json'),p,self.backend)
        self.storage.save('Checklist',self.store); path=self.folder/'copy.aerisbackup'; self.assertIn('Checklist',b.create(path)); self.assertIn('Checklist',b.inspect(path))
        self.store.add('A','Segundo'); self.storage.save('Checklist',self.store,overwrite=True)
        before=self.storage.path('Checklist').read_bytes()
        with self.assertRaises(ValueError): self.storage.restore_blob('Checklist',b'bad')
        self.assertEqual(before,self.storage.path('Checklist').read_bytes())
        self.assertEqual(b.restore(path,'Checklist'),self.storage.previous_path('Checklist'))
        self.assertEqual(len(self.storage.load('Checklist').tasks('A')),1); self.assertEqual(len(self.storage.load_previous('Checklist').tasks('A')),2)
