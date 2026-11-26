import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import ROUTINE_RUN, ROUTINE_COPY, BRIDGE_RUN

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for n in ('Routine','Bridge','Expand','Text','Capture'): h.toggle_tool(n)
            h.open_tool('Routine'); root.update(); ui=h.routine_window
            assert 'Routine' in dict(h.quick_tools())
            assert str(ui.run_button.cget('state'))=='disabled'
            ui.add(); ui.step.set('Text → Capture'); ui.add(); ui.save(); assert len(h.routine_store.list())==1
            ui.input.insert('1.0','  ;att  '); root.update()
            for cap in (ROUTINE_RUN,BRIDGE_RUN,ROUTINE_COPY): h.permissions.set(cap,True)
            ui.run(); assert ui.preview.text=='Atenciosamente,' and h.capture_store is None
            with patch('aeris.routine_ui.messagebox.askyesno',return_value=True): ui.copy()
            assert root.clipboard_get()=='Atenciosamente,'
            h.permissions.set(ROUTINE_RUN,False); assert ui.preview is None
            h.permissions.set(ROUTINE_RUN,True); ui.run(); assert ui.preview
            ui.input.insert('end','!'); root.update(); assert ui.preview is None
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Bridge')
            assert h.routine_window is None and not h.permissions.allowed(ROUTINE_RUN)
            assert len(h.routine_store.list())==1
            h.open_tool('Routine')
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.routine_store is None and h.routine_window is None
        finally: root.destroy()
    print('Routine smoke: OK')
if __name__=='__main__': main()
