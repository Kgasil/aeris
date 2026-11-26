"""Dashboard reuses Data's explicit file selection and cancellable worker."""
import tkinter as tk
from tkinter import ttk
from aeris.data_ui import DataWindow
from aeris.dashboard import dataset_file, aggregate, MODES, DISPLAY_GROUPS
from aeris.permissions import DASHBOARD_READ
from aeris.organizer import safe_name
from aeris.theme import PALETTES


def label(value,limit=45):
    text=safe_name(value)
    return text if len(text)<=limit else text[:limit-1]+'…'

class DashboardWindow(DataWindow):
    permission=DASHBOARD_READ
    title='Aeris Dashboard'
    description='Agregações locais por categoria. Selecione CSV fictício e confira separadores.'
    def __init__(self,hub):
        self.dataset=None; self.summary=None
        super().__init__(hub)
        self.window.geometry('820x740'); self.window.minsize(650,600)
        self.report.configure(height=5)
        frame=self.report.master
        options=ttk.Frame(frame.master); options.pack(fill='x',before=frame,pady=4)
        ttk.Label(options,text='Categoria').pack(side='left')
        self.group_box=ttk.Combobox(options,state='disabled',width=18); self.group_box.pack(side='left',padx=4)
        self.mode_box=ttk.Combobox(options,values=MODES,state='disabled',width=10); self.mode_box.pack(side='left',padx=4); self.mode_box.set(MODES[0])
        ttk.Label(options,text='Métrica').pack(side='left')
        self.metric_box=ttk.Combobox(options,state='disabled',width=18); self.metric_box.pack(side='left',padx=4)
        self.metric_indices=[]
        for widget in (self.group_box,self.mode_box,self.metric_box): widget.bind('<<ComboboxSelected>>',lambda _:self.update_chart())
        self.canvas=tk.Canvas(frame.master,height=260,highlightthickness=0,bg=PALETTES[hub.settings.appearance.theme]['field'])
        self.canvas.pack(fill='x',before=frame,pady=4)
        self.canvas.bind('<Configure>',lambda _:self.draw())
        self.controls()
    def parse(self,path,delimiter,decimal,cancelled):
        return dataset_file(path,delimiter,decimal,cancelled=cancelled)
    def show(self,text):
        self.dataset=None; self.summary=None
        if hasattr(self,'canvas'):
            self.canvas.delete('all'); self.group_box.set(''); self.metric_box.set(''); self.group_box.configure(values=()); self.metric_box.configure(values=()); self.metric_indices=[]; self.controls()
        super().show(text)
    def controls(self):
        super().controls()
        if hasattr(self,'group_box'):
            enabled=self.dataset is not None and self.job is None and self.hub.permissions.allowed(self.permission)
            self.group_box.configure(state='readonly' if enabled else 'disabled')
            self.mode_box.configure(state='readonly' if enabled else 'disabled')
            self.metric_box.configure(state='readonly' if enabled and self.mode_box.get()!='Contagem' and self.metric_indices else 'disabled')
    def render_result(self,result):
        self.dataset=result
        columns=result.profile.columns
        names=[f'{i+1}: {label(c.name,30)}' for i,c in enumerate(columns)]
        self.group_box.configure(values=names); self.group_box.current(0)
        self.metric_indices=[i for i,c in enumerate(columns) if c.kind=='Numérica']
        self.metric_box.configure(values=[names[i] for i in self.metric_indices]); self.metric_box.set('')
        if self.metric_indices: self.metric_box.current(0)
        self.mode_box.set('Contagem'); self.controls(); self.update_chart()
    def update_chart(self):
        if self.dataset is None or not self.hub.permissions.allowed(self.permission): return
        self.controls(); self.summary=None
        try:
            metric=self.metric_box.current()
            self.summary=aggregate(self.dataset,self.group_box.current(),self.mode_box.get(),self.metric_indices[metric] if 0<=metric<len(self.metric_indices) else None)
        except ValueError as exc:
            super().show(str(exc)); self.draw(); return
        s=self.summary
        overall='—' if s.overall is None else f'{s.overall:.10g}'
        mode=self.mode_box.get()
        metric='Média global por registro' if mode=='Média' else 'Total global'
        total=s.included+s.skipped
        coverage=f'{100*s.included/total:.2f}%' if total else '—'
        lines=[f'Registros usados: {s.included} | Ignorados: {s.skipped} | Categorias: {len(s.groups)} | {metric}: {overall}',
               f'Cobertura dos registros: {coverage} | Categorias exibidas: {min(len(s.groups),DISPLAY_GROUPS)}/{len(s.groups)}',
               f'Gráfico e lista: até {DISPLAY_GROUPS} categorias por valor decrescente; cálculo global considera todas. Duplicatas mantidas.']
        lines.extend(f'{label(g.name,80)}: {g.value:.10g} ({g.count} registros)' for g in s.groups[:DISPLAY_GROUPS])
        super().show('\n'.join(lines)); self.draw()
    def draw(self):
        if not hasattr(self,'canvas'): return
        c=self.canvas; c.delete('all'); p=PALETTES[self.hub.settings.appearance.theme]; c.configure(bg=p['field'])
        if self.summary is None or not self.summary.groups: return
        groups=self.summary.groups[:DISPLAY_GROUPS]; w=max(c.winfo_width(),500); h=max(c.winfo_height(),260)
        left=150; right=w-105; top=24; row=(h-top-8)/len(groups)
        lo=min(0,min(g.value for g in groups)); hi=max(0,max(g.value for g in groups)); span=hi-lo
        def x(v): return left+float((v-lo)/span)*(right-left) if span else left
        zero=x(0); c.create_line(zero,top-4,zero,h-5,fill=p['muted']); c.create_text(left,10,text='0 (eixo de referência)',anchor='w',fill=p['deep'],font=('Segoe UI',9))
        for i,g in enumerate(groups):
            y=top+(i+.5)*row; end=x(g.value)
            c.create_text(5,y,text=label(g.name,19),anchor='w',fill=p['deep'],font=('Segoe UI',9))
            if end!=zero: c.create_rectangle(min(zero,end),y-row*.31,max(zero,end),y+row*.31,fill=p['forest'],outline='')
            c.create_text(w-5,y,text=f'{g.value:.6g}',anchor='e',fill=p['deep'],font=('Segoe UI',9))
