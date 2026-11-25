"""Anotações explícitas em memória, sem disco, rede ou captura automática."""
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox

@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str

class CaptureStore:
    def __init__(self):
        self._notes = {}
        self._next = 1

    def list(self):
        return tuple(self._notes.values())

    def save(self, title, body, note_id=None):
        title = title.strip()
        if not title or not body.strip():
            raise ValueError('Preencha título e conteúdo.')
        if len(title) > 120 or len(body) > 100000:
            raise ValueError('Limite: 120 caracteres no título e 100.000 no conteúdo.')
        if note_id is None:
            if len(self._notes) >= 100:
                raise ValueError('Limite de 100 anotações por sessão.')
            note_id = self._next
            self._next += 1
        elif note_id not in self._notes:
            raise KeyError(note_id)
        self._notes[note_id] = Note(note_id, title, body)
        return self._notes[note_id]

    def delete(self, note_id):
        del self._notes[note_id]

    def clear(self):
        self._notes.clear()

class CaptureWindow:
    def __init__(self, parent, store):
        self.store = store
        self.current = None
        self.window = tk.Toplevel(parent)
        self.window.title('Aeris Capture — sessão local')
        self.window.geometry('760x480')
        self.window.minsize(560, 360)
        self.window.configure(bg='#F6FAF7')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        ttk.Label(self.window, text='Capture · anotações voluntárias', font=('Segoe UI', 16)).pack(anchor='w', padx=16, pady=(12, 2))
        ttk.Label(self.window, text='Apenas nesta sessão. Use dados fictícios; nada é salvo em disco.').pack(anchor='w', padx=16)
        area = ttk.Frame(self.window, padding=16)
        area.pack(fill='both', expand=True)
        self.items = tk.Listbox(area, width=24, exportselection=False)
        self.items.pack(side='left', fill='y', padx=(0, 12))
        self.items.bind('<<ListboxSelect>>', self.select)
        editor = ttk.Frame(area)
        editor.pack(side='left', fill='both', expand=True)
        self.title = tk.StringVar(self.window)
        ttk.Label(editor, text='Título').pack(anchor='w')
        ttk.Entry(editor, textvariable=self.title).pack(fill='x', pady=(0, 8))
        ttk.Label(editor, text='Conteúdo').pack(anchor='w')
        self.body = tk.Text(editor, wrap='word', height=8, undo=True)
        self.body.pack(fill='both', expand=True)
        buttons = ttk.Frame(editor)
        buttons.pack(fill='x', pady=(10, 0))
        for label, cmd in [('Nova', self.new), ('Salvar na sessão', self.save), ('Excluir', self.delete)]:
            ttk.Button(buttons, text=label, command=cmd).pack(side='left', padx=(0, 5))
        self.refresh()

    def values(self):
        return self.title.get(), self.body.get('1.0', 'end-1c')

    def dirty(self):
        baseline = next(((n.title, n.body) for n in self.store.list() if n.id == self.current), ('', ''))
        return self.values() != baseline

    def allow_discard(self):
        return not self.dirty() or messagebox.askyesno('Descartar edição?', 'Alterações não salvas serão descartadas.', parent=self.window)

    def refresh(self):
        self.notes = self.store.list()
        self.items.delete(0, 'end')
        for i, note in enumerate(self.notes):
            self.items.insert('end', note.title)
            if note.id == self.current:
                self.items.selection_set(i)

    def fill(self, note=None):
        self.current = note.id if note else None
        self.title.set(note.title if note else '')
        self.body.delete('1.0', 'end')
        if note:
            self.body.insert('1.0', note.body)
        self.body.edit_reset()

    def select(self, _=None):
        selected = self.items.curselection()
        if selected:
            note = self.notes[selected[0]]
            if note.id != self.current:
                if self.allow_discard():
                    self.fill(note)
                else:
                    self.refresh()

    def new(self):
        if self.allow_discard():
            self.fill()
            self.refresh()

    def save(self):
        try:
            note = self.store.save(*self.values(), note_id=self.current)
        except ValueError as exc:
            messagebox.showwarning('Capture', str(exc), parent=self.window)
            return
        self.fill(note)
        self.refresh()

    def delete(self):
        if self.current is not None and messagebox.askyesno('Excluir anotação?', 'Esta anotação e suas edições serão removidas da sessão.', parent=self.window):
            self.store.delete(self.current)
            self.fill()
            self.refresh()

    def close(self):
        if self.allow_discard():
            self.window.destroy()
