"""Focus countdown; one Tk callback only while running, no background service."""
import tkinter as tk
from tkinter import ttk
from aeris.focus import MODES


class FocusWindow:
    def __init__(self, hub):
        self.hub = hub
        self.model = hub.focus_timer
        self.callback = None
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Focus')
        self.window.geometry('460x490'); self.window.minsize(370,460)
        self.window.protocol('WM_DELETE_WINDOW', self.window.destroy)
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        self.window.bind('<Destroy>', self.destroyed, add='+')
        f = ttk.Frame(self.window, padding=18); f.pack(fill='both', expand=True)
        ttk.Label(f, text='Aeris Focus', font=('Segoe UI', 18)).pack(anchor='w')
        ttk.Label(f, text='Concentre-se no que importa. Nenhuma atividade é monitorada.', wraplength=330).pack(anchor='w', pady=(0,8))
        self.mode = tk.StringVar(self.window, self.model.mode)
        self.mode_box = ttk.Combobox(f, textvariable=self.mode, values=MODES, state='readonly')
        self.mode_box.pack(fill='x'); self.mode_box.bind('<<ComboboxSelected>>', self.mode_changed)
        duration = ttk.Frame(f); duration.pack(fill='x', pady=5)
        ttk.Label(duration, text='Duração (1–120 min)').pack(side='left')
        self.minutes = tk.StringVar(self.window, str(self.model.minutes))
        self.duration_box = ttk.Spinbox(duration, from_=1, to=120, textvariable=self.minutes, width=6)
        self.duration_box.pack(side='right')
        presets=ttk.Frame(f); presets.pack(fill='x')
        self.preset_buttons=[]
        for label, mode, minutes in [('25 min', MODES[0],25),('50 min', MODES[0],50),('5 min pausa', MODES[1],5)]:
            button=ttk.Button(presets,text=label,command=lambda m=mode,n=minutes:self.preset(m,n))
            button.pack(side='left',fill='x',expand=True,padx=2)
            self.preset_buttons.append(button)
        self.display = tk.StringVar(self.window)
        ttk.Label(f, textvariable=self.display, font=('Segoe UI', 42), anchor='center').pack(fill='x', pady=8)
        self.progress = ttk.Progressbar(f, maximum=100, mode='determinate'); self.progress.pack(fill='x')
        self.status = tk.StringVar(self.window)
        ttk.Label(f, textvariable=self.status, wraplength=330).pack(pady=5)
        buttons = ttk.Frame(f); buttons.pack(fill='x')
        self.start_button = ttk.Button(buttons, command=self.start); self.start_button.pack(side='left', fill='x', expand=True)
        self.pause_button = ttk.Button(buttons, text='Pausar', command=self.pause); self.pause_button.pack(side='left', fill='x', expand=True, padx=3)
        ttk.Button(buttons, text='Reiniciar', command=self.reset).pack(side='left', fill='x', expand=True)
        self.sound = tk.BooleanVar(self.window, False)
        ttk.Checkbutton(f, text='Sinal sonoro ao concluir (opcional)', variable=self.sound).pack(anchor='w', pady=8)
        self.stats = tk.StringVar(self.window)
        ttk.Label(f, textvariable=self.stats, wraplength=330).pack(anchor='w')
        ttk.Label(f, text='Ao fechar esta janela, a contagem pausa. Sessões não são gravadas em disco.', wraplength=330).pack(anchor='w', pady=(8,0))
        self.render()

    def preset(self, mode, minutes):
        if self.model.state not in ('ready','finished'):
            return
        self.model.configure(mode,minutes)
        self.mode.set(mode); self.minutes.set(str(minutes)); self.render()

    def mode_changed(self, _=None):
        self.minutes.set('25' if self.mode.get() == MODES[0] else '5')
        try:
            self.model.configure(self.mode.get(), int(self.minutes.get()))
        except ValueError:
            return
        self.render()

    def render(self):
        m = self.model
        mins, secs = divmod(m.seconds, 60)
        self.display.set(f'{mins:02d}:{secs:02d}')
        self.progress['value'] = 100 * (1 - m.remaining / (m.minutes * 60))
        editable = m.state in ('ready', 'finished')
        self.mode_box.configure(state='readonly' if editable else 'disabled')
        self.duration_box.configure(state='normal' if editable else 'disabled')
        for button in self.preset_buttons:
            button.configure(state='normal' if editable else 'disabled')
        self.start_button.configure(text='Retomar' if m.state == 'paused' else 'Iniciar', state='disabled' if m.state == 'running' else 'normal')
        self.pause_button.configure(state='normal' if m.state == 'running' else 'disabled')
        self.stats.set(f"Concentrações concluídas: {m.completed[MODES[0]]}  |  Intervalos: {m.completed[MODES[1]]}")
        self.status.set({'ready':'Pronto para iniciar.', 'running':'Sessão em andamento.', 'paused':'Pausado.', 'finished':'Tempo concluído! Escolha a próxima sessão.'}[m.state])

    def start(self):
        if self.model.state in ('ready', 'finished'):
            try:
                self.model.configure(self.mode.get(), int(self.minutes.get()))
            except ValueError:
                self.status.set('Informe um número inteiro entre 1 e 120.'); return
        self.model.start()
        self.update_timer()

    def cancel_callback(self):
        if self.callback is not None:
            self.window.after_cancel(self.callback); self.callback = None

    def update_timer(self):
        self.cancel_callback()
        finished = self.model.tick()
        self.render()
        if finished and self.sound.get():
            self.window.bell()
        if self.model.state == 'running':
            self.callback = self.window.after(250, self.update_timer)

    def pause(self):
        self.cancel_callback()
        finished = self.model.pause()
        self.render()
        if finished and self.sound.get(): self.window.bell()

    def reset(self):
        self.cancel_callback(); self.model.reset()
        self.mode.set(self.model.mode); self.minutes.set(str(self.model.minutes)); self.render()

    def destroyed(self, event):
        if event.widget is self.window:
            self.cancel_callback(); self.model.pause()
