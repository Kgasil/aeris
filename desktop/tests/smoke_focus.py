import tkinter as tk
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.focus import MODES


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.open_tool('Focus'); assert h.focus_window is None
            h.toggle_tool('Focus'); h.open_tool('Focus'); ui=h.focus_window; t=ui.model
            assert 'Focus' in dict(h.active_tools()) and ui.callback is None and not ui.sound.get()
            now=[100.0]; t.clock=lambda:now[0]
            ui.minutes.set('0'); ui.start(); assert t.state=='ready' and ui.callback is None
            ui.minutes.set('1'); ui.start(); assert ui.callback is not None and t.state=='running'
            now[0]+=20; ui.pause(); assert ui.callback is None and ui.display.get()=='00:40'
            ui.start(); now[0]+=10; ui.window.destroy(); assert ui.callback is None and t.state=='paused' and t.seconds==30
            h.open_tool('Focus'); ui=h.focus_window; assert ui.model is t and ui.display.get()=='00:30'
            ui.start(); now[0]+=30
            with patch.object(ui.window,'bell') as bell:
                ui.update_timer(); assert t.state=='finished' and ui.callback is None; bell.assert_not_called()
                ui.mode.set(MODES[1]); ui.mode_changed(); ui.minutes.set('1'); ui.sound.set(True); ui.start(); now[0]+=60
                ui.update_timer(); ui.update_timer(); bell.assert_called_once()
            assert t.completed=={MODES[0]:1,MODES[1]:1}
            ui.start(); h.toggle_tool('Focus'); assert ui.callback is None and h.focus_timer is None and not h.alive(ui)
            h.toggle_tool('Focus'); h.open_tool('Focus'); ui=h.focus_window; ui.start()
            with patch('aeris.hub.messagebox.askyesno',return_value=True): assert h.clear_session()
            assert ui.callback is None and h.focus_timer is None and h.focus_window is None
        finally: root.destroy()
    print('Focus smoke: OK')

if __name__=='__main__': main()
