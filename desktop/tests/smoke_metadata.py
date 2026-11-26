import time,tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import METADATA_READ
from tests.test_metadata import png_sample

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'sample.png'; p.write_bytes(png_sample()); root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Metadata'); assert h.metadata_window is None
            h.toggle_tool('Metadata'); h.open_tool('Metadata'); root.update(); ui=h.metadata_window
            with patch('aeris.metadata_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                ui.choose(); dialog.assert_not_called(); h.permissions.set(METADATA_READ,True); ui.choose(); dialog.assert_called_once()
            with patch('aeris.metadata_ui.messagebox.askyesno',return_value=True): ui.run()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline: root.update(); time.sleep(.02)
            assert ui.job is None and 'Texto PNG: Author: Example' in ui.report.get('1.0','end')
            h.permissions.set(METADATA_READ,False); assert ui.path is None and 'Example' not in ui.report.get('1.0','end')
            h.permissions.set(METADATA_READ,True); h.toggle_tool('Metadata'); assert not h.alive(ui) and not h.permissions.allowed(METADATA_READ)
            h.toggle_tool('Metadata'); h.open_tool('Metadata'); ui=h.metadata_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert not h.alive(ui) and h.metadata_window is None
        finally: root.destroy()
    print('Metadata smoke: OK')
if __name__=='__main__': main()
