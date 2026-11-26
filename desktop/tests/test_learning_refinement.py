"""Learning UI regression, synthetic records and simulated speech effects."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from unittest import TestCase, main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import PLAY_PRONOUNCE
from tests.smoke_voice import FakeProcess

class LearningRefinement(TestCase):
    def _collect_ui(self):
        import gc
        self.h=None
        self.root=None
        gc.collect()

    def setUp(self):
        self.addCleanup(self._collect_ui)
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/'settings.json'))
        self.root.update()

    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')

    def test_learn_pending_filter_and_stale_plan_confirmation(self):
        ui=self.open('Learn')
        p=ui.store.create('Python'); a=ui.store.add(p.id,'A',25); b=ui.store.add(p.id,'B',50)
        ui.store.toggle(p.id,a.id); ui.refresh(p.id)
        ui.pending_only.set(True); ui.render()
        self.assertEqual(ui.tree.get_children(),(str(b.id),))
        self.assertEqual(ui.stats.get(),'1/2 tópicos · 25/75 min estimados concluídos')
        ui.tree.selection_set(str(b.id))
        def changed(*args,**kwargs):
            ui.store.edit(p.id,b.id,'B revisado',60); return True
        with patch('aeris.learn_ui.messagebox.askyesno',side_effect=changed): ui.delete_topic()
        self.assertEqual(ui.store.get(p.id).topics[-1].title,'B revisado')
        self.assertIn('alterado',ui.status.get())
        ui.store.delete_plan(p.id); other=ui.store.create('Python')
        with self.assertRaises(ValueError): ui.plan_id()
        ui.refresh(other.id); self.assertEqual(ui.plan_id(),other.id)

    def test_research_filters_keep_draft_and_changed_record_not_deleted(self):
        ui=self.open('Research')
        a=ui.store.add('A','Estudos','Livro'); b=ui.store.add('B','Trabalho','Artigo')
        ui.render(); ui.tree.selection_set(str(a.id)); ui.load_selected()
        ui.title.set('Rascunho'); ui.project_filter.set('Estudos'); ui.render()
        self.assertEqual(ui.tree.selection(),(str(a.id),))
        ui.clear_filters(); self.assertEqual(len(ui.tree.get_children()),2)
        self.assertEqual(ui.title.get(),'Rascunho')
        def changed(*args,**kwargs):
            ui.store.edit(a.id,'Atualizado','Estudos','Livro'); return True
        with patch('aeris.research_ui.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get(a.id).title,'Atualizado')
        self.assertEqual(ui.title.get(),'Rascunho')

    def test_flashcards_changed_before_reveal_not_exposed(self):
        ui=self.open('Flashcards')
        a=ui.store.add('Geral','Pergunta','Resposta A'); ui.render()
        ui.start_review(); self.assertEqual(ui.review_id,a.id)
        ui.store.edit(a.id,'Geral','Nova pergunta','Resposta B')
        ui.reveal()
        self.assertIsNone(ui.review_id)
        self.assertNotIn('Resposta B',ui.review_text.get('1.0','end'))
        ui.start_review(); ui.reveal(); ui.rate('Médio')
        self.assertEqual(ui.store.get(a.id).reviews,1)

    def test_flashcards_changed_after_reveal_not_rated(self):
        ui=self.open('Flashcards')
        a=ui.store.add('Geral','Q','A'); ui.render()
        ui.start_review(); ui.reveal()
        ui.store.edit(a.id,'Geral','Q','Outro')
        ui.rate('Fácil')
        self.assertEqual(ui.store.get(a.id).reviews,0)
        self.assertIsNone(ui.review_id)
        ui.query.set('inexistente'); ui.render(); self.assertFalse(ui.tree.get_children())
        ui.clear_filters(); self.assertEqual(ui.tree.get_children(),(str(a.id),))

    def test_pronounce_preserves_voice_and_cancels_on_language_change(self):
        ui=self.open('Pronounce')
        ui.set_voices(('A','B')); ui.voice.set('B'); ui.set_voices(('B','C'))
        self.assertEqual(ui.voice.get(),'B')
        ui.text.insert('1.0','Good morning!')
        self.h.permissions.set(PLAY_PRONOUNCE,True)
        fake=FakeProcess()
        with patch('aeris.voice_ui.start_process',return_value=fake) as launch:
            ui.play(); launch.assert_called_once(); self.assertIs(ui.process,fake)
            ui.language.set('Español')
            self.assertTrue(fake.killed.is_set()); self.assertIsNone(ui.process)
            self.assertEqual(ui.voices,())
            self.assertIn('¡Buenos días!',ui.exercise_choice.cget('values'))
            self.assertEqual(ui.text.get('1.0','end-1c'),'Good morning!')
            ui.play(); launch.assert_called_once()

    def test_accessibility_jump_and_stale_discard(self):
        ui=self.open('Accessibility')
        ui.source.insert('1.0','Um\nDois\nTrês'); ui.load(); ui.guide.set(True); ui.style()
        self.assertEqual(ui.position.get(),'Linha 1/3')
        ui.jump(True); self.assertEqual(ui.position.get(),'Linha 3/3')
        self.assertEqual(str(ui.last.cget('state')),'disabled')
        ui.jump(False); self.assertEqual(ui.position.get(),'Linha 1/3')
        def changed(*args,**kwargs):
            ui.source.insert('end','\nNovo'); return True
        with patch('aeris.accessibility_ui.messagebox.askyesno',side_effect=changed): ui.confirm_clear()
        self.assertIn('Novo',ui.source.get('1.0','end'))
        self.assertEqual(ui.reader.lines,3)
        with patch('aeris.accessibility_ui.messagebox.askyesno',return_value=True): ui.confirm_clear()
        self.assertFalse(ui.dirty()); self.assertEqual(ui.reader.lines,0)

if __name__=='__main__': main(verbosity=2)
