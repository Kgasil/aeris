import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Convert');assert h.convert_window is None
            h.toggle_tool('Convert');h.open_tool('Convert');root.update();ui=h.convert_window
            assert 'Convert' in dict(h.active_tools())
            ui.amount.set('1000');ui.run();assert ui.result.get()=='1 km'
            ui.swap();assert not ui.result.get();ui.run();assert ui.result.get()=='1000000 m'
            ui.category.set('Temperatura');ui.change_category();ui.amount.set('100');ui.run();assert ui.result.get()=='212 °F'
            ui.amount.set('-274');ui.run();assert ui.status.get() and not ui.result.get()
            ui.clear();assert not ui.amount.get() and not ui.status.get()
            ui.window.destroy();h.open_tool('Convert');ui=h.convert_window;assert not ui.amount.get()
            h.toggle_tool('Convert');assert not h.alive(ui)
            h.toggle_tool('Convert');h.open_tool('Convert');ui=h.convert_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.convert_window is None and not h.alive(ui)
        finally:root.destroy()
    print('Convert smoke: OK')
if __name__=='__main__':main()
