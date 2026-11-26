import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.privacy import inventory


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Ideas'); assert h.ideas_window is None
            h.toggle_tool('Ideas'); h.open_tool('Ideas'); ui=h.ideas_window
            assert 'Ideas' in dict(h.active_tools())
            ui.title.set('Automação'); ui.category.set('Tecnologia'); ui.body.insert('1.0','Relatório mensal'); ui.save()
            item=ui.store.list()[0]; assert not ui.dirty() and dict(inventory(h)[2])['ideas']==1
            ui.state.set('Em desenvolvimento'); ui.save(); assert ui.store.get(item.id).status=='Em desenvolvimento'
            ui.query.set('automacao relatorio'); ui.render(); assert ui.tree.get_children()==(str(item.id),)
            ui.filter.set('Arquivada'); ui.render(); assert not ui.tree.get_children()
            ui.title.set('Rascunho')
            with patch('aeris.ideas_ui.messagebox.askyesno',return_value=False): ui.close(); ui.new()
            assert h.alive(ui) and ui.title.get()=='Rascunho'
            with patch('aeris.ideas_ui.messagebox.askyesno',return_value=True): ui.close()
            h.open_tool('Ideas'); ui=h.ideas_window; ui.tree.selection_set(str(item.id)); ui.load_selected(); assert ui.title.get()=='Automação'
            with patch('aeris.ideas_ui.messagebox.askyesno',return_value=False): ui.delete()
            assert ui.store.list()
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Ideas')
            assert h.enabled('Ideas') and h.alive(ui)
            store=ui.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Ideas')
            assert not h.enabled('Ideas') and h.ideas_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Ideas'); h.open_tool('Ideas'); ui=h.ideas_window; ui.title.set('Nova'); ui.save()
            with patch('aeris.ideas_ui.messagebox.askyesno',return_value=True): ui.delete()
            assert not ui.store.list(); ui.title.set('Outra'); ui.save()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.ideas_store is None and not ui.store.list() and not h.alive(ui)
        finally: root.destroy()
    print('Ideas smoke: OK')

if __name__=='__main__': main()
