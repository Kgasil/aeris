"""Editor de aparência com prévia local. Ícone global ainda não implementado."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.settings import Appearance, CORNERS, SIZES

class AppearanceWindow:
    def __init__(self, hub):
        self.hub = hub
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris · Aparência')
        self.window.transient(hub.root)
        self.window.geometry('540x610')
        self.window.minsize(420, 570)
        self.window.bind('<Escape>', lambda _: self.close())
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        prefs = hub.settings.appearance
        self.corner = tk.StringVar(self.window, prefs.corner)
        self.icon = tk.IntVar(self.window, prefs.icon_size)
        self.panel = tk.StringVar(self.window, prefs.panel_size)
        self.opacity = tk.IntVar(self.window, prefs.opacity)
        self.enabled = tk.BooleanVar(self.window, prefs.quick_enabled)
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Seu Aeris, do seu jeito.', font=('Segoe UI', 18)).pack(anchor='w')
        ttk.Checkbutton(frame, text='Disponibilizar painel rápido no Hub', variable=self.enabled).pack(anchor='w', pady=8)
        for label, variable, values in [('Posição relativa ao Hub', self.corner, CORNERS), ('Tamanho inicial do painel', self.panel, tuple(SIZES))]:
            ttk.Label(frame, text=label).pack(anchor='w', pady=(5, 2))
            ttk.Combobox(frame, textvariable=variable, values=values, state='readonly').pack(fill='x')
        for label, variable, low, high in [('Tamanho do futuro ícone (px) · prévia', self.icon, 24, 64), ('Opacidade do painel (%)', self.opacity, 80, 100)]:
            ttk.Label(frame, text=label).pack(anchor='w', pady=(6, 0))
            tk.Scale(frame, from_=low, to=high, orient='horizontal', variable=variable, resolution=1, highlightthickness=0).pack(fill='x')
        ttk.Label(frame, text='Pré-visualização · ícone global ainda indisponível').pack(anchor='w', pady=(6, 2))
        self.canvas = tk.Canvas(frame, height=145, bg='#E7F0EA', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self.preview)
        for variable in (self.corner, self.icon, self.panel, self.opacity, self.enabled):
            variable.trace_add('write', self.preview)
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=(10, 0))
        ttk.Button(buttons, text='Restaurar padrões', command=self.reset).pack(side='left')
        ttk.Button(buttons, text='Cancelar', command=self.close).pack(side='right')
        ttk.Button(buttons, text='Salvar', command=self.save).pack(side='right', padx=6)
        self.preview()

    def values(self):
        return Appearance(self.corner.get(), self.icon.get(), self.panel.get(), self.opacity.get(), self.enabled.get())

    def preview(self, *_):
        c = self.canvas
        c.delete('all')
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        c.create_rectangle(12, 12, w-12, h-12, fill='#FFFFFF', outline='#CFDFD5')
        for y in range(25, h-20, 14):
            c.create_line(25, y, w*0.55, y, fill='#CFDFD5', width=2)
        if not self.enabled.get():
            return
        corner = self.corner.get()
        right, bottom = corner.endswith('direito'), corner.startswith('Inferior')
        r = self.icon.get()/3
        cx = w-20-r if right else 20+r
        cy = h-20-r if bottom else 20+r
        panel_w, panel_h = SIZES[self.panel.get()]
        pw, ph = min(w*0.45, panel_w*0.33), min(h-28, panel_h*0.24)
        x = w-20-pw if right else 20
        y = max(14, cy-r-ph-5) if bottom else min(h-ph-14, cy+r+5)
        a = self.opacity.get()/100
        # Aproxima a transparência sobre o fundo da prévia.
        color = '#'+''.join(f'{round(a*v+(1-a)*b):02x}' for v,b in zip((246,250,247),(207,223,213)))
        c.create_rectangle(x,y,x+pw,y+ph,fill=color,outline='#508D70')
        c.create_text(x+8,y+12,text='aeris.',anchor='w',fill='#285640')
        c.create_oval(cx-r,cy-r,cx+r,cy+r,fill='#285640',outline='')
        for dy in (-0.36,0,0.36):
            c.create_line(cx-r*.58,cy+r*dy,cx,cy+r*(dy-.25),cx+r*.58,cy+r*dy,fill='#DCEFE3',smooth=True,width=2)

    def reset(self):
        defaults = Appearance()
        self.corner.set(defaults.corner)
        self.icon.set(defaults.icon_size)
        self.panel.set(defaults.panel_size)
        self.opacity.set(defaults.opacity)
        self.enabled.set(defaults.quick_enabled)

    def close(self):
        if self.values() != self.hub.settings.appearance and not messagebox.askyesno('Descartar?', 'Descartar alterações de aparência?', parent=self.window):
            return
        self.window.destroy()

    def save(self):
        try:
            self.hub.settings.set_appearance(self.values())
        except (OSError, ValueError) as exc:
            messagebox.showerror('Aeris', f'Não foi possível salvar as preferências: {type(exc).__name__}', parent=self.window)
            return
        self.hub.apply_appearance()
        self.window.destroy()
