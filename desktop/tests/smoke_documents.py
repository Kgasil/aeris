import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DOCUMENTS_READ

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'sample.txt';p.write_text('Example document',encoding='utf-8');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Documents');assert h.documents_window is None
            h.toggle_tool('Documents');h.open_tool('Documents');root.update();ui=h.documents_window
            assert 'Documents' in dict(h.active_tools())
            with patch('aeris.documents_ui.filedialog.askopenfilename',return_value=str(p)) as dialog:
                ui.choose();dialog.assert_not_called();h.permissions.set(DOCUMENTS_READ,True);ui.choose();dialog.assert_called_once()
            with patch('aeris.documents_ui.messagebox.askyesno',return_value=True):ui.run()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.job is None and 'Example document' in ui.report.get('1.0','end')
            h.permissions.set(DOCUMENTS_READ,False);assert ui.path is None and 'Example document' not in ui.report.get('1.0','end')
            h.permissions.set(DOCUMENTS_READ,True);h.toggle_tool('Documents');assert not h.alive(ui) and not h.permissions.allowed(DOCUMENTS_READ)
            h.toggle_tool('Documents');h.open_tool('Documents');ui=h.documents_window
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert not h.alive(ui) and h.documents_window is None
        finally:root.destroy()
    print('Documents smoke: OK')
if __name__=='__main__':main()
