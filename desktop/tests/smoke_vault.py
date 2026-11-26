"""UI smoke with test double, not proof of Windows encryption."""
import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.vault import Vault
from tests.test_vault import TestBackend

def main():
    with TemporaryDirectory() as folder:
        root=tk.Tk()
        try:
            settings=Settings(Path(folder)/'settings.json')
            hub=Hub(root,settings); settings.set_module('Vault',True)
            with patch('aeris.vault.Vault',side_effect=lambda path:Vault(path,TestBackend())):
                hub.open_tool('Vault')
            ui=hub.vault_window; assert not ui.vault.unlocked
            ui.unlock(); root.update(); assert ui.vault.unlocked
            ui.title.set('Fictício'); ui.body.insert('1.0','Conteúdo'); ui.save(); root.update()
            assert len(ui.vault.list())==1
            ui.lock(); assert not ui.vault.unlocked
            ui.unlock(); assert len(ui.vault.list())==1
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert hub.clear_session()
            assert not ui.vault.unlocked
            ui.unlock(); assert len(ui.vault.list())==1
            ui.close(); assert not ui.vault.unlocked
        finally: root.destroy()
    print('Vault UI smoke: OK (test backend)')
if __name__=='__main__': main()
