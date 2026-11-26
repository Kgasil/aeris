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
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Flashcards'); assert h.flashcards_window is None
            h.toggle_tool('Flashcards'); h.open_tool('Flashcards'); ui=h.flashcards_window; root.update()
            assert 'Flashcards' in dict(h.active_tools())
            ui.deck.set('Ciência'); ui.question.insert('1.0','Automação?'); ui.answer.insert('1.0','Resposta secreta'); ui.save(); c=ui.store.list()[0]
            assert not ui.dirty() and dict(inventory(h)[2])['flashcards']==1
            ui.deck_filter.set('CIENCIA'); ui.query.set('automacao'); ui.render(); assert ui.tree.get_children()==(str(c.id),)
            ui.start_review(); assert 'Resposta secreta' not in ui.review_text.get('1.0','end'); ui.rate('Fácil'); assert ui.store.get(c.id).reviews==0
            ui.reveal(); assert 'Resposta secreta' in ui.review_text.get('1.0','end'); ui.rate('Médio'); assert ui.store.get(c.id).reviews==1
            ui.start_review(); assert ui.review_id is None
            ui.question.insert('end',' rascunho')
            with patch('aeris.flashcards_ui.messagebox.askyesno',return_value=False): ui.close(); ui.new()
            assert h.alive(ui) and ui.dirty()
            with patch('aeris.flashcards_ui.messagebox.askyesno',return_value=True): ui.close()
            h.open_tool('Flashcards'); ui=h.flashcards_window; assert ui.store.get(c.id).reviews==1
            ui.tree.selection_set(str(c.id)); ui.load_selected(); assert not ui.dirty()
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Flashcards')
            assert h.enabled('Flashcards') and h.alive(ui)
            store=ui.store
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Flashcards')
            assert not h.enabled('Flashcards') and h.flashcards_store is None and not store.list() and not h.alive(ui)
            h.toggle_tool('Flashcards'); h.open_tool('Flashcards'); ui=h.flashcards_window; ui.question.insert('1.0','Q'); ui.answer.insert('1.0','A'); ui.save()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert h.flashcards_store is None and not ui.store.list() and not h.alive(ui)
        finally: root.destroy()
    print('Flashcards smoke: OK')
if __name__=='__main__': main()
