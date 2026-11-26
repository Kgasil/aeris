import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_TEXT

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Text'); h.open_tool('Text'); root.update()
            ui=h.text_window; ui.input.insert('1.0','Olá  mundo'); root.update(); ui.apply(); root.update()
            assert ui.output=='OLÁ  MUNDO' and ui.original()=='Olá  mundo'
            assert 'Text' in dict(h.quick_tools()); assert str(ui.copy_button.cget('state'))=='disabled'
            h.permissions.set(COPY_TEXT,True); assert str(ui.copy_button.cget('state'))=='normal'
            h.permissions.set(COPY_TEXT,False); assert str(ui.copy_button.cget('state'))=='disabled'
            ui.input.insert('end','!'); root.update(); assert ui.output is None
            ui.operation.set('Remover espaços excedentes'); ui.apply(); assert ui.output=='Olá mundo!'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.text_window is None and not h.permissions.allowed(COPY_TEXT)
        finally: root.destroy()
    print('Text UI smoke: OK')
if __name__=='__main__': main()
