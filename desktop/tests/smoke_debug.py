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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Debug'); assert h.debug_window is None
            h.toggle_tool('Debug'); h.open_tool('Debug'); u=h.debug_window; root.update()
            assert 'Debug' in dict(h.active_tools()); assert not u.dirty()
            u.source.insert('1.0','def f()\n    pass'); root.update(); u.run(); root.update()
            assert not u.analysis.valid and 'Linha 1' in u.output.get('1.0','end'); u.goto(); assert u.source.index('insert').startswith('1.')
            u.source.insert('1.end',':'); root.update(); assert u.analysis is None and not u.status.get()
            u.run(); root.update(); assert u.analysis.valid
            with patch('aeris.debug_ui.messagebox.askyesno',return_value=False): u.close(); u.clear()
            assert h.alive(u) and u.dirty()
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Debug')
            assert h.enabled('Debug') and h.alive(u)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not h.alive(u) and u.analysis is None
            h.open_tool('Debug'); u=h.debug_window; assert not u.dirty()
            u.source.insert('1.0','x=1'); u.run()
            with patch('aeris.debug_ui.messagebox.askyesno',return_value=True): u.clear()
            assert not u.dirty() and u.analysis is None
            u.source.insert('1.0','x=2'); u.run()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Debug')
            assert not h.enabled('Debug') and not h.alive(u)
        finally: root.destroy()
    print('Debug smoke: OK')
if __name__=='__main__': main()
