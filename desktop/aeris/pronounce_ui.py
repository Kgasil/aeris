"""Pronunciation practice, no microphone, scores or recordings."""
import tkinter as tk
from tkinter import ttk
from aeris.voice_ui import VoiceWindow
from aeris.permissions import PLAY_PRONOUNCE
from aeris.pronounce import LANGUAGES, EXERCISES, practice_payload
from aeris.window_lifecycle import trace_window

class PronounceWindow(VoiceWindow):
    capability=PLAY_PRONOUNCE
    tool_name='Pronounce'
    description='Ouça e repita palavras e frases. Sem microfone ou avaliação da fala.'

    def __init__(self,hub):
        super().__init__(hub)
        self.window.geometry('520x610'); self.window.minsize(450,570)
        self.language=tk.StringVar(self.window,'English')
        self.repeat=tk.IntVar(self.window,2); self.rate.set(-2)
        self.voice.set('Selecione uma voz do idioma'); self.choice.configure(values=())
        controls=ttk.Frame(self.frame); controls.pack(fill='x',before=self.text,pady=5)
        ttk.Label(controls,text='Idioma do exercício').pack(anchor='w')
        lang=ttk.Combobox(controls,textvariable=self.language,values=tuple(LANGUAGES),state='readonly'); lang.pack(fill='x')
        self.exercise=tk.StringVar(self.window,'')
        self.exercise_choice=ttk.Combobox(controls,textvariable=self.exercise,values=EXERCISES['en'],state='readonly'); self.exercise_choice.pack(fill='x',pady=4)
        self.exercise_choice.bind('<<ComboboxSelected>>',self.fill_exercise)
        ttk.Label(controls,text='Repetições (1–5) · pausa de 0,7 s').pack(anchor='w')
        ttk.Spinbox(controls,from_=1,to=5,textvariable=self.repeat,state='readonly',width=5).pack(anchor='w')
        self.list_button.configure(text='Listar vozes do idioma')
        self.play_button.configure(text='Ouvir exercício')
        trace_window(self.window,self.language,self.language_changed)
        self.permissions_changed()

    def language_changed(self,*_):
        self.stop(); self.voices=(); self.choice.configure(values=()); self.voice.set('Selecione uma voz do idioma')
        self.exercise.set(''); self.exercise_choice.configure(values=EXERCISES[LANGUAGES[self.language.get()]])
        self.status.set('Texto preservado. Selecione uma frase ou revise o idioma do texto; liste as vozes.')
        self.permissions_changed()

    def fill_exercise(self,event=None):
        self.stop(); self.text.delete('1.0','end'); self.text.insert('1.0',self.exercise.get())

    def list_voices(self):
        if self.hub.permissions.allowed(self.capability) and self.process is None:
            self.start({'action':'list','language':LANGUAGES[self.language.get()]})

    def set_voices(self,data):
        selected=self.voice.get()
        self.voices=data; self.choice.configure(values=data)
        self.voice.set(selected if selected in data else data[0] if data else 'Nenhuma voz compatível')
        self.status.set(f'{len(data)} vozes encontradas. Se necessário, instale uma voz no Windows.')

    def play(self):
        if not self.hub.permissions.allowed(self.capability) or self.process is not None: return
        if self.voice.get() not in self.voices:
            self.status.set('Liste e selecione uma voz compatível com o idioma.'); return
        try: payload=practice_payload(self.text.get('1.0','end-1c'),LANGUAGES[self.language.get()],self.voice.get(),self.rate.get(),self.volume.get(),self.repeat.get())
        except (ValueError,tk.TclError) as exc: self.status.set(str(exc)); return
        self.start(payload)
