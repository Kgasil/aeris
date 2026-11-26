import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import INTEGRATION_RUN

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json'))
            for n in ('Learn','Research','Flashcards'):h.toggle_tool(n)
            h.open_tool('Learn');u=h.learn_window;p=u.store.create('Python');t=u.store.add(p.id,'API?',25);u.refresh(p.id);u.tree.selection_set(str(t.id));h.permissions.set(INTEGRATION_RUN,True)
            with patch('aeris.study_integration_ui.simpledialog.askstring',return_value='Interface'),patch('aeris.study_integration_ui.messagebox.askyesno',return_value=False):u.send_topic()
            assert not h.flashcards_store.list()
            with patch('aeris.study_integration_ui.simpledialog.askstring',return_value='Interface'),patch('aeris.study_integration_ui.messagebox.askyesno',return_value=True):u.send_topic()
            assert h.flashcards_store.list()[0].answer=='Interface'
            h.open_tool('Research');r=h.research_window;x=r.store.add('SQL','Estudos','Livro');r.set_editor(x)
            with patch('aeris.study_integration_ui.simpledialog.askinteger',side_effect=[1,45]),patch('aeris.study_integration_ui.messagebox.askyesno',return_value=True):r.send_reference()
            assert u.store.get(p.id).topics[-1].title=='SQL'
            h.permissions.set(INTEGRATION_RUN,False);r.send_reference();assert len(u.store.get(p.id).topics)==2
        finally:root.destroy()
    print('Study integration smoke: OK')
if __name__=='__main__':main()
