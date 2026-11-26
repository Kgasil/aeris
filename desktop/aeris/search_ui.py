"""Janela compacta sob demanda; sem indexação permanente ou histórico."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk
from aeris.permissions import SEARCH_CAPTURE, SEARCH_SNIPPETS
from aeris.search import search
from aeris.quick_panel import panel_bounds
from aeris.settings import SIZES

class SearchWindow:
    def __init__(self, hub):
        self.hub = hub
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Search')
        self.window.bind('<Escape>', lambda _: self.window.destroy())
        self.window.protocol('WM_DELETE_WINDOW', self.window.destroy)
        prefs = hub.settings.appearance
        root = hub.root
        root.update_idletasks()
        width, height = SIZES[prefs.panel_size]
        w,h,x,y = panel_bounds(prefs.corner, (max(380,width), max(400,height)),
                                (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()),
                                (root.winfo_screenwidth(), root.winfo_screenheight()))
        self.window.geometry(f'{w}x{h}+{x}+{y}')
        self.window.minsize(min(330,w), min(350,h))
        try:
            self.window.attributes('-alpha', prefs.opacity / 100)
        except tk.TclError:
            pass
        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Aeris Search', font=('Segoe UI', 18)).pack(anchor='w')
        self.query = tk.StringVar(self.window)
        self.entry = ttk.Entry(frame, textvariable=self.query)
        self.entry.pack(fill='x', pady=6)
        ttk.Button(frame,text='Limpar busca',command=self.clear_query).pack(anchor='w')
        self.entry.bind('<Return>',self.focus_results)
        self.sources = {}
        self.checks = {}
        self.capabilities = {'Capture': SEARCH_CAPTURE, 'Snippets': SEARCH_SNIPPETS}
        for name, available in [('Ferramentas', True), ('Capture', hub.settings.capture_enabled), ('Snippets', hub.settings.snippets_enabled)]:
            var = tk.BooleanVar(self.window, name == 'Ferramentas')
            self.sources[name] = var
            check = ttk.Checkbutton(frame, text=name, variable=var, command=self.refresh)
            check.pack(anchor='w')
            self.checks[name] = check
            if not available:
                check.state(['disabled'])
        ttk.Button(frame, text='Gerenciar acesso às fontes', command=hub.open_permissions).pack(anchor='w')
        self.status = tk.StringVar(self.window)
        ttk.Label(frame, textvariable=self.status).pack(anchor='w', pady=4)
        listing = ttk.Frame(frame)
        listing.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(listing)
        scroll.pack(side='right', fill='y')
        self.items = tk.Listbox(listing, height=5, exportselection=False, yscrollcommand=scroll.set)
        self.items.pack(fill='both', expand=True)
        scroll.configure(command=self.items.yview)
        self.items.bind('<<ListboxSelect>>', self.preview)
        self.items.bind('<Double-Button-1>', self.open_selected)
        self.items.bind('<Return>', self.open_selected)
        self.detail = tk.Text(frame, height=4, wrap='word', state='disabled', exportselection=False)
        self.detail.pack(fill='x', pady=6)
        self.button = ttk.Button(frame, text='Abrir resultado', command=self.open_selected)
        self.button.pack(fill='x')
        trace_window(self.window, self.query, self.refresh)
        self.window.bind('<FocusIn>', self.on_focus)
        self.refresh()
        self.entry.focus_set()

    def clear_query(self):
        self.query.set(''); self.entry.focus_set()
    def focus_results(self,_=None):
        if self.results:
            self.items.focus_set()
            if not self.items.curselection(): self.items.selection_set(0)
            self.preview()
        return 'break'
    def selected(self):
        selection=self.items.curselection()
        return self.results[selection[0]] if selection and selection[0]<len(self.results) else None
    def on_focus(self, event):
        if event.widget is self.window:
            self.refresh()

    def refresh(self, *_):
        hub = self.hub
        selected=self.selected() if hasattr(self,'results') else None
        allowed = {'Ferramentas'}
        for name, capability in self.capabilities.items():
            if hub.enabled(name) and hub.permissions.allowed(capability):
                allowed.add(name); self.checks[name].state(['!disabled'])
            else:
                self.sources[name].set(False); self.checks[name].state(['disabled'])
        sources = {name for name, var in self.sources.items() if var.get() and name in allowed}
        notes = hub.capture_store.list() if 'Capture' in sources and hub.settings.capture_enabled and hub.capture_store else ()
        snippets = hub.snippets_store.list() if 'Snippets' in sources and hub.settings.snippets_enabled and hub.snippets_store else ()
        self.results = search(self.query.get(), sources, hub.modules, notes, snippets)
        self.items.delete(0, 'end')
        for result in self.results:
            self.items.insert('end', f'{result.title} · {result.source}')
        if selected in self.results:
            index=self.results.index(selected); self.items.selection_set(index); self.items.see(index)
        self.status.set(f'{len(self.results)} resultado(s)' if self.query.get().strip() else 'Digite um termo para pesquisar.')
        self.preview()

    def preview(self, _=None):
        result=self.selected()
        self.detail.configure(state='normal')
        self.detail.delete('1.0', 'end')
        if result is not None:
            self.detail.insert('1.0', result.body[:800] + ('…' if len(result.body)>800 else ''))
        self.detail.configure(state='disabled')
        self.button.configure(state='normal' if result is not None else 'disabled')

    def open_selected(self, _=None):
        result=self.selected()
        if result is None: return 'break'
        self.refresh()
        if self.selected()!=result:
            self.status.set('Resultado alterado. Pesquise novamente.'); return 'break'
        if self.hub.open_search_result(result):
            if self.window.winfo_exists(): self.window.destroy()
        elif self.window.winfo_exists():
            self.refresh(); self.status.set('Resultado indisponível ou abertura cancelada.')
        return 'break'
