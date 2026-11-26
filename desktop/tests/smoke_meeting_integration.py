import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import INTEGRATION_RUN
from aeris.meeting import Action

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for name in ('Meeting','Checklist','Reminder'):
                if not h.enabled(name): h.toggle_tool(name)
                h.open_tool(name)
            u=h.meeting_window; h.checklist_store.create('Projeto'); h.checklist_window.refresh_lists('Projeto')
            day=(datetime.now()+timedelta(days=1)).date().isoformat()
            item=h.meeting_store.add('Reunião','','','','',(Action('Revisar','Ana',day),)); u.set_editor(item); u.render_actions(0)
            root.update()
            u.transfer('Checklist'); assert not h.checklist_store.list()
            h.permissions.set(INTEGRATION_RUN,True)
            with patch('aeris.meeting_ui.simpledialog.askstring',return_value='Projeto'),patch('aeris.meeting_ui.messagebox.askyesno',return_value=False): u.transfer('Checklist')
            assert not h.checklist_store.list()
            with patch('aeris.meeting_ui.simpledialog.askstring',return_value='Projeto'),patch('aeris.meeting_ui.messagebox.askyesno',return_value=True): u.transfer('Checklist'); u.transfer('Checklist')
            assert len(h.checklist_store.list())==1 and len(h.checklist_window.tree.get_children())==1
            def revoke(*a,**k): h.permissions.set(INTEGRATION_RUN,False); return True
            with patch('aeris.meeting_ui.simpledialog.askstring',return_value='14:00'),patch('aeris.meeting_ui.messagebox.askyesno',side_effect=revoke): u.transfer('Reminder')
            assert not h.reminder_store.list()
            h.permissions.set(INTEGRATION_RUN,True)
            with patch('aeris.meeting_ui.simpledialog.askstring',return_value='14:00'),patch('aeris.meeting_ui.messagebox.askyesno',return_value=True): u.transfer('Reminder')
            assert len(h.reminder_store.list())==1 and h.reminder_job is not None and len(h.reminder_window.tree.get_children())==1
            assert u.store.get(item.id) is item
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not h.permissions.allowed(INTEGRATION_RUN)
        finally: root.destroy()
    print('Integration smoke: OK')
if __name__=='__main__': main()
