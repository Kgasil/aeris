import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import STORAGE_SAVE, STORAGE_LOAD, STORAGE_DELETE
from aeris.protected_storage import ProtectedStorage
from tests.test_protected_storage import FakeBackend

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            h.query.set('Checklist'); h.toggle.invoke(); h.launch.invoke(); root.update()
            assert h.alive(h.checklist_window)
            h.checklist_store.create('Estudos'); h.checklist_store.add('Estudos','Fictício')
            h.open_privacy(); root.update(); panel=h.privacy_window.storage_panel
            storage=ProtectedStorage(d,FakeBackend())
            with patch.object(panel,'storage',return_value=storage),patch('aeris.storage_ui.messagebox.askyesno',return_value=True):
                panel.save(); assert not storage.path('Checklist').exists()
                h.permissions.set(STORAGE_SAVE,True); panel.save(); assert storage.path('Checklist').exists()
                h.checklist_store.add('Estudos','Temporário'); h.permissions.set(STORAGE_LOAD,True)
                panel.load(); assert len(h.checklist_store.list())==2 # open window blocks restore
                h.close_window('checklist_window'); panel.load(); assert len(h.checklist_store.list())==1
                with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
                assert h.checklist_store is None and storage.path('Checklist').exists()
                panel.load(); assert h.checklist_store is None # permission revoked
                h.permissions.set(STORAGE_LOAD,True); panel.load(); assert len(h.checklist_store.list())==1
                h.permissions.set(STORAGE_DELETE,True); panel.delete(); assert not storage.path('Checklist').exists() and len(h.checklist_store.list())==1
                # Restore a real reminder store after closing the editor, and re-arm its timer.
                h.query.set('Reminder'); root.update(); h.toggle.invoke(); h.launch.invoke(); root.update()
                assert h.alive(h.reminder_window)
                from time import time
                future=h.reminder_store.add('Futuro',30,True)
                h.reminder_store.restore_record('Vencido',time()-60,True,'pending')
                h.schedule_reminders(); assert h.reminder_job is not None
                panel.module.set('Reminder'); h.permissions.set(STORAGE_SAVE,True); panel.save()
                assert storage.path('Reminder').exists()
                h.reminder_store.add('Descartar',45)
                panel.load(); assert len(h.reminder_store.list())==3
                h.close_window('reminder_window'); old_job=h.reminder_job; panel.load()
                assert len(h.reminder_store.list())==2 and h.reminder_job is not None and h.reminder_job!=old_job
                assert not h.alive(h.reminder_alert)
                assert h.reminder_store.list()[0].state=='due' and h.reminder_store.list()[1].due==future.due
                h.open_tool('Reminder'); root.update(); assert h.alive(h.reminder_window)
                assert len(h.reminder_window.tree.get_children())==2
                h.reset_reminders()

        finally: root.destroy()
    print('Protected storage smoke: OK')
if __name__=='__main__': main()
