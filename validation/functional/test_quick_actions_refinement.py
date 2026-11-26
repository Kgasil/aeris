"""Quick Actions regression with real Tk, synthetic text and simulated protected storage."""
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.autofill import ProfileStore
from aeris.permissions import COPY_AUTOFILL,READ_CLIPBOARD,WRITE_CLIPBOARD,COPY_SNIPPETS,COPY_EXPAND
from tests.test_vault import TestBackend

class QuickActionsRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/'settings.json'))
        self.root.update()

    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')

    def test_autofill_explicit_fields_and_changed_selection(self):
        with patch('aeris.autofill.ProfileStore',side_effect=lambda p,perms:ProfileStore(p,perms,TestBackend())):
            ui=self.open('Autofill')
        self.addCleanup(ui.store.lock)
        ui.unlock(); ui.title.set('Demo'); ui.vars['name'].set('Alex Example'); ui.save()
        ui.show_preview(); self.assertEqual(ui.preview_rows,())
        ui.requested['name'].set(True); ui.show_preview()
        self.assertEqual(ui.preview_rows,(('name','Alex Example'),))
        ui.preview_items.selection_set(0); self.h.permissions.set(COPY_AUTOFILL,True)
        def changed(*args,**kwargs):
            ui.requested['name'].set(False)
            return True
        with patch('aeris.autofill_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertEqual(ui.preview_rows,())

    def test_clipboard_pinned_filter_and_selection(self):
        ui=self.open('Clipboard'); self.h.permissions.set(READ_CLIPBOARD,True)
        a=ui.store.capture(lambda:'A'); b=ui.store.capture(lambda:'B'); ui.refresh()
        index=next(i for i,c in enumerate(ui.visible) if c.id==a.id)
        ui.items.selection_set(index); ui.pin()
        self.assertEqual(ui.selected().id,a.id)
        ui.pinned_only.set(True); ui.refresh()
        self.assertEqual(tuple(c.id for c in ui.visible),(a.id,))
        self.assertEqual(ui.selected().id,a.id)
        ui.pinned_only.set(False); ui.refresh()
        self.assertEqual(len(ui.visible),2)

    def test_clipboard_removed_during_confirmation_not_written(self):
        ui=self.open('Clipboard')
        self.h.permissions.set(READ_CLIPBOARD,True); self.h.permissions.set(WRITE_CLIPBOARD,True)
        a=ui.store.capture(lambda:'Fictício'); ui.refresh(); ui.items.selection_set(0)
        def changed(*args,**kwargs): ui.store.delete(a.id); return True
        with patch('aeris.clipboard_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()

    def test_snippets_changed_during_confirmation_not_written(self):
        ui=self.open('Snippets'); self.h.permissions.set(COPY_SNIPPETS,True)
        item=ui.store.save('A','Geral','Texto original'); ui.fill(item); ui.refresh()
        def changed(*args,**kwargs):
            ui.store.save('A','Geral','Texto novo',item.id); return True
        with patch('aeris.editor.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIn('alterado',ui.status.get())

    def test_expand_changed_rules_during_confirmation_not_written(self):
        ui=self.open('Expand'); self.h.permissions.set(COPY_EXPAND,True)
        ui.input.insert('1.0',';att'); self.root.update(); ui.apply()
        self.assertIsNotNone(ui.output)
        def changed(*args,**kwargs): ui.store.save(';att','Outro texto'); return True
        with patch('aeris.expand_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIsNone(ui.output)

    def test_convert_inverse_and_stale_result(self):
        ui=self.open('Convert'); ui.amount.set('1000'); ui.run()
        self.assertEqual(ui.result.get(),'1 km')
        ui.reverse_result()
        self.assertEqual((ui.source.get(),ui.target.get(),ui.result.get()),('km','m','1000 m'))
        ui.amount.set('2')
        self.assertIsNone(ui.last_result)
        self.assertEqual(str(ui.reverse_button.cget('state')),'disabled')
        ui.run(); ui.category.set('Temperatura')
        self.assertIsNone(ui.last_result)

if __name__=='__main__': main(verbosity=2)
