import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import PLAY_PRONOUNCE, PLAY_VOICE
from tests.smoke_voice import FakeProcess


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk()
        try:
            h=Hub(root,Settings(Path(d)/'settings.json')); h.toggle_tool('Pronounce'); h.open_tool('Pronounce'); root.update()
            ui=h.pronounce_window; assert 'Pronounce' in dict(h.quick_tools())
            ui.exercise.set('Good morning!'); ui.fill_exercise()
            fake=FakeProcess()
            with patch('aeris.voice_ui.start_process',return_value=fake) as launch:
                h.permissions.set(PLAY_VOICE,True); ui.play(); launch.assert_not_called()
                h.permissions.set(PLAY_PRONOUNCE,True); ui.play(); launch.assert_not_called()
                ui.set_voices(('Test voice',)); ui.repeat.set(3); ui.play(); launch.assert_called_once()
                assert ui.process is fake
                h.permissions.set(PLAY_PRONOUNCE,False); assert fake.killed.is_set() and ui.process is None
                assert h.permissions.allowed(PLAY_VOICE)
            ui.language.set('Español'); ui.language_changed(); assert not ui.voices and '¡Buenos días!' in ui.exercise_choice.cget('values')
            with patch('aeris.hub.messagebox.askyesno',return_value=True): h.toggle_tool('Pronounce')
            assert h.pronounce_window is None and not h.permissions.allowed(PLAY_PRONOUNCE)
        finally: root.destroy()
    print('Pronounce UI smoke: OK')
if __name__=='__main__': main()
