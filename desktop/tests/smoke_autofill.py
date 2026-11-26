import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.autofill import ProfileStore
from aeris.permissions import COPY_AUTOFILL
from tests.test_vault import TestBackend

def main():
    with TemporaryDirectory() as folder:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(folder)/'settings.json')); h.toggle_tool('Autofill')
            with patch('aeris.autofill.ProfileStore',side_effect=lambda path,permissions:ProfileStore(path,permissions,TestBackend())): h.open_tool('Autofill')
            ui=h.autofill_window; ui.unlock(); root.update(); ui.title.set('Demo'); ui.vars['name'].set('Alex Example'); ui.save(); ui.requested['name'].set(True); ui.show_preview()
            assert ui.preview_rows==(('name','Alex Example'),)
            ui.preview_items.selection_set(0); ui.permissions_changed(); assert str(ui.copy_button.cget('state'))=='disabled'
            h.permissions.set(COPY_AUTOFILL,True); assert str(ui.copy_button.cget('state'))=='normal'
            with patch('aeris.autofill_ui.messagebox.askyesno',return_value=True): ui.copy()
            assert root.clipboard_get()=='Alex Example'
            h.permissions.revoke_all(); assert str(ui.copy_button.cget('state'))=='disabled'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert not ui.store.unlocked and not ui.preview_rows
            ui.unlock(); assert len(ui.store.list())==1
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Autofill')
            assert not ui.store.unlocked and h.autofill_window is None
        finally: root.destroy()
    print('Autofill smoke: OK (simulated storage)')
if __name__=='__main__': main()
