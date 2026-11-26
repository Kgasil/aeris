import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings, Appearance
from aeris.workspace import TOOLS
from aeris.permissions import WORKSPACE_OPEN

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for n in ('Workspace','Capture','Search'): h.toggle_tool(n)
            h.open_tool('Workspace'); root.update(); ui=h.workspace_window
            ui.name.set('Estudos'); ui.tools.selection_set(TOOLS.index('Capture')); ui.tools.selection_set(TOOLS.index('Text'))
            ui.links.insert('1.0','https://example.org'); ui.save(); ui.activate()
            assert [n for n,_ in h.quick_tools()]==['Capture','Workspace'] and not h.enabled('Text')
            ui.actions.current(2); ui.permissions_changed(); assert str(ui.open_button.cget('state'))=='disabled'
            h.permissions.set(WORKSPACE_OPEN,True); assert str(ui.open_button.cget('state'))=='normal'
            with patch('aeris.workspace_ui.messagebox.askyesno',return_value=True), patch.object(h.workspace_store,'open_link') as launch:
                ui.open_selected(); launch.assert_called_once_with('Estudos',0,h.permissions)
            h.permissions.set(WORKSPACE_OPEN,False); assert str(ui.open_button.cget('state'))=='disabled'
            ui.deactivate(); assert [n for n,_ in h.quick_tools()]==['Capture','Search','Workspace']
            ui.activate(); h.toggle_quick_panel(); root.update(); assert h.alive(h.quick_panel)
            ui.deactivate(); assert not h.alive(h.quick_panel)
            h.permissions.set(WORKSPACE_OPEN,True)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.workspace_store is None and h.workspace_window is None and not h.permissions.allowed(WORKSPACE_OPEN)
        finally: root.destroy()
    print('Workspace smoke: OK')
if __name__=='__main__': main()
