import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings, Appearance
from aeris.permissions import CREATE_BACKUP, RESTORE_BACKUP

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Backup'); h.open_tool('Backup'); root.update()
            ui=h.backup_window; path=str(Path(d)/'copy.aerisbackup')
            assert str(ui.create_button.cget('state'))=='disabled'
            h.permissions.set(CREATE_BACKUP,True); h.permissions.set(RESTORE_BACKUP,True)
            with patch('aeris.backup_ui.filedialog.asksaveasfilename',return_value=path), patch('aeris.backup_ui.messagebox.askyesno',return_value=True): ui.create()
            assert Path(path).is_file()
            with patch('aeris.backup_ui.filedialog.askopenfilename',return_value=path): ui.inspect()
            assert ui.choice.get()=='Aparência'
            h.settings.set_appearance(Appearance(theme='Escuro'))
            with patch('aeris.backup_ui.messagebox.askyesno',return_value=True): ui.restore()
            assert h.settings.appearance.theme=='Claro'
            h.permissions.set(RESTORE_BACKUP,False); assert ui.path is None
            h.toggle_tool('Backup'); assert not h.enabled('Backup') and h.backup_window is None and not h.permissions.allowed(CREATE_BACKUP)
        finally: root.destroy()
    print('Backup UI smoke: OK')
if __name__=='__main__': main()
