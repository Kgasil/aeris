import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import MEETING_COPY
from aeris.privacy import inventory

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Meeting'); assert h.meeting_window is None
            h.toggle_tool('Meeting'); h.open_tool('Meeting'); u=h.meeting_window; root.update(); assert 'Meeting' in dict(h.active_tools()); assert not u.dirty()
            u.title.set('Reunião de projeto'); u.day.set('2026-11-25'); u.agenda.insert('1.0','Indicadores'); u.notes.insert('1.0','Decisão'); u.participants.insert('1.0','Equipe'); u.action_title.set('Revisar'); u.owner.set('Ana'); u.due.set('2026-12-01'); u.add_action(); u.toggle_action(); assert u.actions[0].done
            u.action_title.set('Enviar'); u.save(); assert not u.store.list(); u.add_action(); u.load_action(); u.owner.set('Bruno'); u.action_tree.selection_set('0'); u.edit_action(); assert u.actions[0].owner=='Ana'; u.action_tree.selection_set('1'); u.edit_action(); assert u.actions[1].owner=='Bruno'; u.save(); assert not u.dirty() and dict(inventory(h)[2])['meeting']==1
            u.preview(); root.update(); assert str(u.copy_button['state'])=='disabled'; item=u.store.get(u.selected_id); h.permissions.set(MEETING_COPY,True); assert str(u.copy_button['state'])=='normal'
            root.clipboard_clear(); root.clipboard_append('antes')
            with patch('aeris.meeting_ui.messagebox.askyesno',return_value=False): u.copy(item)
            assert root.clipboard_get()=='antes'
            with patch('aeris.meeting_ui.messagebox.askyesno',return_value=True): u.copy(item)
            assert '[x] Revisar' in root.clipboard_get() and 'Bruno' in root.clipboard_get()
            h.permissions.set(MEETING_COPY,False); assert str(u.copy_button['state'])=='disabled'
            u.title.set('Rascunho'); h.permissions.set(MEETING_COPY,True); u.copy(item); assert 'Rascunho' not in root.clipboard_get()
            with patch('aeris.meeting_ui.messagebox.askyesno',return_value=False): u.close()
            assert h.alive(u)
            with patch('aeris.meeting_ui.messagebox.askyesno',return_value=True): u.close()
            h.open_tool('Meeting'); u=h.meeting_window; u.tree.selection_set(str(item.id)); u.load(); assert u.title.get()=='Reunião de projeto' and len(u.actions)==2
            store=u.store
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Meeting')
            assert h.enabled('Meeting') and store.list()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert not store.list() and not h.alive(u) and not h.permissions.allowed(MEETING_COPY)
            h.open_tool('Meeting'); u=h.meeting_window; u.title.set('Nova'); u.save(); store=u.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Meeting')
            assert not h.enabled('Meeting') and not store.list()
        finally: root.destroy()
    print('Meeting smoke: OK')
if __name__=='__main__': main()
