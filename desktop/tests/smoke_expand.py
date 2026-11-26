import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_EXPAND

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Expand'); h.open_tool('Expand'); root.update()
            ui=h.expand_window; ui.code.set(';demo'); ui.replacement.insert('1.0','Olá'); ui.save()
            ui.input.insert('1.0',';demo!'); root.update(); ui.apply()
            assert ui.output.text=='Olá!' and ui.original()==';demo!' and 'Expand' in dict(h.quick_tools())
            assert str(ui.copy_button.cget('state'))=='disabled'
            h.permissions.set(COPY_EXPAND,True); assert str(ui.copy_button.cget('state'))=='normal'
            with patch('aeris.expand_ui.messagebox.askyesno',return_value=True): ui.copy()
            assert root.clipboard_get()=='Olá!'
            h.permissions.set(COPY_EXPAND,False); assert str(ui.copy_button.cget('state'))=='disabled'
            ui.input.insert('end',' mudou'); root.update(); assert ui.output is None
            with patch('aeris.expand_ui.messagebox.askyesno',return_value=True): ui.close()
            h.open_tool('Expand'); assert ';demo' in dict(h.expand_store.list())
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.expand_store is None and h.expand_window is None and not h.permissions.allowed(COPY_EXPAND)
        finally: root.destroy()
    print('Expand smoke: OK')
if __name__=='__main__': main()
