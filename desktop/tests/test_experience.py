"""Source-level experience regression. Uses synthetic inputs; no real user's data."""
import base64
import json
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from aeris.experience import ExperienceHub
from aeris.settings import Settings
from aeris.permissions import COMPANION_SCREEN,COMPANION_MIC,COMPANION_CHAT,COPILOT_RUN
from aeris.screen_context import validate_png,describe_screen,installed_models
from aeris.experience_help import HELP

def tiny_png():
    r=tk.PhotoImage(width=2,height=2); r.put('#285640',to=(0,0,2,2))
    return base64.b64decode(r.data(format='png')) if not isinstance(r.data(format='png'),bytes) else r.data(format='png')

class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=tk.Tk()
        self.h=ExperienceHub(self.root,Settings(Path(self.tmp.name)/'settings.json'))
        self.ui=self.h.conversation; self.root.update()
    def tearDown(self):
        self.root.destroy(); self.ui=None; self.h=None; self.root=None
        import gc; gc.collect(); self.tmp.cleanup()
    def test_initial_layout_and_portuguese_search(self):
        self.assertEqual(self.h.view,'chat'); self.assertTrue(self.ui.window.winfo_ismapped())
        self.assertFalse(self.h.legacy_side.winfo_ismapped()); self.assertFalse(self.h.catalog.winfo_ismapped())
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC)); self.assertFalse(self.h.permissions.allowed(COMPANION_SCREEN))
        self.h.navigate('catalog'); self.root.update(); self.h.query.set('anotações')
        self.assertIn('Capture',[m.name for m in self.h.visible])
        self.h.navigate('chat'); self.assertEqual(self.h.view,'chat')
    def test_catalog_explains_all_existing_tools_and_advanced_controls_are_hidden(self):
        self.assertEqual(set(HELP),{m.name for m in self.h.modules})
        self.assertFalse(self.ui.advanced.winfo_ismapped())
        self.assertFalse(self.ui.proposal_panel.winfo_ismapped())
        self.ui.toggle_advanced(); self.root.update(); self.assertTrue(self.ui.advanced.winfo_ismapped())
        self.ui.toggle_advanced(); self.root.update(); self.assertFalse(self.ui.advanced.winfo_ismapped())
        self.h.navigate('catalog'); self.h.query.set('dados'); self.h.query.set('Anotações')
        i=next(i for i,m in enumerate(self.h.visible) if m.name=='Capture')
        self.h.listbox.selection_clear(0,'end'); self.h.listbox.selection_set(i); self.h.show_selected()
        self.assertIn('COMO USAR',self.h.example.cget('text')); self.assertIn('título',self.h.example.cget('text'))
    def test_discover_models_excludes_remote_and_cloud(self):
        class Response:
            status=200
            def read(self,n): return b'{"models":[{"name":"local"},{"name":"local"},{"name":"bad-cloud"},{"name":"remote","remote_host":"https://example.org"}]}'
        class Connection:
            def __init__(self,host,port,timeout): assert (host,port)==('127.0.0.1',11434)
            def request(self,method,path): assert (method,path)==('GET','/api/tags')
            def getresponse(self): return Response()
            def close(self): pass
        self.assertEqual(installed_models(connection_factory=Connection),('local',))
        with patch('aeris.experience.messagebox.askyesno',return_value=True),patch('aeris.experience.installed_models',return_value=('local',)):
            self.ui.detect_models()
            deadline=time.monotonic()+3
            while self.ui.busy and time.monotonic()<deadline: self.root.update(); time.sleep(.03)
        self.assertFalse(self.ui.busy); self.assertEqual(self.ui.model.get(),'local')
    def test_inline_action_requires_confirmation_and_rejects_edit(self):
        self.ui.input.insert('1.0','Lembre-me de relatório em 30 minutos'); self.root.update()
        with patch('aeris.experience.messagebox.askyesno',return_value=True): self.ui.send()
        self.assertIsNotNone(self.ui.session.pending); self.assertIsNone(self.h.reminder_store)
        self.ui.input.insert('end','!'); self.ui.confirm_action()
        self.assertIsNone(self.h.reminder_store)
        self.ui.input.delete('1.0','end'); self.ui.input.insert('1.0','Lembre-me de relatório em 30 minutos'); self.root.update()
        self.ui.prepare_action(); self.ui.confirm_action()
        self.assertEqual(len(self.h.reminder_store.list()),1)
    def test_notes_and_meeting_saved_to_existing_stores(self):
        self.ui.note.insert('1.0','Nota sintética'); self.ui.meeting_text.insert('1.0','Pauta fictícia')
        with patch('aeris.experience.messagebox.askyesno',return_value=True):
            self.ui.save_note(); self.ui.save_meeting()
        self.assertEqual(self.h.capture_store.list()[0].body,'Nota sintética')
        self.assertEqual(self.h.meeting_store.list()[0].notes,'Pauta fictícia')
        self.ui.meeting_summary(); self.assertIn('Pauta fictícia',self.ui.input.get('1.0','end-1c'))
        self.assertFalse(self.h.permissions.allowed(COMPANION_CHAT))
    def test_screen_requires_consent_and_revocation_discards(self):
        with patch('aeris.experience.messagebox.askyesno',return_value=False),patch('aeris.experience.capture_process') as cap:
            self.ui.capture(); cap.assert_not_called()
        self.h.permissions.set(COMPANION_SCREEN,True)
        self.ui.screen=b'synthetic'
        self.h.permissions.set(COMPANION_SCREEN,False)
        self.assertIsNone(self.ui.screen)
    def test_meeting_requires_consent_and_stop_discards_late_result(self):
        with patch('aeris.experience.messagebox.askyesno',return_value=False),patch('aeris.experience.speech_process') as mic:
            self.ui.start_meeting(); mic.assert_not_called()
        self.h.permissions.set(COMPANION_MIC,True)
        self.ui.meeting_active=True; self.ui.busy=True; self.ui.kind='meeting'; self.ui.cap=COMPANION_MIC
        self.ui.job=8; self.ui.meeting_text.configure(state='disabled')
        self.h.permissions.set(COMPANION_MIC,False)
        self.ui.results.put((8,True,'late text')); self.ui.poll()
        self.assertFalse(self.ui.meeting_active); self.assertNotIn('late text',self.ui.meeting_text.get('1.0','end'))
    def test_chat_and_vision_loopback_with_synthetic_reply(self):
        class Response:
            status=200
            def read(self,n): return b'{"done":true,"message":{"role":"assistant","content":"Resposta ficticia"}}'
        class Connection:
            def __init__(self,host,port,timeout): self.target=(host,port); self.body=None
            def request(self,method,path,body,headers): self.body=json.loads(body); self.method=method; self.path=path
            def getresponse(self): return Response()
            def close(self): pass
        calls=[]
        def factory(*a,**kw):
            c=Connection(*a,**kw); calls.append(c); return c
        raw=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',1,1)
        self.assertEqual(describe_screen('local-vision','Veja',raw,connection_factory=factory),'Resposta ficticia')
        self.assertEqual(calls[0].target,('127.0.0.1',11434))
        self.assertEqual(calls[0].body['messages'][-1]['images'],[base64.b64encode(raw).decode()])
        with self.assertRaises(ValueError): validate_png(raw[:16]+struct.pack('>II',9000,9000))
        with self.assertRaises(ValueError): describe_screen('cloud','Veja',raw,connection_factory=factory)
        self.ui.model.set('local'); self.ui.input.insert('1.0','Olá')
        with patch('aeris.experience.messagebox.askyesno',return_value=True),patch('aeris.companion_ui.chat',return_value='Resposta'):
            self.ui.send()
            deadline=time.monotonic()+3
            while self.ui.busy and time.monotonic()<deadline: self.root.update(); time.sleep(.03)
        self.assertFalse(self.ui.busy); self.assertEqual(self.ui.history[-1],('assistant','Resposta'))

if __name__=='__main__': unittest.main(verbosity=2)
