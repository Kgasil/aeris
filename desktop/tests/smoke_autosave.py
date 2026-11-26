import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import STORAGE_AUTO, STORAGE_SAVE, STORAGE_DELETE
from aeris.protected_storage import ProtectedStorage
from tests.test_protected_storage import FakeBackend

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.query.set('Checklist'); h.toggle.invoke(); h.launch.invoke(); root.update()
            h.checklist_store.create('A'); h.checklist_store.add('A','Fictício'); h.open_privacy(); root.update()
            p=h.privacy_window.auto_panel; storage=ProtectedStorage(d,FakeBackend())
            with patch('aeris.protected_storage.ProtectedStorage',return_value=storage),patch('aeris.autosave_ui.messagebox.askyesno',return_value=True),patch('aeris.hub.messagebox.askyesno',return_value=True):
                p.arm(); assert h.autosave_job is None
                h.permissions.set(STORAGE_AUTO,True); p.arm(); assert h.autosave_job is None
                h.permissions.set(STORAGE_SAVE,True); p.arm(); assert h.autosave_job is not None
                p.flush(); assert storage.path('Checklist').exists(); original=storage.path('Checklist').read_bytes()
                h.checklist_store.add('A','Outra'); h.permissions.set(STORAGE_AUTO,False); assert h.autosave_job is None and not h.autosave.armed
                p.flush(); assert storage.path('Checklist').read_bytes()==original
                h.permissions.set(STORAGE_AUTO,True); p.arm(); assert not h.autosave.armed
                # Reconcile manually; then arm again.
                panel=h.privacy_window.storage_panel
                with patch.object(panel,'storage',return_value=storage),patch('aeris.storage_ui.messagebox.askyesno',return_value=True):
                    panel.save(); p.arm(); assert h.autosave_job is not None
                    h.permissions.set(STORAGE_DELETE,True); panel.delete(); assert h.autosave_job is None and not storage.path('Checklist').exists()
                    panel.save(); p.arm(); assert h.autosave_job is not None
                    original=storage.path('Checklist').read_bytes()
                    h.checklist_store.add('A','Não salvar ao limpar'); assert h.clear_session(); assert h.autosave_job is None and not h.autosave.armed
                    assert storage.path('Checklist').read_bytes()==original
            root.update()
        finally: root.destroy()
    print('AutoSave smoke: OK')
if __name__=='__main__': main()
