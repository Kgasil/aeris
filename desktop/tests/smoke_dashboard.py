import time,tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DASHBOARD_READ,DATA_READ

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'demo.csv';raw=b'grupo,valor\nA,4\nA,2\nB,-2\n';p.write_bytes(raw);root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Dashboard');assert h.dashboard_window is None
            h.toggle_tool('Dashboard');h.open_tool('Dashboard');root.update();ui=h.dashboard_window;assert 'Dashboard' in dict(h.active_tools())
            with patch('aeris.data_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                h.permissions.set(DATA_READ,True);ui.choose();dialog.assert_not_called();h.permissions.set(DASHBOARD_READ,True);ui.choose();dialog.assert_called_once()
            with patch('aeris.data_ui.messagebox.askyesno',return_value=True):ui.run()
            deadline=time.monotonic()+4
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.summary is not None and ui.summary.overall==3
            ui.mode_box.set('Soma');ui.update_chart();root.update();assert ui.summary.overall==4 and len(ui.canvas.find_all())>0
            assert p.read_bytes()==raw
            h.permissions.set(DASHBOARD_READ,False);assert ui.dataset is None and ui.summary is None and not ui.canvas.find_all() and ui.path is None
            h.permissions.set(DASHBOARD_READ,True);h.toggle_tool('Dashboard');assert not h.alive(ui) and not h.permissions.allowed(DASHBOARD_READ)
            h.toggle_tool('Dashboard');h.open_tool('Dashboard');ui=h.dashboard_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.dashboard_window is None and not h.alive(ui)
        finally:root.destroy()
    print('Dashboard smoke: OK')
if __name__=='__main__':main()
