import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_TRANSLATION

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Translate'); h.open_tool('Translate'); root.update()
            ui=h.translate_window; ui.input.insert('1.0','Bom dia!'); ui.translate(); assert ui.output=='Good morning!'
            assert str(ui.copy_button.cget('state'))=='disabled'
            h.permissions.set(COPY_TRANSLATION,True); assert str(ui.copy_button.cget('state'))=='normal'
            h.permissions.set(COPY_TRANSLATION,False); assert str(ui.copy_button.cget('state'))=='disabled'
            assert 'Translate' in dict(h.quick_tools())
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.translate_window is None
        finally: root.destroy()
    print('Translate UI smoke: OK')
if __name__=='__main__': main()
