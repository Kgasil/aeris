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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Interview'); assert h.interview_window is None
            h.toggle_tool('Interview'); h.open_tool('Interview'); u=h.interview_window; root.update()
            assert 'Interview' in dict(h.active_tools()); assert not u.dirty()
            u.answer.insert('1.0','Minha trajetória'); u.checks[0].set(True)
            with patch('aeris.interview_ui.messagebox.askyesno',return_value=False): u.move(1)
            assert u.index==0 and u.dirty()
            u.save(); assert not u.dirty(); assert dict(inventory(h)[2])['interview']==1
            u.move(1); assert u.index==1 and not u.dirty(); u.reveal(); assert u.hint.get()
            u.move(-1); assert u.values()[0]=='Minha trajetória' and u.checks[0].get()
            u.answer.insert('end','!'); u.area.set('Dados e BI')
            with patch('aeris.interview_ui.messagebox.askyesno',return_value=False): u.change_area()
            assert u.area.get()=='Comportamental' and u.dirty()
            u.save(); u.area.set('Dados e BI'); u.change_area(); assert u.current().id=='d1' and not u.dirty()
            u.close(); h.open_tool('Interview'); u=h.interview_window; assert u.values()[0]=='Minha trajetória!'
            store=u.store
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Interview')
            assert h.enabled('Interview') and store.list()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not store.list() and not h.alive(u)
            h.open_tool('Interview'); u=h.interview_window; u.answer.insert('1.0','Teste'); u.save(); store=u.store
            with patch('aeris.interview_ui.messagebox.askyesno',return_value=True): u.delete()
            assert not store.list() and not u.dirty()
            u.answer.insert('1.0','Outro'); u.save()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Interview')
            assert not h.enabled('Interview') and not store.list()
        finally: root.destroy()
    print('Interview smoke: OK')
if __name__=='__main__': main()
