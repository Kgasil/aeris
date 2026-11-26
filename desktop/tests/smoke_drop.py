import time, tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DROP_ADD, DROP_COPY
from aeris.drop import Cancelled

def main():
    with TemporaryDirectory() as d:
        a=Path(d)/'a.txt';b=Path(d)/'b.csv';a.write_bytes(b'abc');b.write_bytes(b'1,2');root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Drop');assert h.drop_window is None
            h.toggle_tool('Drop');h.open_tool('Drop');ui=h.drop_window;assert 'Drop' in dict(h.active_tools())
            with patch('aeris.drop_ui.filedialog.askopenfilenames',return_value=(str(a),str(b))) as dialog,patch('aeris.drop_ui.messagebox.askyesno',return_value=True):
                ui.choose();dialog.assert_not_called();h.permissions.set(DROP_ADD,True);ui.choose();dialog.assert_called_once()
            deadline=time.monotonic()+3
            while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
            assert ui.job is None and len(h.drop_store.list())==2
            ui.listbox.selection_set(0,1);ui.copy();h.permissions.set(DROP_COPY,True);ui.listbox.selection_set(0,1)
            with patch('aeris.drop_ui.messagebox.askyesno',return_value=True):ui.copy()
            assert root.clipboard_get()==str(a)+'\n'+str(b)
            ui.listbox.selection_clear(0,'end');ui.listbox.selection_set(0);ui.remove();assert len(h.drop_store.list())==1 and a.read_bytes()==b'abc'
            ui.close();h.open_tool('Drop');ui=h.drop_window;assert len(ui.items)==1
            ui.close();h.permissions.set(DROP_ADD,False);assert not h.drop_store.list();h.open_tool('Drop');ui=h.drop_window
            h.permissions.set(DROP_ADD,True)
            def slow(paths,cancelled):
                while not cancelled():time.sleep(.01)
                raise Cancelled()
            with patch('aeris.drop_ui.inspect_paths',side_effect=slow),patch('aeris.drop_ui.filedialog.askopenfilenames',return_value=(str(a),)),patch('aeris.drop_ui.messagebox.askyesno',return_value=True):
                ui.choose();assert ui.job;h.permissions.set(DROP_ADD,False)
                deadline=time.monotonic()+3
                while ui.job and time.monotonic()<deadline:root.update();time.sleep(.02)
                assert ui.job is None and not h.drop_store.list()
            h.toggle_tool('Drop');assert not h.alive(ui) and h.drop_store is None and not h.permissions.allowed(DROP_COPY)
            h.toggle_tool('Drop');h.open_tool('Drop')
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert h.drop_store is None and h.drop_window is None and b.read_bytes()==b'1,2'
        finally:root.destroy()
    print('Drop smoke: OK')
if __name__=='__main__':main()
