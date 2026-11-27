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
from aeris.experience import ExperienceHub,NAMES
from aeris.settings import Settings
from aeris.permissions import COMPANION_SCREEN,COMPANION_MIC,COMPANION_CHAT,COPILOT_RUN
from aeris.screen_context import validate_png,describe_screen,installed_models
from aeris.experience_help import HELP

def tiny_png():
    import zlib
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x28\x56\x40'*2)*2))+chunk(b'IEND',b'')

class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=tk.Tk()
        self.h=ExperienceHub(self.root,Settings(Path(self.tmp.name)/'settings.json'))
        self.ui=self.h.conversation; self.root.update()
    def tearDown(self):
        self.root.destroy(); self.ui=None; self.h=None; self.root=None
        import gc; gc.collect(); self.tmp.cleanup()
    def test_redesign_composer_and_shortcuts_remain_accessible(self):
        self.root.geometry('980x660')
        self.root.update()
        self.assertIs(self.ui.input.master,self.ui.composer)
        self.assertIs(self.ui.send_button.master.master,self.ui.composer)
        self.assertEqual(set(self.ui.quick_actions),{'screen','notes','meeting'})
        for width,height in ((980,660),(980,600)):
            self.root.geometry(f'{width}x{height}'); self.root.update()
            for control in (self.ui.send_button,*self.ui.quick_actions.values()):
                self.assertTrue(control.winfo_ismapped(),control.cget('text'))
                self.assertGreaterEqual(control.winfo_height(),control.winfo_reqheight(),control.cget('text'))
                self.assertGreaterEqual(control.winfo_width(),control.winfo_reqwidth(),control.cget('text'))
                self.assertLessEqual(control.winfo_rooty()+control.winfo_height(),self.root.winfo_rooty()+self.root.winfo_height())
        self.ui.input.insert('1.0','Rascunho de teste')
        self.ui.quick_actions['notes'].invoke(); self.root.update()
        self.assertEqual(self.h.view,'notes')
        self.h.navigate('chat'); self.root.update()
        self.assertEqual(self.ui.input.get('1.0','end-1c'),'Rascunho de teste')
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        self.assertFalse(self.h.permissions.allowed(COMPANION_SCREEN))

    def test_theme_switch_persists_and_preserves_draft(self):
        self.assertEqual(self.h.settings.appearance.theme,'Escuro')
        self.ui.input.insert('1.0','Rascunho fictício')
        self.h.toggle_theme(); self.root.update()
        self.assertEqual(Settings(self.h.settings.path).appearance.theme,'Claro')
        self.h.toggle_theme(); self.root.update()
        self.assertEqual(Settings(self.h.settings.path).appearance.theme,'Escuro')
        self.assertEqual(self.ui.input.get('1.0','end-1c'),'Rascunho fictício')
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        self.assertFalse(self.h.permissions.allowed(COMPANION_SCREEN))

    def test_appearance_actions_accessible_with_scrollable_tabs(self):
        from tkinter import ttk
        self.h.open_appearance()
        window=self.h.appearance_window.window
        window.geometry('450x420')
        self.root.update()
        def walk(widget):
            yield widget
            for child in widget.winfo_children(): yield from walk(child)
        controls=list(walk(window))
        tabs=next(w for w in controls if isinstance(w,ttk.Notebook))
        save=next(w for w in controls if isinstance(w,ttk.Button) and w.cget('text')=='Salvar')
        self.assertEqual(len(tabs.tabs()),2)
        for tab in tabs.tabs():
            tabs.select(tab); self.root.update()
            self.assertTrue(save.winfo_ismapped())
            self.assertLessEqual(save.winfo_rooty()+save.winfo_height(),window.winfo_rooty()+window.winfo_height())
        self.h.appearance_window.theme.set('Claro')
        save.invoke(); self.root.update()
        self.assertEqual(Settings(self.h.settings.path).appearance.theme,'Claro')

    def test_permission_refusal_and_revision_change(self):
        self.assertEqual(self.h.settings.appearance.theme,'Escuro')
        with patch('aeris.experience.ask_permission',return_value=False):
            self.assertFalse(self.ui.authorize(COMPANION_MIC,'Teste fictício'))
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        def stale(*args):
            self.h.permissions.revoke_all(); return True
        with patch('aeris.experience.ask_permission',side_effect=stale):
            self.assertFalse(self.ui.authorize(COMPANION_MIC,'Teste fictício'))
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        with patch('aeris.experience.ask_permission',return_value=True):
            self.assertTrue(self.ui.authorize(COMPANION_MIC,'Teste fictício'))
        self.h.permissions.revoke_all()
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))

    def test_microphone_feedback_requires_current_authorized_capture(self):
        self.h.permissions.set(COMPANION_MIC,True)
        self.ui.busy=True; self.ui.kind='voice_dictation'; self.ui.cap=COMPANION_MIC
        self.ui.voice_capture_job=self.ui.job
        self.ui.voice_events.put(('level',43)); self.ui.voice_events.put(('partial','Pergunta fictícia'))
        self.ui.drain_voice_feedback()
        self.assertEqual(self.ui.voice_level,43)
        self.assertIn('Pergunta fictícia',self.ui.voice_live.get())
        self.h.permissions.set(COMPANION_MIC,False)
        self.ui.voice_events.put(('partial','Atrasado'))
        self.ui.drain_voice_feedback()
        self.assertNotIn('Atrasado',self.ui.voice_live.get())
        self.ui.results.put((self.ui.job-1,True,('ok','Atrasado')))
        self.ui.poll()
        self.assertNotIn('Atrasado',self.ui.input.get('1.0','end'))

    def test_screen_panel_freezes_and_requires_explicit_send(self):
        self.h.navigate('screen'); self.ui.model.set('local-vision')
        with patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.ask_permission',return_value=True):
            self.ui.toggle_vision()
        self.root.update()
        self.assertTrue(self.ui.vision.active)
        self.ui.window.after_cancel(self.ui.vision_timer); self.ui.vision_timer=None
        self.ui.show_capture(tiny_png())
        self.ui.vision.record()
        self.h.permissions.set(COMPANION_MIC,True)
        with patch.object(self.ui,'start_voice_capture',side_effect=lambda kind:setattr(self.ui,'busy',True)):
            self.ui.panel_ask()
        self.assertEqual(self.ui.vision_phase,'listen')
        pending=self.ui.vision_pending; self.ui.busy=False
        self.ui.panel_result('panel_listen',True,True,('ok','O que é isso?'))
        self.assertEqual(self.ui.vision_phase,'review')
        with patch('aeris.experience.capture_process') as capture:
            self.ui.vision_next(); capture.assert_not_called()
        with patch('aeris.experience.ask_permission',return_value=False),patch('aeris.experience.describe_screen') as analyze:
            self.ui.panel_send(); analyze.assert_not_called()
        self.assertIs(self.ui.vision_pending,pending)
        self.h.permissions.set(COMPANION_MIC,False)
        self.assertFalse(self.ui.vision.active)
        self.assertIsNone(self.ui.vision_pending)
        self.assertIsNone(self.ui.vision_badge)

    def test_initial_layout_and_portuguese_search(self):
        self.assertEqual(self.h.view,'chat'); self.assertTrue(self.ui.window.winfo_ismapped())
        self.assertFalse(self.h.legacy_side.winfo_ismapped()); self.assertFalse(self.h.catalog.winfo_ismapped())
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC)); self.assertFalse(self.h.permissions.allowed(COMPANION_SCREEN))
        self.h.navigate('catalog'); self.root.update(); self.h.query.set('anotações')
        self.assertIn('Capture',[m.name for m in self.h.visible])
        self.h.navigate('chat'); self.assertEqual(self.h.view,'chat')
    def test_wind_brand_welcome_and_compact_menu_preserve_draft(self):
        self.assertEqual(len(self.ui.welcome_mark.find_all()),3)
        self.assertEqual(len(self.h.sidebar_mark.find_all()),3)
        self.assertTrue(self.ui.welcome.winfo_ismapped())
        self.ui.input.insert('1.0','Rascunho sintético')
        self.h.toggle_sidebar(); self.root.update()
        self.assertTrue(self.h.sidebar_compact)
        self.assertEqual(self.ui.input.get('1.0','end-1c'),'Rascunho sintético')
        self.h.toggle_sidebar(); self.root.update()
        self.assertFalse(self.h.sidebar_compact)
        self.ui.history=[('user','Oi'),('assistant','Olá')]; self.ui.draw(); self.root.update()
        self.assertFalse(self.ui.welcome.winfo_ismapped())
        self.assertTrue(self.ui.transcript.winfo_ismapped())
        self.ui.history=[]; self.ui.draw(); self.root.update()
        self.assertTrue(self.ui.welcome.winfo_ismapped())
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        self.assertFalse(self.h.permissions.allowed(COMPANION_SCREEN))

    def test_catalog_favorites_recent_and_scope_preserve_permissions(self):
        self.h.navigate('catalog')
        self.h.toggle_favorite('Data')
        self.assertIn('Data',self.h.settings.appearance.favorites)
        self.h.catalog_scope.set('Favoritas'); self.h.refresh()
        self.assertEqual([m.name for m in self.h.visible],['Data'])
        self.h.open_friendly('Data'); self.root.update()
        self.assertEqual(self.h.recent_tools[0],'Data')
        self.assertFalse(self.h.permissions.allowed(COMPANION_MIC))
        from aeris.permissions import DATA_READ
        self.assertFalse(self.h.permissions.allowed(DATA_READ))
        self.h.catalog_scope.set('Recentes'); self.h.refresh()
        self.assertEqual([m.name for m in self.h.visible],['Data'])
        self.h.toggle_favorite('Data')
        self.assertNotIn('Data',self.h.settings.appearance.favorites)
        self.h.clear_filters()
        self.assertEqual(len(self.h.visible),50)
        self.assertEqual(self.h.catalog_scope.get(),'Todas')

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
    def test_all_fifty_catalog_cards_show_correct_help_without_granting_access(self):
        self.h.navigate('catalog'); self.h.clear_filters()
        self.assertEqual(len(self.h.visible),50)
        self.assertEqual(len(NAMES),50)
        self.assertEqual(set(NAMES),set(HELP))
        for i,module in enumerate(self.h.visible):
            with self.subTest(tool=module.name):
                self.h.listbox.selection_clear(0,'end')
                self.h.listbox.selection_set(i); self.h.show_selected()
                description,example=HELP[module.name]
                self.assertTrue(description.strip()); self.assertTrue(example.strip())
                self.assertEqual(self.h.detail_name.cget('text'),NAMES[module.name])
                self.assertEqual(self.h.detail_desc.cget('text'),description)
                self.assertEqual(self.h.example.cget('text'),'COMO USAR\n'+example)
        self.assertEqual(self.h.recent_tools,[])
        for cap in (COMPANION_SCREEN,COMPANION_MIC,COMPANION_CHAT,COPILOT_RUN):
            self.assertFalse(self.h.permissions.allowed(cap))

    def test_catalog_detail_wrap_and_keyboard_return(self):
        from types import SimpleNamespace
        self.h.navigate('catalog')
        labels=(self.h.detail_name,self.h.detail_status,self.h.detail_desc,self.h.example,self.h.catalog_hint)
        for width,expected in ((180,152),(320,292),(700,420)):
            self.h.resize_catalog_detail(SimpleNamespace(width=width))
            for label in labels:
                self.assertEqual(int(label.cget('wraplength')),expected)
        self.h.resize_catalog_detail(SimpleNamespace(width=1))
        self.assertEqual(int(self.h.example.cget('wraplength')),420)
        self.h.query.set('Anotações')
        with patch.object(self.h.search,'focus_set') as focus:
            self.assertEqual(self.h.focus_catalog_search(),'break')
            focus.assert_called_once_with()
        self.assertEqual(self.h.query.get(),'Anotações')

    def test_responsive_catalog_filters_preserve_selection_and_query(self):
        from types import SimpleNamespace
        self.h.navigate('catalog')
        self.h.goal.set('Analisar informações')
        self.h.category.set('Business')
        self.h.query.set('dados')
        for width,row,column in ((400,1,1),(700,0,3),(400,1,1)):
            with self.subTest(width=width):
                self.h.resize_catalog_filters(SimpleNamespace(width=width))
                self.assertEqual(int(self.h.category_box.grid_info()['row']),row)
                self.assertEqual(int(self.h.category_box.grid_info()['column']),column)
                self.assertEqual(self.h.goal.get(),'Analisar informações')
                self.assertEqual(self.h.category_display.get(),'Negócios')
                self.assertEqual(self.h.query.get(),'dados')
        self.assertTrue(self.h.listbox.cget('xscrollcommand'))
        with patch.object(self.h.search,'focus_set') as focus:
            self.assertEqual(self.h.focus_catalog(),'break')
            self.assertTrue(focus.called)

    def test_catalog_detail_scroll_and_focus_reveal(self):
        from types import SimpleNamespace
        self.h.navigate('catalog')
        canvas=self.h.detail_canvas
        self.assertTrue(canvas.cget('yscrollcommand'))
        self.assertEqual(str(canvas.cget('takefocus')),'1')
        with patch.object(canvas,'yview_scroll') as scroll:
            self.assertEqual(self.h.scroll_catalog_detail(1,'pages'),'break')
            scroll.assert_called_once_with(1,'pages')
        with patch.object(canvas,'bbox',return_value=(0,0,300,600)),patch.object(canvas,'winfo_height',return_value=200),patch.object(canvas,'canvasy',return_value=0),patch.object(canvas,'yview_moveto') as move:
            widget=SimpleNamespace(winfo_y=lambda:500,winfo_height=lambda:30)
            self.h.reveal_catalog_control(SimpleNamespace(widget=widget))
            move.assert_called_once_with(330/600)

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
        with patch('aeris.experience.ask_permission',return_value=True),patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.messagebox.askyesno',return_value=True),patch('aeris.experience.installed_models',return_value=('local',)):
            self.ui.detect_models()
            deadline=time.monotonic()+3
            while self.ui.busy and time.monotonic()<deadline: self.root.update(); time.sleep(.03)
        self.assertFalse(self.ui.busy); self.assertEqual(self.ui.model.get(),'local')
    def test_inline_action_requires_confirmation_and_rejects_edit(self):
        self.ui.input.insert('1.0','Lembre-me de relatório em 30 minutos'); self.root.update()
        with patch('aeris.experience.ask_permission',return_value=True),patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.messagebox.askyesno',return_value=True): self.ui.send()
        self.assertIsNotNone(self.ui.session.pending); self.assertIsNone(self.h.reminder_store)
        self.ui.input.insert('end','!'); self.ui.confirm_action()
        self.assertIsNone(self.h.reminder_store)
        self.ui.input.delete('1.0','end'); self.ui.input.insert('1.0','Lembre-me de relatório em 30 minutos'); self.root.update()
        self.ui.prepare_action(); self.ui.confirm_action()
        self.assertEqual(len(self.h.reminder_store.list()),1)
    def test_notes_and_meeting_saved_to_existing_stores(self):
        self.ui.note.insert('1.0','Nota sintética'); self.ui.meeting_text.insert('1.0','Pauta fictícia')
        with patch('aeris.experience.ask_permission',return_value=True),patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.messagebox.askyesno',return_value=True):
            self.ui.save_note(); self.ui.save_meeting()
        self.assertEqual(self.h.capture_store.list()[0].body,'Nota sintética')
        self.assertEqual(self.h.meeting_store.list()[0].notes,'Pauta fictícia')
        # No model configured: opening help must not transmit or save the transcript.
        with patch.object(self.ui,'configure_ai') as help_ui, patch('aeris.experience.prepare_minutes') as prepare:
            self.ui.meeting_summary()
            help_ui.assert_called_once(); prepare.assert_not_called()
        self.assertFalse(self.h.permissions.allowed(COMPANION_CHAT))
        self.assertEqual(self.ui.input.get('1.0','end-1c'),'')
        self.ui.model.set('local')
        with patch('aeris.experience.ask_permission',return_value=False),patch('aeris.experience.ask_confirmation',return_value=False),patch('aeris.experience.messagebox.askyesno',return_value=False), patch('aeris.experience.prepare_minutes') as prepare:
            self.ui.meeting_summary(); prepare.assert_not_called()
        self.assertFalse(self.h.permissions.allowed(COMPANION_CHAT))
        from aeris.meeting_intelligence import Draft
        draft=Draft('Resumo fictício',())
        with patch('aeris.experience.ask_permission',return_value=True),patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.messagebox.askyesno',return_value=True), patch('aeris.experience.prepare_minutes',return_value=draft) as prepare:
            self.ui.meeting_summary()
            deadline=time.monotonic()+3
            while self.ui.busy and time.monotonic()<deadline: self.root.update(); time.sleep(.03)
            prepare.assert_called_once_with('local','Pauta fictícia')
        self.assertFalse(self.ui.busy)
        self.assertTrue(self.h.alive(self.h.meeting_window) or self.h.meeting_store is not None)
        self.assertEqual(len(self.h.meeting_store.list()),1)
        self.assertIsNotNone(self.ui.meeting_review)
        self.h.permissions.set(COMPANION_CHAT,False)
        self.assertIsNone(self.ui.meeting_review)
        self.assertEqual(len(self.h.meeting_store.list()),1)
    def test_screen_requires_consent_and_revocation_discards(self):
        with patch('aeris.experience.ask_permission',return_value=False),patch('aeris.experience.ask_confirmation',return_value=False),patch('aeris.experience.messagebox.askyesno',return_value=False),patch('aeris.experience.capture_process') as cap:
            self.ui.capture(); cap.assert_not_called()
        self.h.permissions.set(COMPANION_SCREEN,True)
        self.ui.screen=b'synthetic'
        self.h.permissions.set(COMPANION_SCREEN,False)
        self.assertIsNone(self.ui.screen)
    def test_meeting_notes_stay_separate_and_are_saved_explicitly(self):
        self.ui.meeting_text.insert('1.0','Transcrição fictícia')
        self.ui.meeting_notes.insert('1.0','Minha nota')
        self.assertEqual(self.ui.meeting_content(),'Transcrição fictícia\n\nNotas manuais:\nMinha nota')
        self.assertIsNone(self.h.meeting_store)
        with patch('aeris.experience.messagebox.askyesno',return_value=False):
            self.ui.save_meeting()
        self.assertIsNone(self.h.meeting_store)
        with patch('aeris.experience.messagebox.askyesno',return_value=True):
            self.ui.save_meeting()
        self.assertIn('Minha nota',self.h.meeting_store.list()[0].notes)
        self.ui.clear_workspace()
        self.assertEqual(self.ui.meeting_notes.get('1.0','end-1c'),'')
        self.assertEqual(self.ui.meeting_text.get('1.0','end-1c'),'')

    def test_meeting_requires_consent_and_stop_discards_late_result(self):
        with patch('aeris.experience.ask_permission',return_value=False),patch('aeris.experience.ask_confirmation',return_value=False),patch('aeris.experience.messagebox.askyesno',return_value=False),patch('aeris.experience.speech_process') as mic:
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
        with patch('aeris.experience.ask_permission',return_value=True),patch('aeris.experience.ask_confirmation',return_value=True),patch('aeris.experience.messagebox.askyesno',return_value=True),patch('aeris.companion_ui.chat',return_value='Resposta'):
            self.ui.send()
            deadline=time.monotonic()+3
            while self.ui.busy and time.monotonic()<deadline: self.root.update(); time.sleep(.03)
        self.assertFalse(self.ui.busy); self.assertEqual(self.ui.history[-1],('assistant','Resposta'))

if __name__=='__main__': unittest.main(verbosity=2)
