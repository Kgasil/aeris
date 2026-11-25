"""Interface gráfica do Hub. Nenhum serviço residente ou acesso à rede."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris import __version__
from aeris.registry import load_catalog, filter_catalog, Module
from aeris.settings import Settings

COLORS = {'air': '#F6FAF7', 'soft': '#DCEFE3', 'natural': '#8FC7A3',
          'forest': '#508D70', 'deep': '#285640', 'muted': '#CFDFD5'}

class Hub:
    def __init__(self, root: tk.Tk, settings=None):
        self.root = root
        self.modules = load_catalog()
        self.settings = settings if settings is not None else Settings()
        self.capture_store = None
        self.capture_window = None
        self.visible: tuple[Module, ...] = ()
        self.query = tk.StringVar(root)
        self.category = tk.StringVar(root, 'Todas')
        root.title(f'Project Aeris | {__version__}')
        root.geometry('1040x650')
        root.minsize(750, 500)
        root.configure(bg=COLORS['air'])
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Aeris.TCombobox', padding=5)
        self.build()
        self.query.trace_add('write', self.refresh)
        self.category.trace_add('write', self.refresh)
        self.refresh()
        root.protocol('WM_DELETE_WINDOW', self.close)
        if self.settings.warning:
            self.root.after_idle(lambda: messagebox.showwarning('Aeris', self.settings.warning, parent=self.root))
        root.bind('<Control-f>', lambda _: self.search.focus_set())

    def label(self, parent, text='', size=11, bg='air', fg='deep', **kwargs):
        return tk.Label(parent, text=text, font=('Segoe UI', size), bg=COLORS[bg],
                        fg=COLORS[fg], anchor='w', **kwargs)

    def build(self):
        side = tk.Frame(self.root, bg=COLORS['soft'], width=200)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        logo = tk.Canvas(side, width=64, height=60, bg=COLORS['soft'], highlightthickness=0)
        logo.pack(anchor='w', padx=20, pady=(24, 0))
        # Curvas aproximadas do símbolo oficial, desenhadas nativamente.
        for points in [(8,24,22,6,36,34,56,14), (6,35,23,17,40,49,60,28), (14,46,30,33,42,57,54,44)]:
            logo.create_line(*points, smooth=True, width=3, fill=COLORS['forest'], capstyle=tk.ROUND)
        self.label(side, 'aeris.', 30, 'soft').pack(anchor='w', padx=20)
        self.label(side, 'Naturalmente bom.', 10, 'soft').pack(anchor='w', padx=20)
        self.label(side, 'by K&G Vision', 9, 'soft').pack(anchor='w', padx=20, pady=(2,30))
        self.label(side, '  Hub / Catálogo', 13, 'muted', pady=10).pack(fill='x', padx=12)
        self.label(side, 'FOUNDATION', 9, 'soft').pack(anchor='w', padx=20, pady=(24,5))
        self.capture_button = ttk.Button(side, text='Capture', command=self.open_capture)
        self.capture_button.pack(fill='x', padx=15, pady=5)
        for name in ('Snippets', 'Search', 'Spotlight'):
            self.label(side, f'  {name} · planejado', 10, 'soft').pack(anchor='w', padx=15, pady=5)
        self.label(side, f'Pré-alpha {__version__}', 9, 'soft').pack(side='bottom', anchor='w', padx=20, pady=15)
        body = tk.Frame(self.root, bg=COLORS['air'])
        body.pack(fill='both', expand=True, padx=24, pady=22)
        self.label(body, 'Seu espaço, mais leve.', 25).pack(fill='x')
        self.label(body, 'Explore o catálogo de ferramentas do Aeris.', 11).pack(fill='x', pady=(3,16))
        filters = tk.Frame(body, bg=COLORS['air']); filters.pack(fill='x')
        self.search = tk.Entry(filters, textvariable=self.query, font=('Segoe UI', 12), relief='flat',
                               bg='white', fg=COLORS['deep'], highlightthickness=1, highlightbackground=COLORS['muted'])
        self.search.pack(side='left', fill='x', expand=True, ipady=7)
        categories = ['Todas', *dict.fromkeys(m.category for m in self.modules)]
        ttk.Combobox(filters, textvariable=self.category, values=categories, state='readonly',
                     width=18, style='Aeris.TCombobox').pack(side='left', padx=(10,0))
        self.label(body, 'Filtrar por nome, descrição ou categoria · Ctrl+F', 9).pack(fill='x', pady=(4,12))
        self.count = self.label(body, '', 10); self.count.pack(fill='x', pady=(0,5))
        content = tk.Frame(body, bg=COLORS['air']); content.pack(fill='both', expand=True)
        list_frame = tk.Frame(content, bg=COLORS['air']); list_frame.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(list_frame); scroll.pack(side='right', fill='y')
        self.listbox = tk.Listbox(list_frame, font=('Segoe UI', 11), relief='flat', borderwidth=0,
                                  bg='white', fg=COLORS['deep'], selectbackground=COLORS['soft'],
                                  selectforeground=COLORS['deep'], activestyle='none', exportselection=False,
                                  yscrollcommand=scroll.set, width=27, highlightthickness=1,
                                  highlightbackground=COLORS['muted'])
        self.listbox.pack(fill='both', expand=True)
        scroll.configure(command=self.listbox.yview)
        self.listbox.bind('<<ListboxSelect>>', self.show_selected)
        detail = tk.Frame(content, bg=COLORS['soft'], width=265)
        detail.pack(side='right', fill='y', padx=(12,0)); detail.pack_propagate(False)
        self.detail_name = self.label(detail, '', 19, 'soft', wraplength=230, justify='left')
        self.detail_name.pack(fill='x', padx=15, pady=(20,5))
        self.detail_status = self.label(detail, '', 10, 'soft', wraplength=230, justify='left')
        self.detail_status.pack(fill='x', padx=15, pady=(0,16))
        self.detail_desc = self.label(detail, '', 11, 'soft', wraplength=230, justify='left')
        self.detail_desc.pack(fill='x', padx=15)
        self.toggle = ttk.Button(detail, command=self.toggle_capture)
        self.toggle.pack(fill='x', padx=15, pady=(18, 4))
        self.launch = ttk.Button(detail, text='Abrir Capture', command=self.open_capture)
        self.launch.pack(fill='x', padx=15, pady=4)
        self.label(body, 'Local por padrão · Sem conta, rede ou coleta de dados neste protótipo.', 9).pack(fill='x', pady=(12,0))

    def refresh(self, *_):
        self.visible = filter_catalog(self.modules, self.query.get(), self.category.get())
        self.listbox.delete(0, tk.END)
        for module in self.visible:
            self.listbox.insert(tk.END, f'  {module.name}  ·  {module.category}')
        self.count.configure(text=f'{len(self.visible)} de {len(self.modules)} ferramentas no catálogo')
        if self.visible:
            self.listbox.selection_set(0)
        self.show_selected()

    def show_selected(self, _=None):
        self.toggle.pack_forget()
        self.launch.pack_forget()
        self.capture_button.configure(state='normal' if self.settings.capture_enabled else 'disabled')
        selection = self.listbox.curselection()
        if not selection:
            self.detail_name.configure(text='Nenhum resultado')
            self.detail_status.configure(text='')
            self.detail_desc.configure(text='Tente outro termo ou categoria.')
            return
        module = self.visible[selection[0]]
        status = 'Protótipo disponível' if module.status == 'prototype' else 'Planejado · não implementado'
        self.detail_name.configure(text=module.name)
        self.detail_status.configure(text=f'{module.category} · {status}')
        if module.name == 'Capture':
            self.detail_status.configure(text='Memory · Protótipo ' + ('ativado' if self.settings.capture_enabled else 'desativado'))
            self.detail_desc.configure(text=module.description + '\n\nSomente na sessão. Use dados fictícios.')
            self.toggle.configure(text='Desativar' if self.settings.capture_enabled else 'Ativar')
            self.toggle.pack(fill='x', padx=15, pady=(18, 4))
            if self.settings.capture_enabled:
                self.launch.pack(fill='x', padx=15, pady=4)
        else:
            self.detail_desc.configure(text=module.description + ('\n\nVocê está usando o protótipo do Hub.' if module.status == 'prototype' else '\n\nA ferramenta ainda não pode ser executada.'))

    def toggle_capture(self):
        enabled = not self.settings.capture_enabled
        if not enabled and not messagebox.askyesno('Desativar Capture?', 'Todas as anotações e edições da sessão serão descartadas.', parent=self.root):
            return
        try:
            self.settings.set_capture(enabled)
        except OSError:
            messagebox.showerror('Aeris', 'Não foi possível salvar a preferência.', parent=self.root)
            return
        if not enabled:
            if self.capture_window and self.capture_window.window.winfo_exists():
                self.capture_window.window.destroy()
            if self.capture_store:
                self.capture_store.clear()
            self.capture_window = self.capture_store = None
        self.show_selected()

    def open_capture(self):
        if not self.settings.capture_enabled:
            return
        if self.capture_window and self.capture_window.window.winfo_exists():
            self.capture_window.window.lift()
            self.capture_window.window.focus_set()
            return
        from aeris.capture import CaptureStore, CaptureWindow
        if self.capture_store is None:
            self.capture_store = CaptureStore()
        self.capture_window = CaptureWindow(self.root, self.capture_store)

    def close(self):
        has_notes = self.capture_store is not None and bool(self.capture_store.list())
        has_draft = self.capture_window is not None and self.capture_window.window.winfo_exists() and self.capture_window.dirty()
        if (has_notes or has_draft) and not messagebox.askyesno('Encerrar Aeris?', 'Anotações e edições da sessão serão descartadas.', parent=self.root):
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    Hub(root)
    root.mainloop()
