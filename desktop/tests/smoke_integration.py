"""Integração real em display gráfico de teste; sem dados pessoais."""
import tkinter as tk
from tkinter import ttk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); root.update()
            assert h.listbox.size()==50 and h.detail_name.cget('text')=='Hub'
            assert h.spotlight is None and not h.active_tools()
            for name in ('Capture','Snippets','Search'): h.toggle_tool(name)
            for capability in (SEARCH_CAPTURE, SEARCH_SNIPPETS, COPY_SNIPPETS): h.permissions.set(capability, True)
            assert len(h.active_tools())==3
            h.open_capture(); c=h.capture_window; c.title.set('Reunião'); c.body.insert('1.0','SQL e Python'); c.save()
            assert c.store.list()[0].title=='Reunião'
            h.open_snippets(); s=h.snippets_window; s.title.set('SQL'); s.category.set('Código'); s.body.insert('1.0','SELECT 1'); s.save()
            with patch('aeris.editor.messagebox.askyesno',return_value=True): s.copy()
            assert root.clipboard_get()=='SELECT 1'
            h.open_search(); q=h.search_window; q.query.set('sql'); assert not q.results
            q.sources['Capture'].set(True); q.sources['Snippets'].set(True); q.refresh()
            assert [r.source for r in q.results]==['Snippets','Capture']
            q.items.selection_set(0); q.open_selected(); assert not q.window.winfo_exists() and s.current==1
            h.open_search(); q=h.search_window; q.sources['Capture'].set(True); q.query.set('sql'); assert len(q.results)==1
            with patch('aeris.editor.messagebox.askyesno',return_value=True): c.delete()
            assert not q.results
            h.toggle_quick_panel(); root.update(); assert h.alive(h.quick_panel)
            h.open_appearance(); a=h.appearance_window; a.floating.set(True); a.icon.set(48); a.save(); root.update()
            assert h.spotlight and h.spotlight.bounds[:2]==(48,48)
            h.spotlight.button.event_generate('<ButtonRelease-1>',x=12,y=12); root.update()
            assert h.spotlight.panel and h.spotlight.panel.winfo_exists()
            buttons=[w for f in h.spotlight.panel.winfo_children() for w in f.winfo_children() if isinstance(w,ttk.Button)]
            assert [b.cget('text') for b in buttons][:3]==['Capture','Snippets','Search']
            buttons[2].invoke(); root.update(); assert h.alive(h.search_window)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Snippets')
            assert h.snippets_store is None and not h.alive(h.search_window)
            h.hide_spotlight(); assert h.spotlight is None
            h.toggle_spotlight_visibility(); assert h.spotlight is not None
            print('Smoke integrado Foundation: OK')
        finally: root.destroy()
if __name__=='__main__': main()
