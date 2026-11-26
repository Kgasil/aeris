"""Manual local code review; no files opened and no execution."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.debug import analyze

class DebugWindow:
    def __init__(self, hub):
        self.hub=hub; self.window=w=tk.Toplevel(hub.root)
        w.title('Aeris Debug'); w.geometry('740x620'); w.minsize(550,470)
        self.analysis=None; self.snapshot=None; self.diagnostic_index=-1; self.status=tk.StringVar(w)
        f=ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Debug',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Análise estática de Python local. O código nunca é executado.',wraplength=520).pack(anchor='w')
        ttk.Label(f,text='Código Python (até 20.000 caracteres / 1.000 linhas)').pack(anchor='w',pady=(8,0))
        self.source=self.textbox(f,10,'none')
        self.source.bind('<<Modified>>',self.changed); self.source.edit_modified(False)
        row=ttk.Frame(f); row.pack(fill='x',pady=5)
        ttk.Button(row,text='Analisar',command=self.run).pack(side='left')
        ttk.Button(row,text='Primeiro diagnóstico',command=self.goto).pack(side='left',padx=5)
        self.next_button=ttk.Button(row,text='Próximo',command=lambda:self.goto(True),state='disabled'); self.next_button.pack(side='left')
        ttk.Button(row,text='Limpar',command=self.clear).pack(side='left')
        ttk.Label(f,textvariable=self.status,wraplength=520).pack(anchor='w')
        self.output=self.textbox(f,7,'word'); self.output.configure(state='disabled')
        ttk.Label(f,text='Avisos são heurísticos. Sintaxe válida não garante segurança ou funcionamento.',wraplength=520).pack(anchor='w',pady=4)
        w.bind('<Control-Return>',lambda _:self.run()); w.bind('<Escape>',lambda _:self.close()); w.protocol('WM_DELETE_WINDOW',self.close)
        w.bind('<Destroy>',self.destroyed,add='+')
    def textbox(self,parent,height,wrap):
        frame=ttk.Frame(parent); frame.pack(fill='both',expand=True)
        t=tk.Text(frame,height=height,wrap=wrap,font=('Consolas',11),undo=False)
        sb=ttk.Scrollbar(frame,command=t.yview); t.configure(yscrollcommand=sb.set)
        t.grid(row=0,column=0,sticky='nsew'); sb.grid(row=0,column=1,sticky='ns')
        if wrap=='none':
            x=ttk.Scrollbar(frame,orient='horizontal',command=t.xview); t.configure(xscrollcommand=x.set); x.grid(row=1,column=0,sticky='ew')
        frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)
        return t
    def dirty(self): return bool(self.source.get('1.0','end-1c'))
    def display(self,text):
        self.output.configure(state='normal'); self.output.delete('1.0','end'); self.output.insert('1.0',text); self.output.configure(state='disabled')
    def invalidate(self):
        self.analysis=None; self.snapshot=None; self.diagnostic_index=-1; self.next_button.configure(state='disabled'); self.status.set(''); self.display('')
    def changed(self,_=None):
        if self.source.edit_modified():
            self.source.edit_modified(False); self.invalidate()
    def run(self):
        self.source.edit_modified(False); self.invalidate()
        try: self.analysis=analyze(self.source.get('1.0','end-1c'))
        except ValueError as exc: self.status.set(str(exc)); return 'break'
        r=self.analysis
        self.snapshot=self.source.get('1.0','end-1c')
        self.next_button.configure(state='normal' if r.diagnostics else 'disabled')
        self.status.set(('Sintaxe válida · '+str(len(r.diagnostics))+' avisos'+(' (limitados)' if r.truncated else '')) if r.valid else 'Erro de sintaxe ou estrutura')
        self.display('\n\n'.join(f'{d.kind} · Linha {d.line}, coluna {d.column}\n{d.message}\nSugestão: {d.suggestion}' for d in r.diagnostics) or 'Nenhum dos avisos implementados encontrado.')
        return 'break'
    def goto(self,advance=False):
        if self.source.edit_modified() or self.snapshot!=self.source.get('1.0','end-1c'):
            self.source.edit_modified(False); self.invalidate(); return
        if self.analysis and self.analysis.diagnostics:
            ds=self.analysis.diagnostics
            self.diagnostic_index=(self.diagnostic_index+1)%len(ds) if advance else 0
            d=ds[self.diagnostic_index]; pos=f'{d.line}.{d.column-1}'
            self.source.mark_set('insert',pos); self.source.see(pos); self.source.focus_set()
            self.status.set(f'Diagnóstico {self.diagnostic_index+1}/{len(ds)} · Linha {d.line}, coluna {d.column}')
    def clear(self):
        if not self.discard_confirmed('Limpar código?'): return
        self.source.delete('1.0','end'); self.source.edit_modified(False); self.invalidate()
    def discard_confirmed(self,title):
        reviewed=self.source.get('1.0','end-1c')
        if reviewed and not messagebox.askyesno(title,'Descartar código e diagnóstico?',parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.source.get('1.0','end-1c'):
            self.status.set('Código alterado. Confirme novamente.'); return False
        return True
    def close(self):
        if self.discard_confirmed('Fechar Debug?'): self.window.destroy()
        return 'break'
    def destroyed(self,event):
        if event.widget is self.window: self.analysis=None; self.snapshot=None; self.status.set('')
