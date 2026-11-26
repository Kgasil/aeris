import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import READ_CLIPBOARD, WRITE_CLIPBOARD

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root, Settings(Path(d)/'settings.json'))
            h.toggle_tool('Clipboard'); h.open_tool('Clipboard'); ui=h.clipboard_window; root.update()
            root.clipboard_clear(); root.clipboard_append('FICTICIO')
            ui.capture(); assert not h.clipboard_store.list()
            h.permissions.set(READ_CLIPBOARD,True)
            with patch('aeris.clipboard_ui.messagebox.askyesno',return_value=True): ui.capture()
            assert len(h.clipboard_store.list())==1
            ui.items.selection_set(0); ui.preview(); ui.pin(); assert h.clipboard_store.list()[0].pinned
            root.clipboard_clear(); root.clipboard_append('original'); ui.items.selection_set(0); ui.copy(); assert root.clipboard_get()=='original'
            h.permissions.set(WRITE_CLIPBOARD,True)
            with patch('aeris.clipboard_ui.messagebox.askyesno',return_value=True): ui.copy()
            assert root.clipboard_get()=='FICTICIO'
            h.permissions.set(READ_CLIPBOARD,False); h.permissions.set(WRITE_CLIPBOARD,False)
            assert str(ui.capture_button.cget('state'))=='disabled' and str(ui.copy_button.cget('state'))=='disabled'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.clipboard_store is None and root.clipboard_get()=='FICTICIO'
            assert 'FICTICIO' not in h.settings.path.read_text()
            h.open_tool('Clipboard'); h.permissions.set(READ_CLIPBOARD,True)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Clipboard')
            assert not h.settings.clipboard_enabled and not h.permissions.allowed(READ_CLIPBOARD)
            print('Clipboard UI smoke: OK')
        finally: root.destroy()
if __name__=='__main__': main()
