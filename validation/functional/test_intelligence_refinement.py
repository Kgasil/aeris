"""Real Tk regression with synthetic input; no live model, microphone or code execution."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPILOT_RUN,CONTEXT_PREVIEW,SEARCH_CAPTURE
from aeris.copilot import EXAMPLES

class IntelligenceRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/'settings.json')); self.root.update()

    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')

    def test_copilot_enter_prepares_but_never_executes(self):
        ui=self.open('Copilot'); self.h.toggle_tool('Reminder')
        self.h.permissions.set(COPILOT_RUN,True)
        ui.command.set(EXAMPLES[0])
        self.assertEqual(ui.count.get(),f'{len(EXAMPLES[0])} / 500 caracteres')
        self.assertEqual(ui.keyboard_prepare(),'break')
        self.assertIsNotNone(ui.session.pending); self.assertIsNone(self.h.reminder_store)
        ui.command.set('Comando inválido')
        self.assertIsNone(ui.session.pending)
        ui.confirm(); self.assertIsNone(self.h.reminder_store)

    def test_companion_model_change_preserves_unsent_draft(self):
        cop=self.open('Copilot'); cop.open_companion(); ui=cop.companion
        ui.model.set('local-a'); ui.input.insert('1.0','Rascunho fictício'); self.root.update()
        ui.history=[('user','Olá'),('assistant','Oi')]; ui.draw()
        ui.candidate=('Rascunho fictício',EXAMPLES[0]); ui.candidate_label.set(EXAMPLES[0])
        ui.model.set('local-b')
        self.assertFalse(ui.history); self.assertIsNone(ui.candidate)
        self.assertEqual(ui.input.get('1.0','end-1c'),'Rascunho fictício')
        self.assertEqual(ui.count.get(),f"{len('Rascunho fictício')} / 4000 caracteres")
        self.assertIsNone(cop.session.pending)

    def test_context_modified_record_not_authorized(self):
        ui=self.open('Context'); self.h.permissions.set(CONTEXT_PREVIEW,True)
        item=ui.store.add('A','Estudos','Original'); ui.render(); ui.tree.selection_set(str(item.id))
        def changed(*args,**kwargs):
            ui.store.edit(item.id,'A','Estudos','Outro texto'); return True
        with patch('aeris.context_ui.messagebox.askyesno',side_effect=changed): ui.toggle_selected()
        self.assertFalse(ui.store.selected(item.id))
        self.assertEqual(ui.tree.selection(),(str(item.id),))
        self.assertIn('alterado',ui.status.get())
        with patch('aeris.context_ui.messagebox.askyesno',return_value=True): ui.toggle_selected()
        ui.generate(); self.assertIn('Outro texto',ui.preview.get('1.0','end'))
        self.h.permissions.set(CONTEXT_PREVIEW,False)
        self.assertEqual(ui.preview.get('1.0','end-1c'),'')

    def test_interview_next_unanswered_and_stale_delete(self):
        ui=self.open('Interview')
        ui.answer.insert('1.0','Minha trajetória'); ui.save()
        ui.next_unanswered(); self.assertEqual(ui.current().id,'c2')
        ui.answer.insert('1.0','Exemplo'); ui.save()
        q=ui.current().id
        def changed(*args,**kwargs):
            ui.store.save(q,'Resposta revisada',tuple(False for _ in ui.checks)); return True
        with patch('aeris.interview_ui.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get(q).answer,'Resposta revisada')
        self.assertIn('alterada',ui.status.get())

    def search_session(self):
        ed=self.open('Capture'); a=ed.store.save('SQL','Fictício SQL',None)
        ed.fill(); ed.title.set('Rascunho')
        self.h.permissions.set(SEARCH_CAPTURE,True)
        ui=self.open('Search'); ui.sources['Capture'].set(True); ui.query.set('SQL')
        self.assertEqual(len(ui.results),1); ui.focus_results()
        return ui,ed,a

    def test_search_stale_result_cannot_open(self):
        ui,ed,a=self.search_session()
        ed.store.save('SQL','Novo conteúdo SQL',a.id)
        with patch.object(self.h,'open_search_result') as opened: ui.open_selected(); opened.assert_not_called()
        self.assertTrue(ui.window.winfo_exists())
        self.assertIsNone(ed.current)
        ui.clear_query(); self.assertFalse(ui.results)

    def test_search_revocation_during_discard_confirmation(self):
        ui,ed,a=self.search_session()
        def revoke(*args,**kwargs):
            self.h.permissions.set(SEARCH_CAPTURE,False); return True
        with patch('aeris.editor.messagebox.askyesno',side_effect=revoke): ui.open_selected()
        self.assertTrue(ui.window.winfo_exists()); self.assertEqual(ed.title.get(),'Rascunho')
        self.assertIsNone(ed.current)
        self.assertFalse(ui.results); self.assertEqual(ui.detail.get('1.0','end-1c'),'')

    def test_debug_cycles_diagnostics_and_rejects_stale_navigation(self):
        ui=self.open('Debug')
        ui.source.insert('1.0','from math import *\ndef f(x=[]):\n    return x')
        ui.run(); self.assertEqual(len(ui.analysis.diagnostics),2)
        ui.goto(); self.assertEqual(ui.diagnostic_index,0)
        ui.goto(True); self.assertEqual(ui.diagnostic_index,1)
        ui.goto(True); self.assertEqual(ui.diagnostic_index,0)
        ui.source.insert('end','\n# edit'); ui.goto(True)
        self.assertIsNone(ui.analysis)
        self.assertEqual(str(ui.next_button.cget('state')),'disabled')
        def changed(*args,**kwargs):
            ui.source.insert('end','\n# novo'); return True
        with patch('aeris.debug_ui.messagebox.askyesno',side_effect=changed): ui.clear()
        self.assertIn('# novo',ui.source.get('1.0','end'))

if __name__=='__main__': main(verbosity=2)
