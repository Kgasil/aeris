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
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Calculator');assert h.calculator_window is None
            h.toggle_tool('Calculator');h.open_tool('Calculator');root.update();ui=h.calculator_window
            assert 'Calculator' in dict(h.active_tools())
            ui.inputs[0].set('0,1+0,2');ui.run();assert ui.result.get()=='0,3'
            ui.inputs[0].set('1/0');assert not ui.result.get();ui.run();assert ui.status.get() and not ui.result.get()
            ui.operation.set('Markup (%)');ui.change_operation();ui.inputs[0].set('15000');ui.inputs[1].set('10000');ui.run();assert ui.result.get()=='50%'
            ui.clear();assert not ui.result.get() and all(not v.get() for v in ui.inputs)
            ui.window.destroy();h.open_tool('Calculator');ui=h.calculator_window;assert not ui.result.get() and not ui.inputs[0].get()
            h.toggle_tool('Calculator');assert not h.alive(ui)
            h.toggle_tool('Calculator');h.open_tool('Calculator');ui=h.calculator_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.calculator_window is None and not h.alive(ui)
        finally:root.destroy()
    print('Calculator smoke: OK')
if __name__=='__main__':main()
