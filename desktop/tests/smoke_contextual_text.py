import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from threading import Event
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import TEXT_AI
from aeris.intelligent_text import Review, Edit


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Text'); h.open_tool('Text'); root.update(); ui=h.text_window
            def wait():
                root.after(350,root.quit); root.mainloop(); assert not ui.ai_busy
            def fake(text,lang,model): return Review('Olá, mundo!',(Edit(2,3,'a','á','IA'),Edit(3,3,'',', mundo!','IA')))
            ui.input.insert('1.0','Ola'); root.update()
            assert str(ui.ai_button.cget('state'))=='disabled'
            with patch('aeris.text_ui.simpledialog.askstring',return_value='Ola'): ui.edit_dictionary()
            ui.review_now(); assert ui.output=='Ola'
            h.permissions.set(TEXT_AI,True)
            with patch('aeris.text_ui.simpledialog.askstring',return_value='local:1b'),patch('aeris.text_ui.messagebox.askyesno',return_value=False),patch('aeris.text_ui.contextual_review') as call:
                ui.ask_ai(); assert not call.called
            with patch('aeris.text_ui.simpledialog.askstring',return_value='local:1b'),patch('aeris.text_ui.messagebox.askyesno',return_value=True),patch('aeris.text_ui.contextual_review',side_effect=fake):
                ui.ask_ai(); wait()
            assert ui.ai_preview and ui.original()=='Ola' and ui.output=='Olá, mundo!' and ui.result.tag_ranges('revision')
            ui.accept(); root.update(); assert ui.original()=='Olá, mundo!'
            ui.undo_review(); root.update(); assert ui.original()=='Ola'
            with patch('aeris.text_ui.contextual_review',side_effect=fake):
                ui.start_ai(ui.original(),ui.language.get(),'local:1b'); wait()
            h.permissions.set(TEXT_AI,False); assert not ui.ai_preview and ui.output is None
            h.permissions.set(TEXT_AI,True); assert ui.output is None
            gate=Event()
            def delayed(*args): gate.wait(2); return fake(*args)
            with patch('aeris.text_ui.contextual_review',side_effect=delayed):
                ui.start_ai(ui.original(),ui.language.get(),'local:1b'); ui.input.insert('end',' novo'); root.update(); gate.set(); wait()
            assert ui.original()=='Ola novo' and ui.output is None
            with patch('aeris.text_ui.contextual_review',side_effect=fake):
                ui.start_ai(ui.original(),ui.language.get(),'local:1b'); h.permissions.set(TEXT_AI,False); h.permissions.set(TEXT_AI,True); wait()
            assert ui.output is None and ui.ai_timer is None
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not ui.dictionary and not h.permissions.allowed(TEXT_AI)
        finally: root.destroy()
    print('Contextual Text smoke: OK')
if __name__=='__main__': main()
