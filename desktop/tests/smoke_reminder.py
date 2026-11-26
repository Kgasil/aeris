import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.privacy import inventory

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Reminder'); assert h.reminder_window is None
            h.toggle_tool('Reminder'); h.open_tool('Reminder'); ui=h.reminder_window; store=ui.store
            now=[1000.]; store.clock=lambda:now[0]
            ui.title.set('Reunião'); ui.minutes.set('1'); ui.alert.set(True); ui.add()
            r=store.list()[0]; assert r.title=='Reunião' and h.reminder_job is not None
            assert dict(inventory(h)[2])['reminder']==1
            ui.tree.selection_set(str(r.id)); ui.select(); ui.title.set('Reunião de equipe'); ui.edit(); assert store.list()[0].title=='Reunião de equipe'
            ui.window.destroy(); now[0]=1061.; h.poll_reminders()
            assert store.list()[0].state=='due' and h.alive(h.reminder_alert) and h.reminder_job is None
            h.poll_reminders(); assert h.reminder_alert.count==1 and 'Reunião' not in h.reminder_alert.message.get()
            h.reminder_alert.open(); ui=h.reminder_window; assert h.alive(ui) and ui.tree.get_children()
            ui.title.set('Cancelar'); ui.minutes.set('5'); ui.alert.set(False); ui.add(); r=store.list()[-1]
            ui.tree.selection_set(str(r.id)); ui.cancel(); assert h.reminder_job is None and store.list()[-1].state=='cancelled'
            h.toggle_tool('Reminder'); assert h.reminder_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Reminder'); h.open_tool('Reminder'); ui=h.reminder_window; ui.title.set('Nova'); ui.add(); assert h.reminder_job is not None
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.reminder_store is None and h.reminder_job is None and not ui.store.list()
        finally: root.destroy()
    print('Reminder smoke: OK')
if __name__=='__main__': main()
