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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Checklist'); assert h.checklist_window is None
            h.toggle_tool('Checklist'); h.open_tool('Checklist'); ui=h.checklist_window
            assert 'Checklist' in dict(h.active_tools())
            ui.list_name.set('Trabalho'); ui.create(); ui.title.set('Relatório'); ui.priority.set('Alta'); ui.add()
            task=ui.store.tasks('Trabalho')[0]; ui.tree.selection_set(str(task.id)); ui.select_task(); assert ui.title.get()=='Relatório'
            ui.title.set('Relatório final'); ui.edit(); assert ui.store.tasks('Trabalho')[0].title=='Relatório final'
            ui.tree.selection_set(str(task.id)); ui.toggle(); assert ui.stats.get()=='1 de 1 concluídas'
            ui.filter.set('Pendentes'); ui.render(); assert not ui.tree.get_children()
            ui.filter.set('Todas'); ui.render(); assert ui.tree.get_children()
            assert dict(inventory(h)[2])['checklist']==1
            ui.window.destroy(); h.open_tool('Checklist'); ui=h.checklist_window; assert ui.stats.get()=='1 de 1 concluídas'
            ui.list_name.set('Projetos'); ui.rename(); assert ui.store.names()==('Projetos',)
            with patch('aeris.checklist_ui.messagebox.askyesno',return_value=False): ui.delete_list()
            assert ui.store.names()==('Projetos',)
            with patch('aeris.checklist_ui.messagebox.askyesno',return_value=True): ui.delete_list()
            assert not ui.store.names()
            ui.list_name.set('Estudos'); ui.create(); ui.title.set('Python'); ui.add(); store=ui.store
            h.toggle_tool('Checklist'); assert not h.alive(ui) and h.checklist_store is None and not store.list()
            h.toggle_tool('Checklist'); h.open_tool('Checklist'); ui=h.checklist_window; ui.list_name.set('Nova'); ui.create(); ui.title.set('Tarefa'); ui.add()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.checklist_store is None and not ui.store.list() and not h.alive(ui)
        finally: root.destroy()
    print('Checklist smoke: OK')

if __name__=='__main__': main()
