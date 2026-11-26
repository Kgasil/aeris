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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Research'); assert h.research_window is None
            h.toggle_tool('Research'); h.open_tool('Research'); ui=h.research_window; root.update()
            assert 'Research' in dict(h.active_tools())
            ui.title.set('Automação'); ui.project.set('Ciência'); ui.notes.insert('1.0','Dados úteis'); ui.save()
            r=ui.store.list()[0]; assert not ui.dirty() and dict(inventory(h)[2])['research']==1
            ui.state.set('Consultada'); ui.save(); assert ui.store.get(r.id).state=='Consultada'
            ui.query.set('automacao uteis'); ui.project_filter.set('CIENCIA'); ui.render(); assert ui.tree.get_children()==(str(r.id),)
            with patch('aeris.research_ui.messagebox.showinfo') as dialog: ui.preview(); assert '[Ano não informado]' in dialog.call_args.args[1]
            ui.title.set('Rascunho')
            with patch('aeris.research_ui.messagebox.askyesno',return_value=False): ui.close(); ui.new()
            assert h.alive(ui) and ui.title.get()=='Rascunho'
            with patch('aeris.research_ui.messagebox.askyesno',return_value=True): ui.close()
            h.open_tool('Research'); ui=h.research_window; ui.tree.selection_set(str(r.id)); ui.load_selected(); assert ui.title.get()=='Automação'
            with patch('aeris.research_ui.messagebox.askyesno',return_value=False): ui.delete()
            assert ui.store.list()
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Research')
            assert h.enabled('Research') and h.alive(ui)
            store=ui.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Research')
            assert not h.enabled('Research') and h.research_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Research'); h.open_tool('Research'); ui=h.research_window; ui.title.set('Nova'); ui.save()
            with patch('aeris.research_ui.messagebox.askyesno',return_value=True): ui.delete()
            assert not ui.store.list(); ui.title.set('Outra'); ui.save()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.research_store is None and not ui.store.list() and not h.alive(ui)
        finally: root.destroy()
    print('Research smoke: OK')
if __name__=='__main__': main()
