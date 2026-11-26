import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import BRIDGE_CAPTURE, BRIDGE_RUN, BRIDGE_COPY, BRIDGE_SAVE

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for name in ('Bridge','Capture','Text','Expand'): h.toggle_tool(name)
            h.open_tool('Capture'); h.capture_store.save('Demo',';att'); h.open_tool('Bridge'); root.update(); ui=h.bridge_window
            assert 'Bridge' in dict(h.quick_tools())
            assert str(ui.run_button.cget('state'))=='disabled'
            ui.source.set('Capture'); ui.list_records(); assert not ui.records
            for cap in (BRIDGE_CAPTURE,BRIDGE_RUN,BRIDGE_COPY,BRIDGE_SAVE): h.permissions.set(cap,True)
            ui.list_records(); assert len(ui.records)==1
            with patch('aeris.bridge_ui.messagebox.askyesno',return_value=True): ui.import_record()
            root.update(); ui.run(); assert ui.preview.text=='Atenciosamente,'
            with patch('aeris.bridge_ui.messagebox.askyesno',return_value=True): ui.copy()
            assert root.clipboard_get()=='Atenciosamente,'
            h.permissions.set(BRIDGE_CAPTURE,False); root.update(); assert ui.preview is None and not ui.input.get('1.0','end-1c')
            ui.source.set('Manual'); ui.route.set('Text → Capture'); ui.input.insert('1.0','Olá   mundo'); root.update(); ui.run()
            with patch('aeris.bridge_ui.messagebox.askyesno',return_value=True): ui.save()
            assert h.capture_store.list()[-1].body=='Olá mundo'
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Expand')
            assert h.bridge_window is None and not h.permissions.allowed(BRIDGE_RUN)
            h.open_tool('Bridge'); h.permissions.set(BRIDGE_RUN,True)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.bridge_window is None and not h.permissions.allowed(BRIDGE_RUN)
        finally: root.destroy()
    print('Bridge smoke: OK')
if __name__=='__main__': main()
