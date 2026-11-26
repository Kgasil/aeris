"""Verify entry point and frozen-mode UI guard using real Tk, not a Windows build."""
from pathlib import Path
import sys
import tkinter as tk
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.distribution import self_test
from aeris.hub import Hub
from aeris.settings import Settings


def main():
    assert self_test() == 0
    assert self_test(full=True) == 0
    with TemporaryDirectory() as directory, patch.object(sys, 'frozen', True, create=True):
        root = tk.Tk()
        try:
            hub = Hub(root, Settings(Path(directory) / 'settings.json'))
            hub.toggle_tool('Translate'); hub.open_tool('Translate'); root.update()
            ui = hub.translate_window
            ui.input.insert('1.0', 'Bom dia!'); ui.translate()
            assert ui.output == 'Good morning!'
            ui.mode.set('Modelo local (experimental)')
            with patch('aeris.translate_ui.subprocess.Popen') as spawn:
                ui.translate(); spawn.assert_not_called()
            assert 'indisponível' in ui.status.get()
        finally:
            root.destroy()
    print('Distribution entry and frozen mode smoke: OK')


if __name__ == '__main__':
    main()
