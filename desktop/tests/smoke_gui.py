"""Requer ambiente gráfico: python -m tests.smoke_gui"""
import tkinter as tk
from aeris.hub import Hub

def main():
    root = tk.Tk()
    try:
        hub = Hub(root)
        root.update()
        assert hub.listbox.size() == 50
        assert hub.detail_name.cget('text') == 'Hub'
        hub.query.set('Snippets')
        root.update()
        assert hub.listbox.size() == 1
        assert hub.detail_name.cget('text') == 'Snippets'
        assert 'não implementado' in hub.detail_status.cget('text')
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

if __name__ == '__main__':
    main()
