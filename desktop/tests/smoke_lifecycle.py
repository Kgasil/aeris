"""UI ownership, trace removal and session store continuity."""
import gc
import sys
import tkinter as tk
import weakref
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.hub import Hub
from aeris.settings import Settings
from tests.benchmark_lifecycle import TOOLS


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk(); hub=Hub(root,Settings(Path(d)/'settings.json'))
        try:
            assert not any('aeris.'+name in sys.modules for name in ('companion','data','lens','protected_storage'))
            refs=[]
            for name in TOOLS:
                hub.toggle_tool(name); hub.open_tool(name)
                attr=name.lower()+'_window'; ui=getattr(hub,attr)
                hub.open_tool(name); assert getattr(hub,attr) is ui
                if name=='Capture':
                    hub.capture_store.save('Nota de teste','Texto de teste')
                    ui.query.set('Nota')
                if name=='Calculator':
                    old=ui.inputs[0]; ui.change_operation(); assert not old.trace_info(); del old
                if name=='Decision':
                    old=ui.fields[0]; ui.build_matrix(3,3); assert not old.trace_info(); del old
                if name=='Copilot':
                    ui.open_companion(); c=ui.companion
                    c.window.destroy(); assert ui.companion is None and not c.model.trace_info()
                    refs.append(weakref.ref(c)); del c
                refs.append(weakref.ref(ui)); ui.window.destroy()
                assert getattr(hub,attr) is None
                del ui; root.update()
            gc.collect(); assert all(ref() is None for ref in refs), [ref().__class__.__name__ for ref in refs if ref() is not None]
            assert len(hub.capture_store.list())==1
            hub.open_tool('Capture'); assert len(hub.capture_window.store.list())==1
            hub.open_permissions(); hub.permissions_window.window.destroy(); assert hub.permissions_window is None
            hub.open_privacy(); hub.privacy_window.window.destroy(); assert hub.privacy_window is None
        finally: root.destroy()
    print('Lifecycle smoke: OK')

if __name__=='__main__':main()
