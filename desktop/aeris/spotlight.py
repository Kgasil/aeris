"""Optional, event-driven launcher. No global mouse/keyboard hooks."""
import sys
import tkinter as tk
from tkinter import ttk
from aeris.scroll_area import scroll_area
from aeris.settings import SIZES
from aeris.theme import apply_tree


def work_area(root):
    """Primary monitor work area (Windows excludes taskbar); fallback is screen."""
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def anchor(corner, size, area, margin=12):
    l, t, r, b = area
    w = min(size[0], max(1, r-l))
    h = min(size[1], max(1, b-t))
    x = r-w-margin if corner.endswith('direito') else l+margin
    y = b-h-margin if corner.startswith('Inferior') else t+margin
    return w, h, max(l, min(x, r-w)), max(t, min(y, b-h))


def adjacent(corner, size, icon, area, gap=8):
    l, t, r, b = area
    iw, ih, ix, iy = icon
    w, h = min(size[0], max(1,r-l)), min(size[1], max(1,b-t))
    x = ix+iw-w if corner.endswith('direito') else ix
    y = iy-h-gap if corner.startswith('Inferior') else iy+ih+gap
    if y < t or y+h > b:
        y = iy+ih+gap if corner.startswith('Inferior') else iy-h-gap
    return w, h, max(l,min(x,r-w)), max(t,min(y,b-h))


def geometry(bounds):
    w,h,x,y = bounds
    # Current implementation is restricted to the primary monitor.
    return f'{w}x{h}+{max(0,x)}+{max(0,y)}'


class Spotlight:
    def __init__(self, hub):
        self.hub = hub
        self.root = hub.root
        self.prefs = hub.settings.appearance
        self.panel = None
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.title('Aeris Spotlight')
        self.window.overrideredirect(True)
        self.window.configure(bg='#285640')
        self.area = work_area(self.root)
        n = self.prefs.icon_size
        self.bounds = anchor(self.prefs.corner, (n,n), self.area)
        self.window.geometry(geometry(self.bounds))
        # Topmost is an explicit opt-in; no automatic fullscreen detection yet.
        self.window.attributes('-topmost', self.prefs.floating_topmost)
        self.button = tk.Canvas(self.window, bg='#285640', highlightthickness=2, highlightbackground='#285640', highlightcolor='#DCEFE3', cursor='hand2', takefocus=True)
        self.button.pack(fill='both', expand=True)
        self.button.bind('<Configure>', self.draw)
        self.button.bind('<ButtonRelease-1>', self.toggle)
        self.button.bind('<Return>', self.toggle)
        self.button.bind('<space>', self.toggle)
        self.button.bind('<Button-3>', self.menu)
        self.button.bind('<Shift-F10>', self.keyboard_menu)
        self.window.bind('<Escape>', self.dismiss)
        self.window.deiconify()

    def draw(self, event):
        c = self.button
        c.delete('all')
        w,h = event.width,event.height
        for dy in (0.30,0.49,0.68):
            c.create_line(w*.18,h*dy,w*.43,h*(dy-.18),w*.62,h*(dy+.13),w*.82,h*(dy-.08),
                          fill='#DCEFE3', width=max(2,w/18), smooth=True, capstyle=tk.ROUND)

    def keyboard_menu(self, _=None):
        from types import SimpleNamespace
        self.menu(SimpleNamespace(x_root=self.window.winfo_rootx(), y_root=self.window.winfo_rooty()))
        return 'break'

    def menu(self, event):
        if hasattr(self, '_menu'):
            self._menu.destroy()
        menu = self._menu = tk.Menu(self.window, tearoff=False)
        menu.add_command(label='Abrir painel', command=self.show_panel)
        menu.add_command(label='Abrir Hub', command=self.show_hub)
        menu.add_command(label='Ocultar nesta sessão', command=self.hub.hide_spotlight)
        try:
            menu.tk_popup(event.x_root,event.y_root)
        finally:
            try:
                menu.grab_release()
            except tk.TclError:
                pass  # O comando de ocultar pode destruir o menu.

    def toggle(self, _=None):
        if self.panel is not None and self.panel.winfo_exists():
            self.dismiss()
        else:
            self.show_panel()
        return 'break'

    def dismiss(self, _=None):
        if self.panel is not None and self.panel.winfo_exists():
            self.panel.destroy()
        self.panel = None
        return 'break'

    def dismiss_and_focus(self, _=None):
        self.dismiss()
        if self.window.winfo_exists():
            self.button.focus_set()
        return 'break'

    def show_panel(self):
        self.dismiss()
        p = self.hub.settings.appearance
        self.area = work_area(self.root)
        self.bounds = anchor(p.corner,(p.icon_size,p.icon_size),self.area)
        self.window.geometry(geometry(self.bounds))
        self.panel = tk.Toplevel(self.root)
        self.panel.withdraw()
        self.panel.title('Aeris · Spotlight')
        self.panel.geometry(geometry(adjacent(p.corner,SIZES[p.panel_size],self.bounds,self.area)))
        self.panel.attributes('-topmost',p.floating_topmost)
        try:
            self.panel.attributes('-alpha', p.opacity/100)
        except tk.TclError:
            pass
        self.panel.protocol('WM_DELETE_WINDOW', self.dismiss)
        self.panel.bind('<Escape>',self.dismiss_and_focus)
        frame = ttk.Frame(self.panel,padding=12)
        frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='aeris.',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(frame,text='Ambiente: '+self.hub.workspace_store.active[:30] if getattr(self.hub,'workspace_store',None) and self.hub.workspace_store.active else 'Acesso rápido').pack(anchor='w',pady=(0,4))
        tools = self.hub.quick_tools()
        if len(tools)>3:
            footer=ttk.Frame(frame); footer.pack(side='bottom',fill='x')
        else: footer=frame
        if len(tools)>3:
            tool_frame=scroll_area(frame)
            for col in range(2): tool_frame.columnconfigure(col,weight=1,uniform='tool')
            for i,(name,cmd) in enumerate(tools):
                ttk.Button(tool_frame,text=name,command=lambda action=cmd:self.launch(action)).grid(row=i//2,column=i%2,sticky='ew',padx=2,pady=1)
        else:
            for name,cmd in tools:
                ttk.Button(frame,text=name,command=lambda action=cmd:self.launch(action)).pack(fill='x',pady=2)
        if not tools:
            ttk.Label(frame,text='Nenhuma ferramenta ativa neste painel.').pack(anchor='w')
        ttk.Button(footer,text='Hub / Configurações',command=self.show_hub).pack(fill='x',pady=2)
        ttk.Button(footer,text='Ocultar ícone',command=self.hub.hide_spotlight).pack(fill='x',pady=2)
        apply_tree(self.panel, p.theme)
        self.panel.deiconify()
        self.panel.lift()
        # Explicit opening moves focus to the first available keyboard control.
        def first_button(widget):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    return child
                found = first_button(child)
                if found is not None:
                    return found
            return None
        control = first_button(frame)
        if control is not None:
            control.focus_set()

    def launch(self, action):
        self.dismiss()
        # Abre somente a ferramenta, sem restaurar explicitamente o Hub.
        action()

    def show_hub(self):
        self.dismiss()
        self.root.deiconify()
        self.root.lift()

    def destroy(self):
        self.dismiss()
        if self.window.winfo_exists():
            self.window.destroy()
