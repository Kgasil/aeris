"""Editable weighted decision matrix, session-only."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.decision import rank_matrix, display_score, MAX_CRITERIA, MAX_ALTERNATIVES
from aeris.scroll_area import scroll_area
from aeris.theme import apply_tree

class DecisionWindow:
    def __init__(self, hub):
        self.hub=hub; self.window=tk.Toplevel(hub.root); w=self.window
        w.title('Aeris Decision'); w.geometry('850x690'); w.minsize(680,480)
        f=ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Decision',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Escolhas mais conscientes. Notas de 0 a 10: maior é sempre melhor.',wraplength=650).pack(anchor='w')
        bar=ttk.Frame(f); bar.pack(fill='x',pady=6)
        self.nc=tk.IntVar(w,3); self.na=tk.IntVar(w,3)
        for label,var,limit in [('Critérios',self.nc,MAX_CRITERIA),('Alternativas',self.na,MAX_ALTERNATIVES)]:
            ttk.Label(bar,text=label).pack(side='left',padx=3)
            ttk.Spinbox(bar,from_=2,to=limit,state='readonly',width=3,textvariable=var).pack(side='left',padx=3)
        ttk.Button(bar,text='Redimensionar',command=self.resize).pack(side='left',padx=3)
        ttk.Button(bar,text='Exemplo',command=self.example).pack(side='left',padx=3)
        self.body=scroll_area(f); self.matrix=ttk.Frame(self.body); self.matrix.pack(fill='x',pady=5)
        self.status=tk.StringVar(w); self.result=(); self.fields=[]; self.matrix_generation=0
        self.build_matrix(3,3)
        actions=ttk.Frame(self.body); actions.pack(fill='x',pady=8)
        ttk.Button(actions,text='Calcular ranking',command=self.calculate).pack(side='left')
        ttk.Button(actions,text='Limpar',command=self.confirm_clear).pack(side='left',padx=5)
        ttk.Label(self.body,textvariable=self.status,wraplength=610).pack(anchor='w')
        self.table=ttk.Treeview(self.body,columns=('rank','name','score'),show='headings',height=6)
        for key,label,width in [('rank','Posição',65),('name','Alternativa',300),('score','Nota / 10',110)]:
            self.table.heading(key,text=label); self.table.column(key,width=width,stretch=key=='name')
        self.table.pack(fill='x',pady=5)
        ttk.Label(self.body,text='Pesos normalizados pela soma. Empates exatos compartilham posição. Notas exibidas com quatro casas; o ranking usa valores exatos. O resultado depende das avaliações informadas.',wraplength=610).pack(anchor='w')
        w.protocol('WM_DELETE_WINDOW',self.close); w.bind('<Escape>',lambda _:self.close()); w.bind('<Destroy>',self.destroyed,add='+')
    def release_fields(self):
        for var in self.fields:
            for mode, token in var.trace_info(): var.trace_remove(mode, token)

    def build_matrix(self,nc,na,old=None):
        self.matrix_generation+=1
        self.release_fields()
        for widget in self.matrix.winfo_children(): widget.destroy()
        self.fields=[]
        def entry(r,c,value='',width=9):
            var=tk.StringVar(self.window,value); self.fields.append(var)
            ttk.Entry(self.matrix,textvariable=var,width=width).grid(row=r,column=c,padx=2,pady=3,sticky='ew')
            var.trace_add('write',self.invalidate); return var
        def existing(kind,i,j=None):
            if old is None: return ''
            seq=old[kind]
            if i>=len(seq): return ''
            return seq[i] if j is None else seq[i][j] if j<len(seq[i]) else ''
        ttk.Label(self.matrix,text='Critério / alternativa').grid(row=0,column=0,sticky='w')
        self.criteria=[entry(0,i+1,existing(0,i)) for i in range(nc)]
        ttk.Label(self.matrix,text='Peso (0–100)').grid(row=1,column=0,sticky='w')
        self.weights=[entry(1,i+1,existing(1,i)) for i in range(nc)]
        self.alternatives=[]; self.scores=[]
        for j in range(na):
            self.alternatives.append(entry(j+2,0,existing(2,j),17))
            self.scores.append([entry(j+2,i+1,existing(3,j,i)) for i in range(nc)])
        for i in range(MAX_CRITERIA+1): self.matrix.columnconfigure(i,weight=1 if i<=nc else 0)
        self.nc.set(nc); self.na.set(na)
        self.invalidate()
    def values(self):
        return ([v.get() for v in self.criteria],[v.get() for v in self.weights],[v.get() for v in self.alternatives],[[v.get() for v in row] for row in self.scores])
    def dirty(self): return any(v.get() for v in self.fields)
    def invalidate(self,*_):
        self.result=()
        if hasattr(self,'table'): self.table.delete(*self.table.get_children()); self.status.set('Calcule para atualizar o ranking.')
    def snapshot(self):
        return (self.matrix_generation,self.values(),self.nc.get(),self.na.get())
    def confirmed(self,title,prompt):
        reviewed=self.snapshot()
        if self.dirty() and not messagebox.askyesno(title,prompt,parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.snapshot():
            self.status.set('Matriz alterada. Confirme novamente.'); return False
        return True
    def resize(self):
        nc,na=self.nc.get(),self.na.get(); old=self.values()
        if not 2<=nc<=MAX_CRITERIA or not 2<=na<=MAX_ALTERNATIVES: return
        if (nc<len(old[0]) or na<len(old[2])) and not self.confirmed('Redimensionar?', 'Descartar campos que ficarem fora da matriz?'):
            if self.window.winfo_exists(): self.nc.set(len(self.criteria)); self.na.set(len(self.alternatives))
            return
        self.build_matrix(nc,na,old); apply_tree(self.window,self.hub.settings.appearance.theme)
    def example(self):
        if not self.confirmed('Exemplo?', 'Substituir a matriz atual?'): return
        self.build_matrix(3,3,(['Custo-benefício','Desempenho','Facilidade'],['40','35','25'],['Alternativa A','Alternativa B','Alternativa C'],[['9','6','8'],['6','10','7'],['8','8','9']]))
        apply_tree(self.window,self.hub.settings.appearance.theme)
    def calculate(self):
        self.invalidate()
        try: self.result=rank_matrix(*self.values())
        except ValueError as exc: self.status.set(str(exc)); return
        for item in self.result: self.table.insert('', 'end',values=(item.rank,item.name,display_score(item.score)))
        leaders=sum(x.rank==1 for x in self.result)
        if leaders>1:
            detail=f'Empate exato na primeira posição: {leaders} alternativas.'
        else:
            gap=self.result[0].score-self.result[1].score
            detail=f'Primeira posição: {self.result[0].name}. Diferença para a segunda: {display_score(gap)} pontos (arredondada).'
        self.status.set(detail+' Revise as notas e os pesos antes de decidir.')
    def confirm_clear(self):
        if self.confirmed('Limpar?', 'Descartar a matriz?'):
            self.build_matrix(len(self.criteria),len(self.alternatives)); apply_tree(self.window,self.hub.settings.appearance.theme)
    def destroyed(self,event):
        if event.widget is self.window:
            self.release_fields(); self.fields.clear(); self.criteria.clear(); self.weights.clear(); self.alternatives.clear(); self.scores.clear(); self.result=()
    def close(self):
        if self.confirmed('Fechar Decision?', 'Descartar a matriz temporária?'): self.window.destroy()
        return 'break'
