import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_EMAIL

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Email'); h.open_tool('Email'); root.update()
            ui=h.email_window; ui.details.insert('1.0','Informação fictícia.'); root.update(); ui.generate()
            assert ui.draft.subject=='Solicitação'; assert 'Email' in dict(h.quick_tools())
            assert str(ui.copy_body.cget('state'))=='disabled'
            h.permissions.set(COPY_EMAIL,True); assert str(ui.copy_body.cget('state'))=='normal'
            with patch('aeris.email_ui.messagebox.askyesno',return_value=True): ui.copy('body')
            assert root.clipboard_get()==ui.draft.body
            h.permissions.set(COPY_EMAIL,False); assert str(ui.copy_subject.cget('state'))=='disabled'
            ui.subject.set('Novo assunto'); assert ui.draft is None
            ui.generate(); assert ui.draft.subject=='Novo assunto'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.email_window is None and not h.permissions.allowed(COPY_EMAIL)
        finally: root.destroy()
    print('Email UI smoke: OK')
if __name__=='__main__': main()
