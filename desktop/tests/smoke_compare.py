import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import COMPARE_READ
from aeris.compare import Cancelled

def wait(root,ui):
    deadline=time.monotonic()+4
    while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
    assert ui.job is None

def main():
    with TemporaryDirectory() as d:
        a=Path(d)/'a.txt';b=Path(d)/'b.txt';a.write_bytes(b'a\nb');b.write_bytes(b'a\nB');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Compare');assert h.compare_window is None
            h.toggle_tool('Compare');h.open_tool('Compare');ui=h.compare_window;assert 'Compare' in dict(h.active_tools())
            ui.inputs[0].insert('1.0','a\nb');ui.inputs[1].insert('1.0','a\nB');root.update();ui.run();wait(root,ui)
            assert 'Mantidas: 1' in ui.status.get() and '[sem quebra final]' in ui.report.get('1.0','end')
            ui.inputs[0].insert('end','x');root.update();assert not ui.report.get('1.0','end-1c')
            ui.mode.set('Arquivos');root.update()
            with patch('aeris.compare_ui.filedialog.askopenfilename',side_effect=[str(a),str(b)]) as dialog,patch('aeris.compare_ui.messagebox.askyesno',return_value=True):
                ui.choose(0);dialog.assert_not_called();h.permissions.set(COMPARE_READ,True);ui.choose(0);ui.choose(1);ui.run();wait(root,ui)
            assert 'Mantidas: 1' in ui.status.get() and a.read_bytes()==b'a\nb'
            def slow(*args,cancelled):
                while not cancelled():time.sleep(.01)
                raise Cancelled()
            with patch('aeris.compare_ui.compare_files',side_effect=slow),patch('aeris.compare_ui.messagebox.askyesno',return_value=True):
                ui.run();assert ui.job;h.permissions.set(COMPARE_READ,False);wait(root,ui)
            assert ui.paths==[None,None] and not ui.report.get('1.0','end-1c')
            h.permissions.set(COMPARE_READ,True);h.toggle_tool('Compare');assert not h.alive(ui) and not h.permissions.allowed(COMPARE_READ)
            h.toggle_tool('Compare');h.open_tool('Compare');ui=h.compare_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.compare_window is None and b.read_bytes()==b'a\nB'
        finally:root.destroy()
    print('Compare smoke: OK')
if __name__=='__main__':main()
