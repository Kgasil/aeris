import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.privacy import inventory

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'));h.open_tool('Learn');assert h.learn_window is None
            h.toggle_tool('Learn');h.open_tool('Learn');ui=h.learn_window
            assert 'Learn' in dict(h.active_tools())
            with patch('aeris.learn_ui.simpledialog.askstring',return_value='Python'):ui.create()
            p=ui.plan_id();store=ui.store
            with patch.object(ui,'topic_fields',return_value=('Fundamentos',30)):ui.add()
            with patch.object(ui,'topic_fields',return_value=('APIs',90)):ui.add()
            a,b=store.get(p).topics;ui.tree.selection_set(str(b.id));ui.move(-1);ui.toggle()
            assert ui.stats.get()=='1/2 tópicos · 90/120 min estimados concluídos'
            with patch.object(ui,'topic_fields',return_value=('APIs REST',60)):ui.edit()
            assert store.get(p).topics[0].title=='APIs REST'
            with patch.object(ui,'topic_fields',return_value=None):ui.add()
            assert len(store.get(p).topics)==2
            assert dict(inventory(h)[2])['learn']==1
            ui.window.destroy();h.open_tool('Learn');ui=h.learn_window;assert ui.stats.get()=='1/2 tópicos · 60/90 min estimados concluídos'
            with patch('aeris.hub.messagebox.askyesno',return_value=False):h.toggle_tool('Learn')
            assert h.enabled('Learn') and h.alive(ui)
            with patch('aeris.hub.messagebox.askyesno',return_value=True):h.toggle_tool('Learn')
            assert h.learn_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Learn');h.open_tool('Learn');ui=h.learn_window;ui.store.create('SQL');ui.refresh()
            with patch('aeris.hub.messagebox.askyesno',return_value=True):assert h.clear_session()
            assert not ui.store.list() and h.learn_store is None
        finally:root.destroy()
    print('Learn smoke: OK')

if __name__=='__main__':main()
