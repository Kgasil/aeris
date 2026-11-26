"""Explicit suggestion, opt-in speech, stop, revocation and stale input."""
import json
import threading
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COMPANION_CHAT, COMPANION_MIC, COMPANION_SPEAK, COPILOT_RUN
from tests.smoke_eco import until

class FakeSpeech:
    def __init__(self, text=None):
        self.text=text; self.returncode=None; self.killed=threading.Event(); self.started=threading.Event(); self.payload=None
    def kill(self): self.killed.set()
    def communicate(self,payload=None,timeout=None):
        self.payload=json.loads(payload); self.started.set()
        if self.text is not None:
            self.returncode=0; return json.dumps(self.text),None
        assert self.killed.wait(3)
        self.returncode=1; return '',None

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk(); gate=threading.Event()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Copilot'); h.toggle_tool('Reminder'); h.open_tool('Copilot'); cop=h.copilot_window; cop.open_companion(); ui=cop.companion
            h.permissions.set(COMPANION_CHAT,True); ui.model.set('local')
            assert not ui.auto_speak.get() and str(ui.suggest_button['state'])=='disabled'
            h.permissions.set(COPILOT_RUN,True); h.permissions.set(COMPANION_MIC,True)
            original='Daqui a vinte minutos me avise de revisar'; command='Lembre-me de revisar em 20 minutos'
            with patch('aeris.companion_ui.speech_process',return_value=FakeSpeech(original)):
                ui.speech('listen'); until(root,lambda:not ui.busy)
            assert ui.input.get('1.0','end-1c')==original and not cop.session.pending
            with patch('aeris.companion_ui.suggest_command',return_value=command) as suggest:
                ui.suggest(); until(root,lambda:not ui.busy)
                suggest.assert_called_once_with('local',original)
            assert ui.candidate==(original,command) and not cop.session.pending and h.reminder_store is None
            ui.accept_candidate(); assert ui.input.get('1.0','end-1c')==command and not cop.session.pending
            ui.prepare_action(); assert cop.session.pending and h.reminder_store is None
            cop.confirm(); assert len(h.reminder_store.list())==1
            def input_text(text): ui.input.delete('1.0','end'); ui.input.insert('1.0',text)
            def slow(*args): assert gate.wait(3); return command
            input_text(original)
            with patch('aeris.companion_ui.suggest_command',side_effect=slow):
                ui.suggest(); input_text('Outra solicitação'); gate.set(); until(root,lambda:not ui.busy)
            assert not ui.candidate and not cop.session.pending
            input_text(original); gate.clear()
            with patch('aeris.companion_ui.suggest_command',side_effect=slow):
                ui.suggest(); h.permissions.set(COPILOT_RUN,False); h.permissions.set(COPILOT_RUN,True); gate.set(); until(root,lambda:not ui.busy)
            assert not ui.candidate and len(h.reminder_store.list())==1
            h.permissions.set(COMPANION_SPEAK,True)
            input_text('Olá')
            with patch('aeris.companion_ui.chat',return_value='Oi'),patch('aeris.companion_ui.speech_process') as launch:
                ui.send(); until(root,lambda:not ui.busy); launch.assert_not_called()
            assert ui.history[-1][1]=='Oi'
            ui.auto_speak.set(True); input_text('Outra mensagem'); fake=FakeSpeech()
            with patch('aeris.companion_ui.chat',return_value='Nova resposta'),patch('aeris.companion_ui.speech_process',return_value=fake):
                ui.send(); until(root,fake.started.is_set); assert fake.payload=={'action':'speak','text':'Nova resposta'}
                ui.stop(); assert fake.killed.is_set(); until(root,lambda:not ui.busy)
            assert ui.history[-1][1]=='Nova resposta' and ui.timer is None
            h.permissions.set(COMPANION_SPEAK,False); assert not ui.auto_speak.get()
            h.permissions.set(COMPANION_CHAT,False); assert not ui.history
        finally: gate.set(); root.destroy()
    print('Companion flow smoke: OK')
if __name__=='__main__': main()
