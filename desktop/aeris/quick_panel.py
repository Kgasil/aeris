"""Painel sob demanda relativo ao Hub, sem integração global com o sistema."""
import tkinter as tk
from tkinter import ttk
from aeris.settings import SIZES

def panel_bounds(corner, size, host, screen):
    """Calcula posição relativa ao Hub, limitada à tela primária do protótipo."""
    x, y, hw, hh = host
    sw, sh = screen
    w, h = min(size[0], sw), min(size[1], sh)
    px = x + hw - w if corner.endswith('direito') else x
    py = y + hh - h if corner.startswith('Inferior') else y
    return w, h, max(0, min(px, sw-w)), max(0, min(py, sh-h))

class QuickPanel:
    def __init__(self, hub):
        self.hub = hub
        root = hub.root
        prefs = hub.settings.appearance
        root.update_idletasks()
        self.window = tk.Toplevel(root)
        self.window.title('Aeris · acesso rápido')
        self.window.transient(root)
        self.window.configure(bg='#F6FAF7')
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        self.window.protocol('WM_DELETE_WINDOW', self.window.destroy)
        w, h, x, y = panel_bounds(prefs.corner, SIZES[prefs.panel_size],
                                  (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()),
                                  (root.winfo_screenwidth(), root.winfo_screenheight()))
        self.window.geometry(f'{w}x{h}+{x}+{y}')
        try:
            self.window.attributes('-alpha', prefs.opacity / 100)
        except tk.TclError:
            pass  # Alguns gerenciadores não oferecem transparência.
        self.window.minsize(min(w, 240), min(h, 200))
        frame = ttk.Frame(self.window, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='aeris.', font=('Segoe UI', 20)).pack(anchor='w')
        ttk.Label(frame, text='Acesso rápido · ferramentas ativas').pack(anchor='w', pady=(0, 12))
        if hub.settings.capture_enabled:
            ttk.Button(frame, text='Capture', command=self.open_capture).pack(fill='x', pady=4)
        if hub.settings.snippets_enabled:
            ttk.Button(frame, text='Snippets', command=self.open_snippets).pack(fill='x', pady=4)
        if not (hub.settings.capture_enabled or hub.settings.snippets_enabled):
            ttk.Label(frame, text='Ative Capture ou Snippets no Hub para usar aqui.', wraplength=max(140,w-45)).pack(anchor='w')
        ttk.Button(frame, text='Voltar ao Hub', command=self.window.destroy).pack(fill='x', pady=4)
        ttk.Button(frame, text='Configurações', command=self.open_settings).pack(fill='x', pady=4)

    def open_capture(self):
        self.window.destroy()
        self.hub.open_capture()

    def open_snippets(self):
        self.window.destroy()
        self.hub.open_snippets()

    def open_settings(self):
        self.window.destroy()
        self.hub.open_appearance()
