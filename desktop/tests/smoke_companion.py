import tkinter as tk
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COMPANION_CHAT, COPILOT_RUN, COMPANION_MIC
from aeris.copilot import EXAMPLES

def wait(root,ui):
    deadline=time.monotonic()+3
    while ui.busy and time.monotonic()<deadline: root.update(); time.sleep(.02)
    assert not ui.busy

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Copilot'); h.toggle_tool('Reminder'); h.open_tool('Copilot'); cop=h.copilot_window; cop.open_companion(); ui=cop.companion; root.update()
            assert str(ui.send_button['state'])=='disabled'
            assert ui.timer is None and not ui.busy
            h.permissions.set(COMPANION_CHAT,True); ui.model.set('local'); ui.input.insert('1.0','Oi')
            with patch('aeris.companion_ui.chat',return_value=EXAMPLES[0]):
                ui.send(); assert ui.timer is not None; wait(root,ui)
            assert ui.timer is None
            assert ui.history[-1][1]==EXAMPLES[0] and h.reminder_store is None and not cop.session.pending
            h.permissions.set(COPILOT_RUN,True); ui.input.insert('1.0',EXAMPLES[0]); ui.prepare_action(); assert cop.session.pending and h.reminder_store is None
            cop.confirm(); assert len(h.reminder_store.list())==1
            h.permissions.set(COMPANION_CHAT,False); assert not ui.history
            h.permissions.set(COMPANION_MIC,True); h.toggle_tool('Copilot'); assert not h.permissions.allowed(COMPANION_MIC) and not h.alive(ui)
        finally:root.destroy()
    print('Companion smoke: OK')
if __name__=='__main__':main()
