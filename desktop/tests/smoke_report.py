import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import REPORT_READ,REPORT_COPY,DATA_READ

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'demo.csv';raw=b'grupo,valor\nA,4\nA,2\nB,-2\n';p.write_bytes(raw);root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Report');assert h.report_window is None
            h.toggle_tool('Report');h.open_tool('Report');root.update();ui=h.report_window;assert 'Report' in dict(h.active_tools())
            with patch('aeris.data_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                h.permissions.set(DATA_READ,True);ui.choose();dialog.assert_not_called();h.permissions.set(REPORT_READ,True);ui.choose();dialog.assert_called_once()
            with patch('aeris.data_ui.messagebox.askyesno',return_value=True):ui.run()
            deadline=time.monotonic()+4
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.output and 'Registros: 3' in ui.output
            ui.group_box.current(1);ui.mode_box.set('Soma');ui.generate();assert 'Total global: 4' in ui.output
            with patch('aeris.report_ui.messagebox.askyesno',return_value=True) as confirm:
                ui.copy();confirm.assert_not_called();h.permissions.set(REPORT_COPY,True);ui.copy();confirm.assert_called_once();assert root.clipboard_get()==ui.output
            assert p.read_bytes()==raw
            h.permissions.set(REPORT_READ,False);assert ui.dataset is None and ui.output is None and ui.path is None
            h.permissions.set(REPORT_READ,True);h.toggle_tool('Report');assert not h.alive(ui) and not h.permissions.allowed(REPORT_COPY) and not h.permissions.allowed(REPORT_READ)
            h.toggle_tool('Report');h.open_tool('Report');ui=h.report_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.report_window is None and not h.alive(ui)
        finally:root.destroy()
    print('Report smoke: OK')
if __name__=='__main__':main()
