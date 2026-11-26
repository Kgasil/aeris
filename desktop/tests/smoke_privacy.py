import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import SEARCH_CAPTURE

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            h.query.set('Privacy'); h.launch.invoke(); root.update(); ui=h.privacy_window
            assert h.alive(ui)
            h.permissions.set(SEARCH_CAPTURE,True)
            assert 'Autorizado: Search → Capture' in ui.grants.get(0,'end')
            ui.revoke(); assert not h.permissions.allowed(SEARCH_CAPTURE)
            ui.original.insert('1.0','pessoa@example.com'); root.update(); ui.mask(); root.update()
            assert ui.preview.get('1.0','end-1c')=='[E-mail ocultado]'
            ui.original.insert('end',' outro'); root.update(); assert not ui.preview.get('1.0','end-1c')
            ui.mask(); root.update()
            with patch('aeris.hub.messagebox.askyesno',return_value=False): ui.clear()
            assert ui.original.get('1.0','end-1c')
            with patch('aeris.privacy_ui.messagebox.askyesno',return_value=True), patch.object(h,'lock_protected') as lock: ui.lock(); lock.assert_called_once()
            h.permissions.set(SEARCH_CAPTURE,True); root.clipboard_clear(); root.clipboard_append('teste')
            with patch('aeris.hub.messagebox.askyesno',return_value=True): ui.clear()
            assert not ui.original.get('1.0','end-1c') and not ui.preview.get('1.0','end-1c')
            assert not h.permissions.allowed(SEARCH_CAPTURE) and not h.query.get() and root.clipboard_get()=='teste'
        finally: root.destroy()
    print('Privacy smoke: OK')
if __name__=='__main__': main()
