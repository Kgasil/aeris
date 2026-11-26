"""Apply reviewed Core changes to the exact RC4 source; fail closed on a different base."""
from pathlib import Path
import hashlib
import sys

def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected patch anchor: " + old[:100])
    return text.replace(old, new, 1)

def apply(root):
    root = Path(root)
    hashes = {
        "hub.py": "f9659c8736f107b4109af5bc5774dfed57e1e22bc96abf3e3c955b81b8ede3f1",
        "spotlight.py": "bf6304c431fb222de6eecd1fee01ed8b104ad051133c6940913fcb28330e9199",
        "health_ui.py": "e5bf666aac27980a435fb4a3a6e6bb67b2049372663e90f670cb6bffafad3d9f",
        "backup.py": "597de6d78b794979f48df62b6ab04dd0c23a254f386a7780008b019e4f7226ce",
        "backup_ui.py": "5264ebbcd72ca101ad62133826070defff52721dda1edfb0e0cdee72dc77d3b9",
        "bridge_ui.py": "eacb6a8a35e9194476b76d086daf723ac670bad672e799ecde1a8ae4808e8440",
    }
    files = {}
    for name, expected in hashes.items():
        raw = (root / "aeris" / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Unexpected RC4 source: " + name)
        files[name] = raw.decode("utf-8").replace("\r\n", "\n")
    s = files["hub.py"]
    s = replace(s, "'Discreto e Eficiente.'", "'Eficiência e Simplicidade.'")
    s = replace(s, "        self.search.pack(side='left', fill='x', expand=True, ipady=7)", """        self.search.pack(side='left', fill='x', expand=True, ipady=7)
        ttk.Button(filters, text='Limpar', command=self.clear_filters).pack(side='right', padx=(8,0))
        self.search.bind('<Escape>', lambda _: self.clear_filters())
        self.search.bind('<Return>', self.focus_results)""")
    s = replace(s, "        self.listbox.bind('<<ListboxSelect>>', self.show_selected)", """        self.listbox.bind('<<ListboxSelect>>', self.show_selected)
        self.listbox.bind('<Return>', self.open_selected)
        self.listbox.bind('<Double-Button-1>', self.open_selected)""")
    s = replace(s, "    def refresh(self, *_):\n        self.visible", """    def clear_filters(self):
        self.query.set('')
        self.category.set('Todas')
        self.search.focus_set()
        return 'break'

    def focus_results(self, _=None):
        if self.visible:
            self.listbox.focus_set()
        return 'break'

    def open_selected(self, _=None):
        selection = self.listbox.curselection()
        if selection:
            self.show_selected()
            if self.launch.winfo_manager():
                self.launch.invoke()
        return 'break'

    def refresh(self, *_):
        selection = self.listbox.curselection()
        selected = self.visible[selection[0]].name if selection and selection[0] < len(self.visible) else None
        self.visible""")
    s = replace(s, "            self.listbox.selection_set(0)", """            index = next((i for i, module in enumerate(self.visible) if module.name == selected), 0)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)""")
    files["hub.py"] = s
    s = files["spotlight.py"]
    s = replace(s, "highlightthickness=0, cursor='hand2', takefocus=True", "highlightthickness=2, highlightbackground='#285640', highlightcolor='#DCEFE3', cursor='hand2', takefocus=True")
    s = replace(s, "        self.button.bind('<Button-3>', self.menu)", """        self.button.bind('<Button-3>', self.menu)
        self.button.bind('<Shift-F10>', self.keyboard_menu)""")
    s = replace(s, "    def menu(self, event):", """    def keyboard_menu(self, _=None):
        from types import SimpleNamespace
        self.menu(SimpleNamespace(x_root=self.window.winfo_rootx(), y_root=self.window.winfo_rooty()))
        return 'break'

    def menu(self, event):""")
    s = replace(s, "        self.panel.bind('<Escape>',self.dismiss)", "        self.panel.bind('<Escape>',self.dismiss_and_focus)")
    s = replace(s, "    def show_panel(self):", """    def dismiss_and_focus(self, _=None):
        self.dismiss()
        if self.window.winfo_exists():
            self.button.focus_set()
        return 'break'

    def show_panel(self):""")
    s = replace(s, "        self.panel.lift()\n", """        self.panel.lift()
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
""")
    files["spotlight.py"] = s
    s = files["health_ui.py"]
    s = replace(s, "        if start is None or not self.hub.enabled('Health'): return\n        self.button.configure(state='normal')", """        self.button.configure(state='normal')
        if start is None or not self.hub.enabled('Health'):
            self.status.set('Medição cancelada.'); self.report.set('Sem amostra.')
            return""")
    files["health_ui.py"] = s
    s = files["backup.py"]
    s = replace(s, "        self.permissions.require(RESTORE_BACKUP)\n        return tuple(parse(bounded_read(path, MAX_ARCHIVE)))\n\n    def restore(self, path, name):\n        self.permissions.require(RESTORE_BACKUP)\n        data = parse(bounded_read(path, MAX_ARCHIVE))[name]", """        return self.inspect_with_digest(path)[0]

    def inspect_with_digest(self, path):
        self.permissions.require(RESTORE_BACKUP)
        raw = bounded_read(path, MAX_ARCHIVE)
        return tuple(parse(raw)), hashlib.sha256(raw).hexdigest()

    def restore(self, path, name, expected_digest=None):
        self.permissions.require(RESTORE_BACKUP)
        raw = bounded_read(path, MAX_ARCHIVE)
        if expected_digest is not None and hashlib.sha256(raw).hexdigest() != expected_digest:
            raise ValueError('Backup alterado desde a inspeção. Selecione e verifique novamente.')
        data = parse(raw)[name]""")
    files["backup.py"] = s
    s = files["backup_ui.py"]
    s = replace(s, "        self.path=None; self.permissions_changed()", "        self.path=None; self.digest=None; self.permissions_changed()")
    s = replace(s, "            self.path=None; self.choice.set('');", "            self.path=None; self.digest=None; self.choice.set('');")
    s = replace(s, "        self.path=None; self.choice.set('');", "        self.path=None; self.digest=None; self.choice.set('');")
    s = replace(s, "names=self.service.inspect(path); self.path=path;", "names,self.digest=self.service.inspect_with_digest(path); self.path=path;")
    s = replace(s, "        if not self.path or not self.hub.permissions.allowed(RESTORE_BACKUP): return\n        name=self.choice.get()", """        if not self.path or not self.digest or not self.hub.permissions.allowed(RESTORE_BACKUP): return
        path,digest,name=self.path,self.digest,self.choice.get()""")
    s = replace(s, "        if self.blocked():", """        if (path,digest,name)!=(self.path,self.digest,self.choice.get()):
            self.status.set('Seleção alterada. Inspecione novamente.'); return
        if self.blocked():""")
    s = replace(s, "recovery=self.service.restore(self.path,name)", "recovery=self.service.restore(path,name,expected_digest=digest)")
    files["backup_ui.py"] = s
    s = files["bridge_ui.py"]
    s = replace(s, "self.preview=None; self.imported='Manual';", "self.preview=None; self.preview_context=None; self.imported='Manual';")
    s = replace(s, "        self.preview=None; self.output.configure", "        self.preview=None; self.preview_context=None; self.output.configure")
    s = replace(s, "    def run(self):\n", """    def current_context(self):
        return (self.route.get(), self.input.get('1.0','end-1c'), self.imported, self.src.get(), self.dst.get())

    def run(self):
""")
    s = replace(s, "self.preview=self.engine.run(self.route.get(),self.input.get('1.0','end-1c'),self.imported,self.src.get(),self.dst.get())", "self.preview_context=self.current_context(); self.preview=self.engine.run(*self.preview_context)")
    s = replace(s, "        if self.preview is None: raise ValueError('Execute o fluxo novamente.')", """        if self.preview is None or self.preview_context != self.current_context():
            self.invalidate()
            raise ValueError('Entrada ou fluxo alterado. Execute novamente.')""")
    s = replace(s, "            self.require_preview(BRIDGE_SAVE)\n            if not messagebox", "            self.require_preview(BRIDGE_SAVE)\n            reviewed=self.preview; title=self.title.get()\n            if not messagebox")
    s = replace(s, "            self.require_preview(BRIDGE_SAVE); self.engine.save_capture(self.preview,self.title.get());", """            self.require_preview(BRIDGE_SAVE)
            if self.preview is not reviewed or self.title.get()!=title: raise ValueError('Seleção alterada. Revise novamente.')
            self.engine.save_capture(reviewed,title);""")
    s = replace(s, "            self.require_preview(BRIDGE_COPY)\n            if not messagebox", "            self.require_preview(BRIDGE_COPY)\n            reviewed=self.preview\n            if not messagebox")
    s = replace(s, "            self.require_preview(BRIDGE_COPY); self.hub.root.clipboard_clear();", """            self.require_preview(BRIDGE_COPY)
            if self.preview is not reviewed: raise ValueError('Prévia alterada. Revise novamente.')
            self.hub.root.clipboard_clear();""")
    files["bridge_ui.py"] = s
    for name, code in files.items():
        compile(code, name, "exec")
    for name, code in files.items():
        (root / "aeris" / name).write_bytes(code.encode("utf-8"))
    print("Core overlay applied: six reviewed files, RC4 base verified")

if __name__ == "__main__":
    apply(sys.argv[1])
