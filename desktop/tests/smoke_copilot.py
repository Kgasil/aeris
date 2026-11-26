import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.copilot import EXAMPLES
from aeris.permissions import COPILOT_RUN

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Copilot');assert h.copilot_window is None
            for n in ('Copilot','Checklist','Focus','Ideas','Reminder'):h.toggle_tool(n)
            h.open_tool('Checklist');h.checklist_store.create('Estudos');h.checklist_window.refresh_lists('Estudos')
            h.open_tool('Copilot');ui=h.copilot_window;root.update()
            ui.command.set(EXAMPLES[0]);ui.prepare();assert not ui.session.pending
            h.permissions.set(COPILOT_RUN,True);ui.prepare();assert ui.session.pending and h.reminder_store is None
            ui.command.set(EXAMPLES[1]);assert not ui.session.pending;ui.prepare();ui.confirm();assert len(h.reminder_store.list())==1 and h.reminder_job is not None
            ui.confirm();assert len(h.reminder_store.list())==1
            ui.command.set(EXAMPLES[2]);ui.prepare();ui.confirm();assert len(h.checklist_store.tasks('Estudos'))==1 and len(h.checklist_window.tree.get_children())==1
            ui.command.set(EXAMPLES[4]);ui.prepare();h.permissions.set(COPILOT_RUN,False);assert not ui.session.pending;ui.confirm();assert h.ideas_store is None
            h.permissions.set(COPILOT_RUN,True);ui.prepare();ui.confirm();assert len(h.ideas_store.list())==1
            ui.command.set(EXAMPLES[3]);ui.prepare();ui.confirm();root.update();assert h.focus_timer.state=='running' and h.focus_window.callback is not None
            ui.prepare();assert not ui.session.pending
            ui.command.set(EXAMPLES[4]);ui.prepare();h.toggle_tool('Copilot');assert not h.permissions.allowed(COPILOT_RUN) and not h.alive(ui) and ui.session.pending is None
            h.toggle_tool('Copilot');h.open_tool('Copilot');assert not h.copilot_window.command.get()
            with patch('aeris.hub.messagebox.askyesno',return_value=True):h.clear_session()
            assert h.copilot_window is None and h.focus_timer is None and h.reminder_store is None and h.ideas_store is None and h.checklist_store is None
        finally:root.destroy()
    print('Copilot smoke: OK')
if __name__=='__main__':main()
