import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for name in ('Capture','Snippets','Search'): h.toggle_tool(name)
            h.open_capture(); h.capture_store.save('Teste','ficticio')
            h.open_snippets(); s=h.snippets_window; s.fill(h.snippets_store.save('Teste','Geral','ficticio'))
            root.clipboard_clear(); root.clipboard_append('original')
            s.copy(); assert root.clipboard_get()=='original'
            h.open_search(); q=h.search_window; q.query.set('ficticio'); q.sources['Capture'].set(True); q.refresh(); assert not q.results
            h.open_permissions(); root.update()
            with patch('aeris.permissions_ui.ask_permission',return_value=True): h.permissions_window.toggle(SEARCH_CAPTURE)
            q.sources['Capture'].set(True); q.refresh(); assert len(q.results)==1
            result=q.results[0]; q.items.selection_set(0); q.preview(); h.permissions.set(SEARCH_CAPTURE,False)
            assert not q.results and not q.detail.get('1.0','end-1c') and not h.open_search_result(result)
            h.permissions.set(COPY_SNIPPETS,True)
            with patch('aeris.editor.messagebox.askyesno',return_value=True): s.copy()
            assert root.clipboard_get()=='ficticio'
            h.permissions.set(COPY_SNIPPETS,False); root.clipboard_clear(); root.clipboard_append('original'); s.copy(); assert root.clipboard_get()=='original'
            h.permissions.set(SEARCH_SNIPPETS,True)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not h.permissions.allowed(SEARCH_SNIPPETS) and root.clipboard_get()=='original'
            print('Smoke Permissions: OK')
        finally: root.destroy()
if __name__=='__main__': main()
