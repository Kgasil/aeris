import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import LENS_READ
from aeris.lens import LensResult, Cancelled

def wait(root,ui):
    deadline=time.monotonic()+5
    while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
    assert ui.job is None

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'image.png';p.write_bytes(b'fictitious');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Lens');assert h.lens_window is None
            h.toggle_tool('Lens');h.open_tool('Lens');ui=h.lens_window;assert 'Lens' in dict(h.active_tools())
            with patch('aeris.lens_ui.filedialog.askopenfilename',return_value=str(p)) as dialog,patch('aeris.lens_ui.messagebox.askyesno',return_value=True),patch('aeris.lens_ui.recognize',return_value=LensResult('Aeris',False,'PNG',100,100)) as ocr:
                ui.choose();dialog.assert_not_called();h.permissions.set(LENS_READ,True);ui.choose();ui.run();wait(root,ui)
                assert 'Aeris' in ui.report.get('1.0','end');ocr.assert_called_once()
            def slow(*args,cancelled):
                while not cancelled():time.sleep(.01)
                raise Cancelled()
            with patch('aeris.lens_ui.recognize',side_effect=slow),patch('aeris.lens_ui.messagebox.askyesno',return_value=True):
                ui.run();h.permissions.set(LENS_READ,False);wait(root,ui)
            assert ui.path is None and 'Aeris' not in ui.report.get('1.0','end')
            h.permissions.set(LENS_READ,True);h.toggle_tool('Lens');assert not h.alive(ui) and not h.permissions.allowed(LENS_READ)
            h.toggle_tool('Lens');h.open_tool('Lens')
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.lens_window is None and p.read_bytes()==b'fictitious'
        finally:root.destroy()
    print('Lens smoke: OK')
if __name__=='__main__':main()
