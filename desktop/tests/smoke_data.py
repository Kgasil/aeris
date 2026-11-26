import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DATA_READ
from aeris.data import Cancelled

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'example.csv';p.write_bytes(b'a,b\n1,2\n1,2\n');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Data');assert h.data_window is None
            h.toggle_tool('Data');h.open_tool('Data');root.update();ui=h.data_window
            assert 'Data' in dict(h.active_tools())
            with patch('aeris.data_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                ui.choose();dialog.assert_not_called();h.permissions.set(DATA_READ,True);ui.choose();dialog.assert_called_once()
            with patch('aeris.data_ui.messagebox.askyesno',return_value=False):ui.run();assert ui.job is None
            with patch('aeris.data_ui.messagebox.askyesno',return_value=True):ui.run()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.job is None and 'Registros: 2' in ui.report.get('1.0','end') and 'Duplicatas exatas adicionais: 1' in ui.report.get('1.0','end')
            assert p.read_bytes()==b'a,b\n1,2\n1,2\n'
            def slow(path,delimiter,decimal,cancelled):
                while not cancelled():time.sleep(.01)
                raise Cancelled()
            with patch('aeris.data_ui.profile_file',side_effect=slow),patch('aeris.data_ui.messagebox.askyesno',return_value=True):
                ui.run();assert ui.job is not None;h.permissions.set(DATA_READ,False)
                deadline=time.monotonic()+3
                while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
                assert ui.job is None and ui.path is None and 'Registros: 2' not in ui.report.get('1.0','end')
            h.permissions.set(DATA_READ,True);h.toggle_tool('Data');assert not h.alive(ui) and not h.permissions.allowed(DATA_READ)
            h.toggle_tool('Data');h.open_tool('Data');ui=h.data_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert not h.alive(ui) and h.data_window is None
        finally:root.destroy()
    print('Data smoke: OK')
if __name__=='__main__':main()
