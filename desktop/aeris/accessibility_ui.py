"""Manual reading preview. No file, screen, microphone or network access."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.accessibility import Reader, ReadingOptions, PALETTES

class AccessibilityWindow:
    def __init__(self, hub):
        self.hub=hub; self.reader=Reader(); self.window=tk.Toplevel(hub.root)
        w=self.window; w.title('Aeris Accessibility'); w.geometry('750x660'); w.minsize(580,560)
        f=ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Accessibility',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Tecnologia para todos. Leitor local de texto inserido manualmente.').pack(anchor='w')
        ttk.Label(f,text='Texto de origem (até 20.000 caracteres)').pack(anchor='w',pady=(8,0))
        self.source=tk.Text(f,height=4,wrap='word',undo=False,font=('Segoe UI',11)); self.source.pack(fill='x')
        actions=ttk.Frame(f); actions.pack(fill='x',pady=4)
        ttk.Button(actions,text='Preparar leitura (Ctrl+Enter)',command=self.load).pack(side='left')
        ttk.Button(actions,text='Limpar texto',command=self.confirm_clear).pack(side='left',padx=5)
        self.size=tk.IntVar(w,16); self.palette=tk.StringVar(w,'Natural'); self.spacious=tk.BooleanVar(w,False); self.guide=tk.BooleanVar(w,False); self.status=tk.StringVar(w)
        opts=ttk.Frame(f); opts.pack(fill='x',pady=4)
        ttk.Label(opts,text='Tamanho (pt)').grid(row=0,column=0,sticky='w'); ttk.Spinbox(opts,from_=12,to=30,textvariable=self.size,width=5,state='readonly',command=self.style).grid(row=0,column=1,padx=5)
        ttk.Label(opts,text='Contraste').grid(row=0,column=2,sticky='w'); combo=ttk.Combobox(opts,textvariable=self.palette,values=tuple(PALETTES),state='readonly',width=15); combo.grid(row=0,column=3,padx=5); combo.bind('<<ComboboxSelected>>',lambda _:self.style())
        ttk.Checkbutton(opts,text='Espaçamento ampliado',variable=self.spacious,command=self.style).grid(row=1,column=0,columnspan=2,sticky='w')
        ttk.Checkbutton(opts,text='Guia por linha',variable=self.guide,command=self.style).grid(row=1,column=2,columnspan=2,sticky='w')
        ttk.Button(opts,text='Restaurar padrões',command=self.reset).grid(row=2,column=0,columnspan=4,sticky='w',pady=4)
        ttk.Label(f,text='Prévia de leitura (somente leitura)').pack(anchor='w')
        pane=ttk.Frame(f); pane.pack(fill='both',expand=True)
        self.preview=tk.Text(pane,wrap='word',state='disabled',takefocus=True,padx=12,pady=8,exportselection=False,highlightthickness=2); self.preview._aeris_reader_palette=True
        bar=ttk.Scrollbar(pane,command=self.preview.yview); bar.pack(side='right',fill='y'); self.preview.configure(yscrollcommand=bar.set); self.preview.pack(side='left',fill='both',expand=True)
        # Text normally consumes Tab; explicitly traverse focus in the read-only preview.
        for widget in (self.source,self.preview):
            widget.bind('<Tab>',lambda e:self.traverse(e.widget,1)); widget.bind('<Shift-Tab>',lambda e:self.traverse(e.widget,-1)); widget.bind('<ISO_Left_Tab>',lambda e:self.traverse(e.widget,-1)); widget.bind('<Control-Return>',lambda _:self.load())
        nav=ttk.Frame(f); nav.pack(fill='x',pady=4)
        self.prev=ttk.Button(nav,text='Linha anterior (Alt+↑)',command=lambda:self.move(-1)); self.prev.pack(side='left')
        self.next=ttk.Button(nav,text='Próxima linha (Alt+↓)',command=lambda:self.move(1)); self.next.pack(side='left',padx=4)
        self.first=ttk.Button(nav,text='Primeira',command=lambda:self.jump(False)); self.first.pack(side='left',padx=2)
        self.last=ttk.Button(nav,text='Última',command=lambda:self.jump(True)); self.last.pack(side='left',padx=2)
        self.position=tk.StringVar(w); ttk.Label(nav,textvariable=self.position).pack(side='left',padx=4)
        ttk.Label(f,textvariable=self.status,wraplength=510).pack(anchor='w')
        w.bind('<Control-Return>',lambda _:self.load()); w.bind('<Alt-Up>',lambda _:self.move(-1)); w.bind('<Alt-Down>',lambda _:self.move(1)); w.bind('<Escape>',lambda _:self.close()); w.protocol('WM_DELETE_WINDOW',self.close)
        w.bind('<Destroy>',self.destroyed,add='+')
        self.style(); self.source.focus_set()
    def destroyed(self,event):
        if event.widget is self.window: self.reader.clear()
    def traverse(self,widget,direction):
        (widget.tk_focusNext() if direction==1 else widget.tk_focusPrev()).focus_set(); return 'break'
    def dirty(self): return bool(self.source.get('1.0','end-1c') or self.reader.text)
    def load(self):
        try: self.reader.load(self.source.get('1.0','end-1c'))
        except ValueError as e: self.status.set(str(e)+' Prévia anterior mantida.'); return 'break'
        self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.insert('1.0',self.reader.text); self.preview.configure(state='disabled'); self.status.set('Prévia atualizada.'); self.style(); return 'break'
    def style(self):
        try: opt=ReadingOptions(self.size.get(),self.palette.get(),self.spacious.get(),self.guide.get())
        except (ValueError,tk.TclError) as exc: self.status.set(str(exc)); return
        bg,fg,mark,markfg=PALETTES[opt.palette]
        self.preview.configure(bg=bg,fg=fg,insertbackground=fg,selectbackground=mark,selectforeground=markfg,highlightbackground=fg,highlightcolor=mark if bg=='#000000' else fg,font=('Segoe UI',opt.size),spacing1=6 if opt.spacious else 0,spacing2=5 if opt.spacious else 0,spacing3=8 if opt.spacious else 2)
        self.preview.tag_configure('guide',background=mark,foreground=markfg); self.preview.tag_raise('sel'); self.refresh_guide()
    def refresh_guide(self):
        self.preview.tag_remove('guide','1.0','end'); enabled=self.guide.get() and self.reader.lines>0; n=self.reader.line
        if enabled:
            self.preview.tag_add('guide',f'{n}.0',f'{n}.0 lineend +1c'); self.preview.see(f'{n}.0')
        self.position.set(f'Linha {n}/{self.reader.lines}' if enabled else 'Guia desativado' if not self.guide.get() else 'Sem texto')
        self.prev.configure(state='normal' if enabled and n>1 else 'disabled'); self.next.configure(state='normal' if enabled and n<self.reader.lines else 'disabled')
        self.first.configure(state='normal' if enabled and n>1 else 'disabled')
        self.last.configure(state='normal' if enabled and n<self.reader.lines else 'disabled')
    def jump(self,last):
        if self.guide.get() and self.reader.lines:
            self.reader.line=self.reader.lines if last else 1; self.refresh_guide()
        return 'break'
    def move(self,delta):
        if self.guide.get(): self.reader.move(delta); self.refresh_guide()
        return 'break'
    def reset(self):
        opt=ReadingOptions(); self.size.set(opt.size); self.palette.set(opt.palette); self.spacious.set(opt.spacious); self.guide.set(opt.guide); self.style()
    def clear(self):
        self.source.delete('1.0','end'); self.reader.clear(); self.load(); self.status.set('Texto removido.')
    def snapshot(self): return (self.source.get('1.0','end-1c'),self.reader.text)
    def discard_confirmed(self,title):
        reviewed=self.snapshot()
        if self.dirty() and not messagebox.askyesno(title,'Descartar texto e prévia?',parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.snapshot():
            self.status.set('Texto alterado. Confirme novamente.'); return False
        return True
    def confirm_clear(self):
        if self.discard_confirmed('Limpar leitura?'): self.clear()
    def close(self):
        if self.discard_confirmed('Fechar leitura?'): self.window.destroy()
        return 'break'
