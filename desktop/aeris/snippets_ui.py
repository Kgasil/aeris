"""Editor local de snippets; nenhum acesso ao clipboard sem clique explícito."""
import tkinter as tk
from tkinter import ttk, messagebox

class SnippetsWindow:
    def __init__(self, parent, store):
        self.parent, self.store = parent, store
        self.current = None
        self.window = tk.Toplevel(parent)
        self.window.title('Aeris Snippets · sessão local')
        self.window.geometry('650x510')
        self.window.minsize(440, 460)
        self.window.configure(bg='#F6FAF7')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda _: self.close())
        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Snippets', font=('Segoe UI', 18)).pack(anchor='w')
        ttk.Label(frame, text='Textos fictícios nesta sessão. Não use senhas ou dados sensíveis.', wraplength=400).pack(anchor='w', pady=(0, 8))
        self.query = tk.StringVar(self.window)
        ttk.Label(frame, text='Buscar por título, categoria ou texto').pack(anchor='w')
        self.search = ttk.Entry(frame, textvariable=self.query)
        self.search.pack(fill='x', pady=(0, 4))
        self.window.bind('<Control-f>', lambda _: self.search.focus_set())
        listing = ttk.Frame(frame)
        listing.pack(fill='x')
        scroll = ttk.Scrollbar(listing)
        scroll.pack(side='right', fill='y')
        self.items = tk.Listbox(listing, height=4, exportselection=False, yscrollcommand=scroll.set)
        self.items.pack(fill='x', expand=True)
        scroll.configure(command=self.items.yview)
        self.items.bind('<<ListboxSelect>>', self.select)
        self.title = tk.StringVar(self.window)
        self.category = tk.StringVar(self.window, 'Geral')
        for label, variable in [('Título', self.title), ('Categoria', self.category)]:
            ttk.Label(frame, text=label).pack(anchor='w', pady=(4, 0))
            ttk.Entry(frame, textvariable=variable).pack(fill='x')
        ttk.Label(frame, text='Texto reutilizável').pack(anchor='w', pady=(4,0))
        editor = ttk.Frame(frame)
        editor.pack(fill='both', expand=True)
        editor_scroll = ttk.Scrollbar(editor)
        editor_scroll.pack(side='right', fill='y')
        self.body = tk.Text(editor, height=4, wrap='word', undo=True, yscrollcommand=editor_scroll.set)
        self.body.pack(fill='both', expand=True)
        editor_scroll.configure(command=self.body.yview)
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=(8, 0))
        for label, command in [('Novo', self.new), ('Salvar', self.save), ('Excluir', self.delete), ('Copiar texto salvo', self.copy)]:
            ttk.Button(buttons, text=label, command=command).pack(side='left', padx=(0, 4))
        self.status = tk.StringVar(self.window, 'Copiar substitui o conteúdo da área de transferência.')
        ttk.Label(frame, textvariable=self.status, wraplength=400).pack(anchor='w', pady=(5, 0))
        self.query.trace_add('write', self.refresh)
        self.refresh()

    def values(self):
        return self.title.get(), self.category.get(), self.body.get('1.0', 'end-1c')

    def dirty(self):
        item = self.store.get(self.current) if self.current is not None else None
        baseline = (item.title, item.category, item.body) if item else ('', 'Geral', '')
        return self.values() != baseline

    def allow_discard(self):
        return not self.dirty() or messagebox.askyesno('Descartar edição?', 'Alterações não salvas serão descartadas.', parent=self.window)

    def refresh(self, *_):
        self.visible = self.store.list(self.query.get())
        self.items.delete(0, 'end')
        for i, item in enumerate(self.visible):
            self.items.insert('end', f'{item.title} · {item.category}')
            if item.id == self.current:
                self.items.selection_set(i)

    def fill(self, item=None):
        self.current = item.id if item else None
        self.title.set(item.title if item else '')
        self.category.set(item.category if item else 'Geral')
        self.body.delete('1.0', 'end')
        if item:
            self.body.insert('1.0', item.body)
        self.body.edit_reset()

    def select(self, _=None):
        selected = self.items.curselection()
        if not selected:
            return
        item = self.visible[selected[0]]
        if item.id != self.current:
            if self.allow_discard():
                self.fill(item)
            else:
                self.refresh()

    def new(self):
        if self.allow_discard():
            self.fill()
            self.refresh()
            self.status.set('Novo snippet.')

    def save(self):
        try:
            item = self.store.save(*self.values(), snippet_id=self.current)
        except ValueError as exc:
            messagebox.showwarning('Snippets', str(exc), parent=self.window)
            return
        self.fill(item)
        self.refresh()
        self.status.set('Salvo somente nesta sessão.')

    def delete(self):
        if self.current is not None and messagebox.askyesno('Excluir snippet?', 'Remover o texto salvo e a edição atual da sessão?', parent=self.window):
            self.store.delete(self.current)
            self.fill()
            self.refresh()
            self.status.set('Snippet removido. Uma cópia anterior pode permanecer no clipboard.')

    def copy(self):
        if self.current is None:
            self.status.set('Salve ou selecione um snippet antes de copiar.')
            return
        if self.dirty():
            self.status.set('Salve as alterações antes de copiar.')
            return
        if not messagebox.askyesno('Copiar para o clipboard?', 'O texto substituirá o clipboard atual e poderá permanecer no histórico do sistema. Continuar?', parent=self.window):
            return
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.store.get(self.current).body)
        except tk.TclError:
            messagebox.showerror('Snippets', 'Não foi possível copiar o texto.', parent=self.window)
            return
        self.status.set('Copiado. Cole manualmente no destino.')

    def close(self):
        if self.allow_discard():
            self.window.destroy()
