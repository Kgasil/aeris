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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Link'); assert h.link_window is None
            h.toggle_tool('Link'); assert 'Link' in dict(h.active_tools())
            h.open_tool('Link'); root.update(); ui=h.link_window
            ui.url.set('http://login.example.com@verification.example.org'); ui.analyze(); root.update()
            report=ui.report.get('1.0','end-1c'); assert 'verification.example.org' in report and 'Indicadores para revisar' in report
            ui.url.set('https://example.org'); assert 'verification.example.org' not in ui.report.get('1.0','end-1c')
            ui.analyze(); assert 'Nenhum indicador estrutural' in ui.report.get('1.0','end-1c')
            ui.clear(); assert not ui.url.get()
            h.toggle_tool('Link'); assert not h.alive(ui) and not h.enabled('Link')
            h.toggle_tool('Link'); h.open_tool('Link'); root.update(); ui=h.link_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert not h.alive(ui) and h.link_window is None
        finally: root.destroy()
    print('Link smoke: OK')
if __name__=='__main__': main()
