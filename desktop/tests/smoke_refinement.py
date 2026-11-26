import tkinter as tk
from tkinter import ttk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS
from aeris.theme import PALETTES

def main():
    with TemporaryDirectory() as folder:
        path=Path(folder)/'settings.json'; root=tk.Tk()
        try:
            h=Hub(root,Settings(path)); root.update()
            for name in ('Capture','Snippets','Search'): h.toggle_tool(name)
            for capability in (SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS): h.permissions.set(capability, True)
            h.open_capture(); c=h.capture_window; c.title.set('Teste'); c.body.insert('1.0','FICTICIO'); c.save(); c.body.insert('end',' rascunho')
            h.open_snippets(); s=h.snippets_window; s.title.set('Snippet'); s.body.insert('1.0','EXEMPLO'); s.save()
            h.open_appearance(); a=h.appearance_window; a.theme.set('Escuro'); a.floating.set(True); a.favorites['Search'].set(True); a.favorites_only.set(True); a.save(); root.update()
            assert root.cget('bg')==PALETTES['Escuro']['air']
            assert c.body.cget('bg')==PALETTES['Escuro']['field']
            assert Settings(path).appearance.theme=='Escuro'
            h.spotlight.show_panel(); root.update()
            buttons=[w.cget('text') for f in h.spotlight.panel.winfo_children() for w in f.winfo_children() if isinstance(w,ttk.Button)]
            assert buttons==['Search','Hub / Configurações','Ocultar ícone'], buttons
            h.spotlight.dismiss(); h.toggle_quick_panel(); root.update()
            assert h.alive(h.quick_panel)
            h.open_search(); q=h.search_window; q.sources['Capture'].set(True); q.query.set('ficticio'); assert q.results
            h.open_privacy(); root.update(); root.clipboard_clear(); root.clipboard_append('clipboard de teste')
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.privacy_window.clear()
            assert h.capture_store.list() and h.alive(h.search_window)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.privacy_window.clear()
            assert h.capture_store is None and h.snippets_store is None and not h.alive(h.search_window)
            assert root.clipboard_get()=='clipboard de teste'
            assert h.settings.capture_enabled and h.settings.snippets_enabled
            assert 'FICTICIO' not in path.read_text() and 'EXEMPLO' not in path.read_text()
            h.privacy_window.hide(); assert h.spotlight is None
            h.open_appearance(); a=h.appearance_window; a.theme.set('Claro'); a.save(); root.update()
            assert root.cget('bg')==PALETTES['Claro']['air'] and h.spotlight is None
            print('Smoke refinamento: OK')
        finally: root.destroy()
if __name__=='__main__': main()
