"""Report preview, explicit read and independently authorized copy."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.data_ui import DataWindow
from aeris.dashboard import dataset_file, MODES
from aeris.report import build_report, label
from aeris.permissions import REPORT_READ, REPORT_COPY


class ReportWindow(DataWindow):
    permission=REPORT_READ
    title='Aeris Report'
    display_title='Gerar relatório'
    description='Gere um relatório de qualidade e estatísticas de um CSV. Revise antes de copiar; use dados fictícios.'

    def __init__(self,hub):
        self.dataset=None; self.output=None; self.metric_indices=[]; self.output_context=None; self.generation=0
        super().__init__(hub)
        self.window.geometry('900x760'); self.window.minsize(650,600)
        f=self.report.master.master
        options=ttk.Frame(f); options.pack(fill='x',before=self.report.master,pady=4)
        ttk.Label(options,text='Agrupar por (opcional)').pack(side='left')
        self.group_box=ttk.Combobox(options,width=20,state='disabled'); self.group_box.pack(side='left',padx=4)
        ttk.Label(options,text='Cálculo').pack(side='left')
        self.mode_box=ttk.Combobox(options,values=MODES,width=10,state='disabled'); self.mode_box.set('Contagem'); self.mode_box.pack(side='left',padx=4)
        ttk.Label(options,text='Métrica').pack(side='left')
        self.metric_box=ttk.Combobox(options,width=20,state='disabled'); self.metric_box.pack(side='left',padx=4)
        for w in (self.group_box,self.mode_box,self.metric_box): w.bind('<<ComboboxSelected>>',lambda _:self.generate())
        self.copy_button=ttk.Button(f,text='Copiar relatório revisado',command=self.copy,style='Aeris.Primary.TButton'); self.copy_button.pack(fill='x',pady=4)
        self.status=tk.StringVar(self.window,''); ttk.Label(f,textvariable=self.status,wraplength=600).pack(anchor='w')
        self.controls()

    def parse(self,path,delimiter,decimal,cancelled):
        return dataset_file(path,delimiter,decimal,cancelled=cancelled)

    def show(self,text):
        self.dataset=None; self.output=None; self.metric_indices=[]; self.output_context=None; self.generation+=1
        if hasattr(self,'group_box'):
            for w in (self.group_box,self.metric_box): w.set(''); w.configure(values=())
            self.status.set(''); self.controls()
        super().show(text)

    def controls(self):
        super().controls()
        if hasattr(self,'copy_button'):
            enabled=self.dataset is not None and self.job is None and self.hub.permissions.allowed(REPORT_READ)
            self.group_box.configure(state='readonly' if enabled else 'disabled')
            aggregation=enabled and self.group_box.current()>0
            self.mode_box.configure(state='readonly' if aggregation else 'disabled')
            self.metric_box.configure(state='readonly' if aggregation and self.mode_box.get()!='Contagem' and self.metric_indices else 'disabled')
            self.copy_button.configure(state='normal' if enabled and self.output is not None and self.hub.permissions.allowed(REPORT_COPY) else 'disabled')

    def render_result(self,result):
        self.dataset=result
        names=[f'{i+1}: {label(c.name,28)}' for i,c in enumerate(result.profile.columns)]
        self.group_box.configure(values=['Sem agregação',*names]); self.group_box.current(0)
        self.metric_indices=[i for i,c in enumerate(result.profile.columns) if c.kind=='Numérica']
        self.metric_box.configure(values=[names[i] for i in self.metric_indices]); self.metric_box.set('')
        if self.metric_indices: self.metric_box.current(0)
        self.mode_box.set('Contagem'); self.generate()

    def report_context(self):
        return (self.context(),id(self.dataset),self.group_box.current(),self.mode_box.get(),self.metric_box.current())
    def generate(self):
        self.generation+=1; self.output=None; self.output_context=None; self.status.set('')
        if self.dataset is None or self.job or not self.hub.permissions.allowed(REPORT_READ): self.controls(); return
        try:
            group=self.group_box.current()-1; metric=self.metric_box.current()
            self.output=build_report(self.dataset,group if group>=0 else None,self.mode_box.get(),self.metric_indices[metric] if 0<=metric<len(self.metric_indices) else None)
        except ValueError as exc: super().show(str(exc))
        else: self.output_context=self.report_context(); super().show(self.output)
        self.controls()

    def copy(self):
        output=self.output
        if output is None or not all(self.hub.permissions.allowed(p) for p in (REPORT_READ,REPORT_COPY)): return
        if self.output_context!=self.report_context(): self.generate(); return
        generation=self.generation; reviewed=self.output_context
        if not messagebox.askyesno('Copiar relatório?', 'O relatório pode conter dados pessoais. O clipboard será substituído e o histórico do sistema pode reter o texto.',parent=self.window): return
        if not self.window.winfo_exists() or not all(self.hub.permissions.allowed(p) for p in (REPORT_READ,REPORT_COPY)): return
        if self.generation!=generation or self.output is not output or self.output_context!=reviewed or self.report_context()!=reviewed:
            self.generate(); self.status.set('Relatório alterado. Revise novamente.'); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(output)
        except tk.TclError: self.status.set('Falha ao copiar.'); return
        self.status.set('Copiado. Cole manualmente no destino.')
