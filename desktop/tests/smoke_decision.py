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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Decision'); assert h.decision_window is None
            h.toggle_tool('Decision'); h.open_tool('Decision'); root.update(); ui=h.decision_window
            assert 'Decision' in dict(h.active_tools()) and not ui.dirty()
            ui.example(); ui.calculate(); root.update(); assert ui.result[0].name=='Alternativa C' and len(ui.table.get_children())==3
            ui.weights[0].set('0'); assert not ui.result and not ui.table.get_children()
            ui.calculate(); assert ui.result[0].name=='Alternativa B'
            ui.nc.set(4); ui.resize(); assert ui.criteria[0].get()=='Custo-benefício' and ui.criteria[3].get()==''
            ui.calculate(); assert not ui.result
            ui.nc.set(2)
            with patch('aeris.decision_ui.messagebox.askyesno',return_value=False): ui.resize(); ui.close()
            assert len(ui.criteria)==4 and ui.nc.get()==4 and h.alive(ui)
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Decision')
            assert h.enabled('Decision') and h.alive(ui)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.decision_window is None and not h.alive(ui) and not ui.result and not ui.fields
            h.open_tool('Decision'); ui=h.decision_window; assert not ui.dirty(); h.toggle_tool('Decision'); assert not h.alive(ui)
        finally: root.destroy()
    print('Decision smoke: OK')
if __name__=='__main__': main()
