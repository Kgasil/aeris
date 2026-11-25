"""Requer ambiente gráfico: python -m tests.smoke_gui"""
import tkinter as tk
from aeris.hub import Hub
from aeris.settings import Settings
from tempfile import TemporaryDirectory
from pathlib import Path

def main():
    folder = TemporaryDirectory()
    root = tk.Tk()
    try:
        hub = Hub(root, Settings(Path(folder.name) / 'settings.json'))
        root.update()
        assert hub.listbox.size() == 50
        assert hub.detail_name.cget('text') == 'Hub'
        hub.query.set('Snippets')
        root.update()
        assert hub.listbox.size() == 1
        assert hub.detail_name.cget('text') == 'Snippets'
        assert 'desativado' in hub.detail_status.cget('text')
        hub.toggle.invoke()
        assert hub.settings.snippets_enabled
        hub.launch.invoke()
        root.update()
        assert hub.snippets_window.window.winfo_exists()
        hub.snippets_window.window.destroy()
        hub.query.set('zzzzzzzzzz')
        root.update()
        assert hub.detail_name.cget('text') == 'Nenhum resultado'
        hub.query.set('')
        hub.category.set('Security')
        root.update()
        assert hub.listbox.size() == 5
        print('Smoke test do Hub: OK')
    finally:
        root.destroy()
        folder.cleanup()

if __name__ == '__main__':
    main()
