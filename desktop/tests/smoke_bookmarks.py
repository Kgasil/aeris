"""GUI with simulated storage and launcher. No real website opened."""
import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings, Appearance
from aeris.permissions import OPEN_BOOKMARK
from aeris.bookmarks import BookmarkStore
from tests.test_vault import TestBackend

def main():
    with TemporaryDirectory() as folder:
        root=tk.Tk(); opened=[]
        try:
            h=Hub(root,Settings(Path(folder)/'settings.json')); h.toggle_tool('Bookmarks')
            assert 'Bookmarks' in dict(h.active_tools())
            with patch('aeris.bookmarks.BookmarkStore',side_effect=lambda path,permissions:BookmarkStore(path,permissions,TestBackend(),opened.append)):
                h.open_tool('Bookmarks')
            ui=h.bookmarks_window; ui.unlock(); root.update()
            ui.title.set('Documentação'); ui.category.set('Estudos'); ui.url.set('https://example.com'); ui.save()
            assert len(ui.store.list())==1 and str(ui.open_button.cget('state'))=='disabled'
            ui.open_selected(); assert not opened
            h.permissions.set(OPEN_BOOKMARK,True); assert str(ui.open_button.cget('state'))=='normal'
            with patch('aeris.bookmarks_ui.messagebox.askyesno',return_value=False): ui.open_selected()
            assert not opened
            with patch('aeris.bookmarks_ui.messagebox.askyesno',return_value=True): ui.open_selected()
            assert opened==['https://example.com']
            h.permissions.set(OPEN_BOOKMARK,False); assert str(ui.open_button.cget('state'))=='disabled'
            ui.query.set('documentacao'); assert len(ui.visible)==1
            ui.lock(); assert not ui.store.unlocked; ui.unlock(); assert len(ui.store.list())==1
            h.permissions.set(OPEN_BOOKMARK,True)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert not ui.store.unlocked and not h.permissions.allowed(OPEN_BOOKMARK)
            ui.unlock(); assert len(ui.store.list())==1
            h.settings.set_appearance(Appearance(favorites=('Bookmarks',),favorites_only=True,floating_enabled=True)); h.apply_appearance()
            h.spotlight.show_panel(); root.update(); assert 'Bookmarks' in dict(h.quick_tools()); h.spotlight.dismiss()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Bookmarks')
            assert not ui.store.unlocked and h.bookmarks_window is None and not h.enabled('Bookmarks')
        finally: root.destroy()
    print('Bookmarks UI smoke: OK (simulated storage and browser)')
if __name__=='__main__': main()
