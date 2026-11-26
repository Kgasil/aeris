"""Idle polling, cancellation, and destruction of the AI companion."""
import threading
import time
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COMPANION_CHAT


def until(root, predicate):
    end = time.monotonic() + 3
    while not predicate() and time.monotonic() < end:
        root.update(); time.sleep(.01)
    assert predicate()


def main():
    with TemporaryDirectory() as d:
        root = tk.Tk()
        release = threading.Event()
        try:
            hub = Hub(root, Settings(Path(d)/'settings.json'))
            hub.toggle_tool('Copilot'); hub.open_tool('Copilot')
            cop = hub.copilot_window; cop.open_companion(); ui = cop.companion
            root.update(); assert ui.timer is None
            hub.permissions.set(COMPANION_CHAT, True); ui.model.set('local')
            def slow(*args):
                assert release.wait(3)
                return 'Resposta atrasada'
            with patch('aeris.companion_ui.chat', side_effect=slow):
                ui.input.insert('1.0', 'Oi'); ui.send()
                assert ui.busy and ui.timer is not None
                old = ui.timer; ui.schedule_poll(); assert ui.timer == old
                hub.permissions.set(COMPANION_CHAT, False)
                assert ui.busy and ui.timer is not None
                release.set(); until(root, lambda: not ui.busy)
                assert ui.timer is None and not ui.history
            hub.permissions.set(COMPANION_CHAT, True); release.clear()
            with patch('aeris.companion_ui.chat', side_effect=slow):
                ui.input.insert('1.0', 'Oi de novo'); ui.send(); assert ui.timer is not None
                pending = ui.timer; ui.window.destroy(); root.update()
                assert ui.closed and ui.timer is None
                assert pending not in root.tk.splitlist(root.tk.call('after','info'))
                release.set(); until(root, lambda: not ui.results.empty())
        finally:
            release.set(); root.destroy()
    print('Eco smoke: OK')

if __name__ == '__main__': main()
