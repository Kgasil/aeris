import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import ORGANIZER_SCAN
from aeris.organizer import Cancelled

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'samples';p.mkdir();(p/'example.csv').write_bytes(b'a,b');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Organizer');assert h.organizer_window is None
            h.toggle_tool('Organizer');h.open_tool('Organizer');root.update();ui=h.organizer_window
            assert 'Organizer' in dict(h.active_tools())
            with patch('aeris.organizer_ui.filedialog.askdirectory',return_value=str(p)) as dialog:
                ui.choose();dialog.assert_not_called();h.permissions.set(ORGANIZER_SCAN,True);ui.choose();dialog.assert_called_once()
            with patch('aeris.organizer_ui.messagebox.askyesno',return_value=False):ui.run();assert ui.job is None
            with patch('aeris.organizer_ui.messagebox.askyesno',return_value=True):ui.run()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.job is None and 'example.csv' in ui.report.get('1.0','end') and 'Planilhas e dados' in ui.report.get('1.0','end')
            assert (p/'example.csv').read_bytes()==b'a,b'
            def slow(path,cancelled):
                while not cancelled():time.sleep(.01)
                raise Cancelled()
            with patch('aeris.organizer_ui.scan_folder',side_effect=slow),patch('aeris.organizer_ui.messagebox.askyesno',return_value=True):
                ui.run();assert ui.job is not None;h.permissions.set(ORGANIZER_SCAN,False)
                deadline=time.monotonic()+3
                while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
                assert ui.job is None and ui.path is None and 'example.csv' not in ui.report.get('1.0','end')
            h.permissions.set(ORGANIZER_SCAN,True);h.toggle_tool('Organizer');assert not h.alive(ui) and not h.permissions.allowed(ORGANIZER_SCAN)
            h.toggle_tool('Organizer');h.open_tool('Organizer');ui=h.organizer_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert not h.alive(ui) and h.organizer_window is None
        finally:root.destroy()
    print('Organizer smoke: OK')
if __name__=='__main__':main()
