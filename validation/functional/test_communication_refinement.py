"""Communication regression: real Tk with synthetic text and no external audio or network."""
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_TRANSLATION,COPY_TEXT,COPY_EMAIL,PLAY_VOICE
from aeris.meeting import Action

class CommunicationRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/'settings.json'))
        self.root.update()

    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')

    def test_translate_rejects_stale_input_and_replacement_during_confirmation(self):
        ui=self.open('Translate')
        self.h.permissions.set(COPY_TRANSLATION,True)
        ui.input.insert('1.0','Bom dia!'); ui.translate()
        self.assertEqual(ui.output,'Good morning!')
        ui.input.insert('end',' outro')
        with patch.object(self.root,'clipboard_clear') as clear: ui.copy(); clear.assert_not_called()
        self.assertEqual(ui.output,'')
        ui.input.delete('1.0','end'); ui.input.insert('1.0','Bom dia!'); ui.translate()
        def changed(*args,**kwargs):
            ui.input.delete('1.0','end'); ui.input.insert('1.0','Olá!'); ui.translate()
            return True
        with patch('aeris.translate_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertEqual(ui.output,'')
        ui.translate(); self.assertEqual(ui.output,'Hello!')
        ui.target.set('Espanhol'); self.assertEqual(ui.output,'')

    def test_voice_count_preserved_choice_and_invalid_controls(self):
        ui=self.open('Voice'); ui.text.insert('1.0','Olá'); self.root.update()
        self.assertEqual(ui.count.get(),'3 caracteres')
        ui.set_voices(('A','B')); ui.voice.set('B'); ui.set_voices(('B','C'))
        self.assertEqual(ui.voice.get(),'B')
        ui.set_voices(('A',)); self.assertEqual(ui.voice.get(),'Voz padrão do Windows')
        self.h.permissions.set(PLAY_VOICE,True); ui.rate.set('invalid')
        with patch('aeris.voice_ui.start_process') as launch:
            ui.play(); launch.assert_not_called()
        ui.clear(); self.assertEqual(ui.count.get(),'0 caracteres')
        with self.assertRaises(tk.TclError): ui.text.edit_undo()

    def test_text_rejects_stale_input_and_new_result(self):
        ui=self.open('Text'); self.h.permissions.set(COPY_TEXT,True)
        ui.input.insert('1.0','Olá'); self.root.update(); ui.apply()
        self.assertEqual(ui.output,'OLÁ')
        ui.input.insert('end','!')
        with patch.object(self.root,'clipboard_clear') as clear: ui.copy(); clear.assert_not_called()
        self.assertIsNone(ui.output)
        self.root.update(); ui.apply()
        with patch('aeris.text_ui.messagebox.askyesno',side_effect=lambda *a,**k:(ui.apply(),True)[1]),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIsNone(ui.output)

    def test_email_full_copy_and_regenerated_draft_rejection(self):
        ui=self.open('Email'); ui.details.insert('1.0','Informação fictícia.'); self.root.update(); ui.generate()
        self.h.permissions.set(COPY_EMAIL,True)
        self.assertEqual(str(ui.copy_full.cget('state')),'normal')
        with patch('aeris.email_ui.messagebox.askyesno',return_value=True),patch.object(self.root,'clipboard_clear'),patch.object(self.root,'clipboard_append') as append:
            ui.copy('full'); append.assert_called_once_with('Assunto: '+ui.draft.subject+'\n\n'+ui.draft.body)
        def changed(*args,**kwargs):
            ui.subject.set('Outro assunto'); ui.generate(); return True
        with patch('aeris.email_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy('full'); clear.assert_not_called()
        self.assertIsNone(ui.draft)

    def test_meeting_changed_record_not_deleted_and_search_preserves_selection(self):
        ui=self.open('Meeting')
        ui.title.set('A'); ui.save(); item=ui.store.get(ui.selected_id)
        ui.tree.selection_set(str(item.id)); ui.query.set('A'); ui.render()
        self.assertEqual(ui.tree.selection(),(str(item.id),)); ui.clear_search()
        self.assertEqual(ui.tree.selection(),(str(item.id),))
        def changed(*args,**kwargs):
            ui.store.edit(item.id,'B','','','','',()); return True
        with patch('aeris.meeting_ui.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get(item.id).title,'B')

    def test_meeting_changed_action_selection_not_deleted(self):
        ui=self.open('Meeting'); ui.actions=[Action('A'),Action('B')]; ui.render_actions(0)
        def changed(*args,**kwargs):
            ui.action_tree.selection_set('1'); return True
        with patch('aeris.meeting_ui.messagebox.askyesno',side_effect=changed): ui.delete_action()
        self.assertEqual([a.title for a in ui.actions],['A','B'])
        self.assertIn('alterada',ui.status.get())

if __name__=='__main__': main(verbosity=2)
