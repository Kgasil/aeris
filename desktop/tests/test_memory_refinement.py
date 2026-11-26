"""Real Tk Memory regression, with synthetic records and injected protected-store test doubles."""
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.vault import Vault
from aeris.bookmarks import BookmarkStore
from aeris.permissions import OPEN_BOOKMARK
from tests.test_vault import TestBackend

class MemoryRefinement(TestCase):
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
    def test_vault_delete_rechecks_record_and_lock_clears_counter(self):
        with patch('aeris.vault.Vault',side_effect=lambda path:Vault(path,TestBackend())):
            ui=self.open('Vault')
        self.addCleanup(ui.vault.lock)
        ui.unlock(); ui.title.set('A'); ui.body.insert('1.0','Fictício')
        self.assertEqual(ui.keyboard_save(),'break')
        item=ui.vault.list()[0]
        self.assertEqual(ui.count.get(),'1 de 100 registros')
        def changed(*args,**kwargs):
            ui.vault.save('B','Novo texto',item.id)
            return True
        with patch('aeris.vault_ui.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.vault.list()[0].title,'B')
        ui.force_lock()
        self.assertFalse(ui.vault.unlocked)
        self.assertEqual(ui.count.get(),'')
        self.assertEqual(ui.keyboard_save(),'break')
    def test_capture_stale_delete_and_removed_record(self):
        ui=self.open('Capture')
        ui.title.set('A'); ui.body.insert('1.0','Fictício'); ui.keyboard_save()
        item=ui.store.list()[0]
        def changed(*args,**kwargs):
            ui.store.save('B','Novo texto',item.id); return True
        with patch('aeris.editor.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get(item.id).title,'B')
        ui.store.delete(item.id)
        self.assertTrue(ui.dirty())
        with patch('aeris.editor.messagebox.showwarning') as warning: ui.save()
        warning.assert_called_once()
    def test_timeline_filters_preserve_visible_selection_and_draft(self):
        ui=self.open('Timeline')
        item=ui.store.add('2026-11-25 09:00','A','Estudos')
        ui.store.add('2026-11-26 10:00','B','Trabalho')
        ui.render(); ui.tree.selection_set(str(item.id)); ui.load_selected()
        ui.title.set('Rascunho'); ui.category_filter.set('Estudos'); ui.render()
        self.assertEqual(ui.tree.selection(),(str(item.id),))
        ui.clear_filters()
        self.assertEqual(len(ui.tree.get_children()),2)
        self.assertEqual(ui.title.get(),'Rascunho')
        def changed(*args,**kwargs):
            ui.store.edit(item.id,'2026-11-25 09:00','C','Estudos',''); return True
        with patch('aeris.timeline_ui.messagebox.askyesno',side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get(item.id).title,'C')
    def test_ideas_rejects_stale_open_and_clears_filters(self):
        ui=self.open('Ideas')
        item=ui.store.add('A','Geral'); other=ui.store.add('B','Geral')
        ui.render(); ui.tree.selection_set(str(item.id)); ui.load_selected()
        ui.title.set('Rascunho'); ui.tree.selection_set(str(other.id))
        def changed(*args,**kwargs):
            ui.store.delete(other.id); return True
        with patch('aeris.ideas_ui.messagebox.askyesno',side_effect=changed): ui.load_selected()
        self.assertEqual(ui.title.get(),'Rascunho')
        ui.query.set('inexistente'); ui.render(); self.assertFalse(ui.tree.get_children())
        ui.clear_filters(); self.assertEqual(ui.tree.get_children(),(str(item.id),))
    def bookmarks(self):
        opened=[]
        with patch('aeris.bookmarks.BookmarkStore',side_effect=lambda path,permissions:BookmarkStore(path,permissions,TestBackend(),opened.append)):
            ui=self.open('Bookmarks')
        self.addCleanup(ui.store.lock)
        ui.unlock(); ui.title.set('A'); ui.url.set('https://example.com'); ui.save()
        self.h.permissions.set(OPEN_BOOKMARK,True)
        return ui,opened
    def test_bookmark_changed_during_confirmation_not_opened(self):
        ui,opened=self.bookmarks()
        def changed(*args,**kwargs):
            ui.store.save('B','Geral','https://example.org',ui.current); return True
        with patch('aeris.bookmarks_ui.messagebox.askyesno',side_effect=changed): ui.open_selected()
        self.assertEqual(opened,[])
        self.assertIn('alterado',ui.status.get())
    def test_bookmark_revoked_during_confirmation_not_opened(self):
        ui,opened=self.bookmarks()
        def changed(*args,**kwargs):
            self.h.permissions.set(OPEN_BOOKMARK,False); return True
        with patch('aeris.bookmarks_ui.messagebox.askyesno',side_effect=changed): ui.open_selected()
        self.assertEqual(opened,[])

if __name__=='__main__': main(verbosity=2)
