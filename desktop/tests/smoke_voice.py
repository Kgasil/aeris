import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import threading
import time
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import PLAY_VOICE

class FakeProcess:
    def __init__(self): self.returncode=None; self.killed=threading.Event(); self.payload=None
    def poll(self): return self.returncode
    def kill(self): self.returncode=1; self.killed.set()
    def communicate(self,payload=None,timeout=None):
        if payload: self.payload=payload
        self.killed.wait(3); self.returncode=1; return '',None

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Voice'); h.open_tool('Voice'); root.update()
            ui=h.voice_window; ui.text.insert('1.0','Olá!'); assert 'Voice' in dict(h.quick_tools())
            fake=FakeProcess()
            with patch('aeris.voice_ui.start_process',return_value=fake) as launch:
                ui.play(); launch.assert_not_called()
                h.permissions.set(PLAY_VOICE,True); ui.play(); launch.assert_called_once(); assert ui.process is fake
                h.permissions.set(PLAY_VOICE,False); assert fake.killed.is_set() and ui.process is None
                assert str(ui.play_button.cget('state'))=='disabled'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.voice_window is None
        finally: root.destroy()
    print('Voice UI smoke: OK')
if __name__=='__main__': main()
