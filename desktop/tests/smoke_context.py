import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import CONTEXT_PREVIEW
from aeris.privacy import inventory

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Context'); assert h.context_window is None
            h.toggle_tool('Context'); h.open_tool('Context'); u=h.context_window
            assert 'Context' in dict(h.active_tools())
            u.title.set('Objetivo'); u.body.insert('1.0','Aprender Python'); u.save(); a=u.store.list()[0]
            assert dict(inventory(h)[2])['context']==1 and not u.dirty()
            h.permissions.set(CONTEXT_PREVIEW,True); u.tree.selection_set(str(a.id))
            with patch('aeris.context_ui.messagebox.askyesno',return_value=False): u.toggle_selected()
            assert not u.store.selected(a.id)
            with patch('aeris.context_ui.messagebox.askyesno',return_value=True): u.toggle_selected()
            u.generate(); assert 'Aprender Python' in u.preview.get('1.0','end')
            h.permissions.set(CONTEXT_PREVIEW,False); assert not u.store.selected(a.id) and not u.preview.get('1.0','end-1c')
            h.permissions.set(CONTEXT_PREVIEW,True); u.tree.selection_set(str(a.id))
            with patch('aeris.context_ui.messagebox.askyesno',return_value=True): u.toggle_selected()
            u.close(); assert not h.alive(u); h.permissions.set(CONTEXT_PREVIEW,False); h.permissions.set(CONTEXT_PREVIEW,True)
            h.open_tool('Context'); u=h.context_window; assert not u.store.selected(a.id) and len(u.store.list())==1
            u.tree.selection_set(str(a.id)); u.load_selected(); u.body.insert('end','!')
            with patch('aeris.context_ui.messagebox.askyesno',return_value=False): u.close()
            assert h.alive(u)
            u.save(); store=u.store
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Context')
            assert h.enabled('Context') and store.list()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not store.list() and not h.alive(u) and not h.permissions.allowed(CONTEXT_PREVIEW)
            h.open_tool('Context'); u=h.context_window; u.title.set('Outro'); u.body.insert('1.0','teste'); u.save(); store=u.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Context')
            assert not store.list() and not h.enabled('Context')
        finally: root.destroy()
    print('Context smoke: OK')
if __name__=='__main__':main()
