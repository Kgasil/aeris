import time
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            h.open_tool('Health'); assert h.health_window is None
            h.toggle_tool('Health'); h.open_tool('Health'); root.update(); ui=h.health_window
            assert 'Health' in dict(h.active_tools()) and ui.pending is None
            ui.run(); assert ui.pending is not None; ui.clear(); assert ui.pending is None and ui.report.get()=='Sem amostra.'
            ui.run(); deadline=time.monotonic()+4
            while ui.pending is not None and time.monotonic()<deadline:
                root.update(); time.sleep(.02)
            assert ui.pending is None and 'CPU do processo:' in ui.report.get() and 'Health' in ui.report.get()
            print(ui.report.get())
            ui.run(); h.toggle_tool('Health'); assert ui.pending is None and not h.alive(ui)
            h.toggle_tool('Health'); h.open_tool('Health'); ui=h.health_window; ui.run()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert ui.pending is None and h.health_window is None
        finally: root.destroy()
    print('Health smoke: OK')

if __name__=='__main__': main()
