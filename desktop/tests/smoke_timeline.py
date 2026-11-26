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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Timeline'); assert h.timeline_window is None
            h.toggle_tool('Timeline'); h.open_tool('Timeline'); ui=h.timeline_window
            assert 'Timeline' in dict(h.active_tools()) and not ui.dirty()
            ui.when.set('2026-11-25 09:00'); ui.title.set('Revisão'); ui.category.set('Trabalho'); ui.body.insert('1.0','Relatório mensal'); ui.save()
            item=ui.store.list()[0]; assert not ui.dirty() and dict(inventory(h)[2])['timeline']==1
            ui.new(); ui.when.set('2026-11-26 10:00'); ui.title.set('Outra tarefa'); ui.save(); assert len(ui.store.list())==2
            ui.query.set('revisao relatorio'); ui.day_from.set('2026-11-25'); ui.day_to.set('2026-11-25'); ui.category_filter.set('trabalho'); ui.render(); assert ui.tree.get_children()==(str(item.id),)
            ui.tree.selection_set(str(item.id)); ui.load_selected(); ui.title.set('Revisão concluída'); ui.save(); assert ui.store.get(item.id).title=='Revisão concluída'
            ui.title.set('Rascunho')
            with patch('aeris.timeline_ui.messagebox.askyesno',return_value=False): ui.close(); ui.new()
            assert h.alive(ui) and ui.title.get()=='Rascunho'
            with patch('aeris.timeline_ui.messagebox.askyesno',return_value=True): ui.close()
            h.open_tool('Timeline'); ui=h.timeline_window; assert len(ui.store.list())==2
            ui.tree.selection_set(str(item.id)); ui.load_selected()
            with patch('aeris.timeline_ui.messagebox.askyesno',return_value=True): ui.delete()
            assert len(ui.store.list())==1
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Timeline')
            assert h.enabled('Timeline') and h.alive(ui)
            store=ui.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Timeline')
            assert not h.enabled('Timeline') and h.timeline_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Timeline'); h.open_tool('Timeline'); ui=h.timeline_window; ui.title.set('Nova'); ui.save()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.timeline_store is None and not ui.store.list() and not h.alive(ui)
            assert dict(inventory(h)[2])['timeline']==0
        finally: root.destroy()
    print('Timeline smoke: OK')

if __name__=='__main__': main()
