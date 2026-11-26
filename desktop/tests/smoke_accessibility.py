import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.theme import apply_tree

def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Accessibility'); assert h.accessibility_window is None
            h.toggle_tool('Accessibility'); h.open_tool('Accessibility'); root.update(); ui=h.accessibility_window
            assert 'Accessibility' in dict(h.active_tools())
            ui.source.insert('1.0','Olá\nSegunda linha\nÚltima'); ui.load(); ui.guide.set(True); ui.style(); root.update()
            assert ui.preview.get('1.0','end-1c')=='Olá\nSegunda linha\nÚltima' and ui.preview.cget('state')=='disabled'
            assert ui.position.get()=='Linha 1/3'; ui.move(1); assert ui.position.get()=='Linha 2/3'; assert str(ui.preview.tag_ranges('guide')[0])=='2.0'
            ui.size.set(30); ui.palette.set('Alto contraste'); ui.spacious.set(True); ui.style(); root.update()
            assert ui.preview.cget('bg')=='#000000' and ui.preview.cget('fg')=='#FFFFFF' and int(ui.preview.cget('spacing2'))==5
            apply_tree(root,'Escuro'); assert ui.preview.cget('bg')=='#000000'
            assert ui.traverse(ui.preview,1)=='break'; root.update(); assert root.focus_get()!=ui.preview
            ui.source.insert('end','x'*20001); ui.load(); assert 'anterior' in ui.status.get() and ui.reader.lines==3
            ui.reset(); assert ui.size.get()==16 and not ui.guide.get() and ui.reader.lines==3
            with patch('aeris.accessibility_ui.messagebox.askyesno',return_value=False): ui.close()
            assert h.alive(ui)
            with patch('aeris.hub.messagebox.askyesno',return_value=False): h.toggle_tool('Accessibility')
            assert h.enabled('Accessibility') and h.alive(ui)
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.clear_session()
            assert h.accessibility_window is None and not h.alive(ui) and not ui.reader.text
            h.open_tool('Accessibility'); ui=h.accessibility_window; assert not ui.dirty(); h.toggle_tool('Accessibility'); assert not h.alive(ui)
        finally: root.destroy()
    print('Accessibility smoke: OK')
if __name__=='__main__': main()
