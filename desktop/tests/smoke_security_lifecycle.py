import tkinter as tk
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COMPANION_CHAT, COMPANION_MIC, TEXT_AI
from aeris.local_worker import worker_for
from tests.smoke_eco import until


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk(); release=threading.Event(); entered=threading.Event()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for name in ('Text','Copilot'): h.toggle_tool(name); h.open_tool(name)
            h.copilot_window.open_companion(); ui=h.copilot_window.companion
            for cap in (COMPANION_CHAT,COMPANION_MIC,TEXT_AI): h.permissions.set(cap,True)
            ui.model.set('local'); ui.input.insert('1.0','Mensagem')
            def delayed(*a): entered.set(); release.wait(4); return 'Resposta antiga'
            with patch('aeris.companion_ui.chat',side_effect=delayed):
                ui.send(); assert entered.wait(2); ui.window.destroy(); root.update()
                h.copilot_window.open_companion(); fresh=h.copilot_window.companion; fresh.model.set('local'); fresh.input.insert('1.0','Nova')
                fresh.send(); assert not fresh.busy and fresh.input.get('1.0','end-1c')=='Nova'
                text=h.text_window; text.input.insert('1.0','Ola'); root.update(); text.start_ai('Ola',text.language.get(),'local'); assert not text.ai_busy
                fresh.input.delete('1.0','end')
                with patch('aeris.companion_ui.speech_process') as speech:
                    fresh.speech('listen'); speech.assert_not_called()
                release.set(); until(root,lambda:not worker_for(h).busy)
            assert not fresh.history and not text.ai_preview
            with patch('aeris.local_worker.threading.Thread.start',side_effect=RuntimeError):
                fresh.input.insert('1.0','Nova'); fresh.send(); assert not fresh.busy and fresh.input.get('1.0','end-1c')=='Nova'
                text.start_ai('Ola',text.language.get(),'local'); assert not text.ai_busy and text.ai_timer is None
            assert not worker_for(h).busy
            with patch('aeris.hub.messagebox.askyesno',return_value=False) as confirm:
                h.close(); confirm.assert_called_once(); assert root.winfo_exists()
            text.window.destroy(); root.update()
            with patch('aeris.hub.messagebox.askyesno',return_value=False) as confirm:
                h.close(); confirm.assert_called_once(); assert root.winfo_exists()
        finally: release.set(); root.destroy()
    print('Security lifecycle smoke: OK')
if __name__=='__main__': main()
