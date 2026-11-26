import hashlib,time,tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import VERIFY_READ

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'test.bin'; p.write_bytes(b'abc'); root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Verify'); assert h.verify_window is None
            h.toggle_tool('Verify'); h.open_tool('Verify'); root.update(); ui=h.verify_window
            with patch('aeris.verify_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                ui.choose(); dialog.assert_not_called(); h.permissions.set(VERIFY_READ,True); ui.choose(); dialog.assert_called_once()
            ui.expected.set(hashlib.sha256(b'abc').hexdigest())
            with patch('aeris.verify_ui.messagebox.askyesno',return_value=True): ui.run()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline: root.update(); time.sleep(.02)
            assert ui.job is None and 'Hashes correspondentes' in ui.report.get('1.0','end')
            ui.expected.set('0'*64); assert 'Hashes correspondentes' not in ui.report.get('1.0','end')
            h.permissions.set(VERIFY_READ,False); assert ui.path is None and not ui.expected.get()
            h.permissions.set(VERIFY_READ,True); h.toggle_tool('Verify'); assert not h.alive(ui) and not h.permissions.allowed(VERIFY_READ)
            h.toggle_tool('Verify'); h.open_tool('Verify'); ui=h.verify_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert not h.alive(ui) and h.verify_window is None
        finally: root.destroy()
    print('Verify smoke: OK')
if __name__=='__main__': main()
