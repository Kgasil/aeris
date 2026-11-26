"""Manual practice window. No microphone, external data, live interview or scoring AI."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.interview import AREAS, QUESTIONS, CRITERIA

class InterviewWindow:
    def __init__(self,hub):
        self.hub=hub; self.store=hub.interview_store
        self.window=w=tk.Toplevel(hub.root); w.title('Aeris Interview'); w.geometry('720x690'); w.minsize(590,590)
        self.area=tk.StringVar(w,AREAS[0]); self.current_area=AREAS[0]; self.index=0
        self.question=tk.StringVar(w); self.progress=tk.StringVar(w); self.status=tk.StringVar(w); self.hint=tk.StringVar(w)
        f=ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Interview',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Treinamento individual. Autoavaliação subjetiva; não é nota de seleção.',wraplength=550).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=4)
        ttk.Label(row,text='Área').pack(side='left'); combo=ttk.Combobox(row,textvariable=self.area,values=AREAS,state='readonly'); combo.pack(side='left',padx=8); combo.bind('<<ComboboxSelected>>',self.change_area)
        ttk.Label(f,textvariable=self.progress).pack(anchor='w')
        ttk.Label(f,textvariable=self.question,wraplength=550,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=5)
        row=ttk.Frame(f); row.pack(fill='both',expand=True)
        self.answer=tk.Text(row,height=6,wrap='word'); sb=ttk.Scrollbar(row,command=self.answer.yview); self.answer.configure(yscrollcommand=sb.set); self.answer.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        self.checks=[tk.BooleanVar(w,False) for _ in CRITERIA]
        ttk.Label(f,text='Autoavaliação (opcional; marque após revisar)').pack(anchor='w',pady=(6,0))
        for label,var in zip(CRITERIA,self.checks): ttk.Checkbutton(f,text=label,variable=var).pack(anchor='w')
        ttk.Button(f,text='Revelar orientação de estudo',command=self.reveal).pack(anchor='w',pady=3)
        ttk.Label(f,textvariable=self.hint,wraplength=550).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=5)
        self.prev=ttk.Button(row,text='Anterior',command=lambda:self.move(-1)); self.prev.pack(side='left')
        self.next=ttk.Button(row,text='Próxima',command=lambda:self.move(1)); self.next.pack(side='left',padx=3)
        self.pending=ttk.Button(f,text='Próxima pergunta sem resposta nesta área',command=self.next_unanswered); self.pending.pack(anchor='w')
        ttk.Button(row,text='Salvar resposta',command=self.save).pack(side='left',padx=3)
        ttk.Button(row,text='Limpar resposta',command=self.delete).pack(side='left',padx=3)
        ttk.Label(f,textvariable=self.status,wraplength=550).pack(anchor='w')
        w.protocol('WM_DELETE_WINDOW',self.close); w.bind('<Escape>',lambda _:self.close()); self.render()
    def questions(self): return tuple(q for q in QUESTIONS if q.area==self.current_area)
    def current(self): return self.questions()[self.index]
    def values(self): return self.answer.get('1.0','end-1c'),tuple(v.get() for v in self.checks)
    def dirty(self):
        item=self.store.get(self.current().id)
        return self.values()!=((item.answer,item.criteria) if item else ('',(False,)*len(CRITERIA)))
    def discard_ok(self): return not self.dirty() or messagebox.askyesno('Descartar rascunho?', 'Descartar alterações não salvas?',parent=self.window)
    def update_progress(self):
        done,total=self.store.progress(self.current_area); self.progress.set(f'Pergunta {self.index+1}/{total} · {done}/{total} respostas salvas nesta área')
    def render(self):
        q=self.current(); self.question.set(q.prompt); self.hint.set(''); self.status.set(''); self.answer.delete('1.0','end')
        item=self.store.get(q.id)
        if item: self.answer.insert('1.0',item.answer); self.status.set(f'Autoavaliação salva: {item.count}/{len(CRITERIA)} critérios marcados.')
        for i,var in enumerate(self.checks): var.set(item.criteria[i] if item else False)
        self.prev.configure(state='normal' if self.index else 'disabled'); self.next.configure(state='normal' if self.index+1<len(self.questions()) else 'disabled'); self.update_progress()
    def change_area(self,_=None):
        new=self.area.get()
        if new==self.current_area: return
        if new not in AREAS or not self.navigation_ok():
            if self.window.winfo_exists(): self.area.set(self.current_area)
            return
        if self.area.get()!=new: self.area.set(self.current_area); return
        self.current_area=new; self.index=0; self.render()
    def navigation_ok(self):
        before=(self.current().id,self.values(),self.store.get(self.current().id))
        if not self.discard_ok() or not self.window.winfo_exists(): return False
        if before!=(self.current().id,self.values(),self.store.get(self.current().id)):
            self.status.set('Resposta alterada. Confirme novamente.'); return False
        return True
    def move(self,delta):
        target=self.index+delta
        if 0<=target<len(self.questions()) and self.navigation_ok():
            self.index=target; self.render()
    def next_unanswered(self):
        qs=self.questions()
        indices=[(self.index+i)%len(qs) for i in range(1,len(qs)+1)]
        target=next((i for i in indices if self.store.get(qs[i].id) is None),None)
        if target is None: self.status.set('Todas as perguntas desta área têm resposta salva.'); return
        if target==self.index: self.status.set('Esta pergunta ainda não tem resposta salva.'); return
        if self.navigation_ok() and self.store.get(qs[target].id) is None:
            self.index=target; self.render()
    def reveal(self): self.hint.set(self.current().hint)
    def refresh_privacy(self):
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def save(self):
        try: item=self.store.save(self.current().id,*self.values())
        except ValueError as exc: self.status.set(str(exc)); return
        self.update_progress(); self.refresh_privacy(); self.status.set(f'Resposta salva na sessão. Autoavaliação: {item.count}/{len(CRITERIA)} critérios marcados (não é nota).')
    def delete(self):
        q=self.current().id; draft=self.values(); item=self.store.get(q)
        if not messagebox.askyesno('Limpar resposta?', 'Descartar resposta salva e rascunho desta pergunta?',parent=self.window): return
        if not self.window.winfo_exists(): return
        if self.current().id!=q or self.values()!=draft or self.store.get(q) is not item:
            self.status.set('Resposta alterada. Confirme novamente.'); return
        self.store.delete(q); self.render(); self.refresh_privacy()
    def close(self):
        if self.navigation_ok(): self.window.destroy()
        return 'break'
