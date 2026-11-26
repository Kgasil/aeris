"""Explicit routine editor, local execution and reviewed copy."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox
from aeris.routine import RoutineEngine, RoutineStore, STEPS, MAX_STEPS
from aeris.permissions import ROUTINE_RUN, ROUTINE_COPY
from aeris.translate import LANGUAGES

class RoutineWindow:
    def __init__(self, hub, store):
        self.hub, self.store = hub, store
        self.engine = RoutineEngine(hub)
        self.preview = None
        self.executed = None
        self.preview_context = None
        self.steps = []
        self.window = tk.Toplevel(hub.root)
        self.window.title('Aeris Routine · Sequências locais')
        self.window.geometry('650x720'); self.window.minsize(490, 600)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda _: self.close())
        f = ttk.Frame(self.window, padding=12); f.pack(fill='both', expand=True)
        ttk.Label(f, text='Routine · simplifique suas tarefas', font=('Segoe UI', 17)).pack(anchor='w')
        ttk.Label(f, text='Rotinas da sessão. Sem agendamento, comandos ou envio automático.', wraplength=450).pack(anchor='w')
        r = ttk.Frame(f); r.pack(fill='x', pady=4)
        self.saved = ttk.Combobox(r, state='readonly'); self.saved.pack(side='left', fill='x', expand=True)
        ttk.Button(r, text='Carregar', command=self.load).pack(side='left')
        ttk.Button(r, text='Excluir', command=self.delete).pack(side='left')
        self.name = tk.StringVar(self.window, 'Minha rotina')
        ttk.Entry(f, textvariable=self.name).pack(fill='x')
        r = ttk.Frame(f); r.pack(fill='x', pady=4)
        self.step = tk.StringVar(self.window, STEPS[0])
        ttk.Combobox(r, textvariable=self.step, values=STEPS, state='readonly').pack(side='left', fill='x', expand=True)
        ttk.Button(r, text='Adicionar etapa', command=self.add).pack(side='left')
        self.sequence = tk.Listbox(f, height=5, exportselection=False); self.sequence.pack(fill='x')
        r = ttk.Frame(f); r.pack(fill='x')
        for label, cmd in [('Subir', lambda: self.move(-1)), ('Descer', lambda: self.move(1)), ('Remover', self.remove), ('Salvar rotina', self.save)]:
            ttk.Button(r, text=label, command=cmd).pack(side='left', padx=2)
        ttk.Label(f, text='Entrada manual · use texto fictício').pack(anchor='w', pady=(6,0))
        self.input = tk.Text(f, height=4, wrap='word'); self.input.pack(fill='both', expand=True)
        self.input.bind('<<Modified>>', self.changed); self.input.edit_modified(False)
        r = ttk.Frame(f); r.pack(fill='x', pady=4)
        self.src = tk.StringVar(self.window, 'pt'); self.dst = tk.StringVar(self.window, 'en')
        ttk.Label(r, text='Idiomas da tradução:').pack(side='left')
        for var in (self.src, self.dst): ttk.Combobox(r, textvariable=var, values=tuple(LANGUAGES), state='readonly', width=5).pack(side='left', padx=3)
        self.run_button = ttk.Button(f, text='Executar e revisar', command=self.run); self.run_button.pack(fill='x')
        self.output = tk.Text(f, height=5, wrap='word', state='disabled'); self.output.pack(fill='both', expand=True, pady=4)
        r = ttk.Frame(f); r.pack(fill='x')
        self.copy_button = ttk.Button(r, text='Copiar resultado', command=self.copy); self.copy_button.pack(side='left')
        ttk.Button(r, text='Permissões', command=hub.open_permissions).pack(side='right')
        self.status = tk.StringVar(self.window, 'Monte uma sequência de até cinco etapas.')
        ttk.Label(f, textvariable=self.status, wraplength=450).pack(anchor='w')
        for var in (self.name, self.src, self.dst): trace_window(self.window, var, lambda *_: self.invalidate())
        self.refresh_saved(); self.render_steps(); self.buttons()

    def buttons(self):
        from aeris.permissions import BRIDGE_RUN
        p = self.hub.permissions
        self.run_button.configure(state='normal' if p.allowed(ROUTINE_RUN) and p.allowed(BRIDGE_RUN) else 'disabled')
        self.copy_button.configure(state='normal' if self.preview and p.allowed(ROUTINE_COPY) else 'disabled')

    def invalidate(self):
        self.preview = self.executed = self.preview_context = None
        self.output.configure(state='normal'); self.output.delete('1.0','end'); self.output.configure(state='disabled'); self.buttons()

    def changed(self, _=None):
        if self.input.edit_modified(): self.input.edit_modified(False); self.invalidate()

    def permissions_changed(self):
        self.invalidate(); self.status.set('Permissões alteradas. Execute novamente.')

    def refresh_saved(self):
        self.saved.configure(values=tuple(x.name for x in self.store.list()))
        self.saved.set('')

    def render_steps(self, selected=None):
        self.sequence.delete(0,'end')
        for i, s in enumerate(self.steps): self.sequence.insert('end', f'{i+1}. {s}')
        if selected is not None: self.sequence.selection_set(selected)
        self.invalidate()

    def add(self):
        if len(self.steps) >= MAX_STEPS: self.status.set('Limite de cinco etapas.'); return
        self.steps.append(self.step.get()); self.render_steps(len(self.steps)-1)

    def remove(self):
        sel = self.sequence.curselection()
        if sel: self.steps.pop(sel[0]); self.render_steps()

    def move(self, direction):
        sel = self.sequence.curselection()
        if not sel: return
        i = sel[0]; j = i+direction
        if 0 <= j < len(self.steps):
            self.steps[i],self.steps[j] = self.steps[j],self.steps[i]; self.render_steps(j)

    def save(self):
        try:
            name=self.name.get().strip()
            if any(x.name==name for x in self.store.list()) and not messagebox.askyesno('Atualizar rotina?', 'Substituir a sequência salva com este nome?', parent=self.window): return
            item=self.store.save(name,self.steps); self.refresh_saved(); self.saved.set(item.name); self.status.set('Rotina salva somente nesta sessão.')
        except ValueError as exc: self.status.set(str(exc))

    def load(self):
        item=next((x for x in self.store.list() if x.name==self.saved.get()),None)
        if item:
            self.name.set(item.name); self.steps=list(item.steps); self.render_steps(); self.status.set('Sequência carregada. Revise antes de executar.')

    def delete(self):
        name=self.saved.get()
        if name and messagebox.askyesno('Excluir rotina?', 'Remover a sequência salva?', parent=self.window):
            self.store.delete(name); self.refresh_saved(); self.status.set('Rotina excluída. O editor atual foi preservado.')

    def context(self):
        return (self.name.get(),tuple(self.steps),self.input.get('1.0','end-1c'),self.src.get(),self.dst.get())

    def require_review(self):
        if self.preview is None or self.preview_context!=self.context():
            self.invalidate()
            raise ValueError('Entrada ou sequência alterada. Execute novamente.')
        self.engine.require(self.executed); self.hub.permissions.require(ROUTINE_COPY)

    def run(self):
        self.invalidate()
        try:
            item=RoutineStore().save(self.name.get(),self.steps)
            previews=self.engine.run(item,self.input.get('1.0','end-1c'),self.src.get(),self.dst.get())
            self.executed=item; self.preview=previews[-1]; self.preview_context=self.context()
            self.output.configure(state='normal'); self.output.insert('1.0',self.render()); self.output.configure(state='disabled')
            self.status.set(f'{len(previews)} etapas concluídas. Nenhuma anotação criada; revise o resultado.'); self.buttons()
        except (ValueError,PermissionError) as exc: self.status.set(str(exc))

    def render(self):
        return (self.preview.subject+'\n\n' if self.preview.subject else '')+self.preview.text

    def copy(self):
        try:
            self.require_review()
            reviewed=self.preview
            if not messagebox.askyesno('Copiar?', 'Substituir a área de transferência? O histórico do sistema pode reter a cópia.', parent=self.window): return
            self.require_review()
            if self.preview is not reviewed: raise ValueError('Prévia alterada. Execute novamente.')
            self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(self.render()); self.status.set('Copiado. Cole manualmente.')
        except (ValueError,PermissionError,tk.TclError) as exc: self.status.set(str(exc))

    def close(self):
        if (self.steps or self.input.get('1.0','end-1c').strip()) and not messagebox.askyesno('Fechar Routine?', 'Descartar editor e prévia? Rotinas salvas permanecem na sessão.',parent=self.window): return
        self.window.destroy()
