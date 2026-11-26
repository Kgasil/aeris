import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COPY_TEXT


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Text'); h.open_tool('Text'); root.update(); ui=h.text_window
            assert ui.mode.get()=='Desligado'
            ui.input.insert('1.0','Ola, voce. A gente fomos.'); root.update()
            ui.mode.set('Sugerir'); ui.window.after(550,ui.window.quit); ui.window.mainloop()
            assert ui.output=='Olá, você. A gente foi.' and ui.original()=='Ola, voce. A gente fomos.'
            assert str(ui.copy_button.cget('state'))=='disabled'
            ui.accept(); root.update(); assert ui.original()=='Olá, você. A gente foi.'
            ui.undo_review(); root.update(); assert ui.original()=='Ola, voce. A gente fomos.' and ui.mode.get()=='Desligado'
            ui.mode.set('Automático'); ui.window.after(550,ui.window.quit); ui.window.mainloop()
            assert ui.original()=='Olá, você. A gente fomos.' and ui.output=='Olá, você. A gente foi.'
            ui.undo_review(); root.update(); assert ui.original()=='Ola, voce. A gente fomos.'
            ui.mode.set('Sugerir'); ui.input.insert('end','!'); root.update(); assert ui.pending is not None
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.text_window is None and ui.pending is None and not h.permissions.allowed(COPY_TEXT)
        finally: root.destroy()
    print('Intelligent Text UI smoke: OK')
if __name__=='__main__': main()
