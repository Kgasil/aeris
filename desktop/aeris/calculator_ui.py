"""On-demand calculator; results and inputs live only in this window."""
import tkinter as tk
from tkinter import ttk
from aeris.calculator import OPERATIONS, calculate, format_value

class CalculatorWindow:
    def __init__(self,hub):
        self.hub=hub; self.window=tk.Toplevel(hub.root)
        self.window.title('Aeris Calculator'); self.window.geometry('540x480'); self.window.minsize(420,440)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Calculator',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Precisão em cada decisão. Cálculos locais, sem execução de código.',wraplength=390).pack(anchor='w',pady=(0,8))
        self.operation=tk.StringVar(self.window,'Expressão')
        op=ttk.Combobox(f,textvariable=self.operation,values=tuple(OPERATIONS),state='readonly'); op.pack(fill='x')
        op.bind('<<ComboboxSelected>>',self.change_operation)
        self.fields=ttk.Frame(f); self.fields.pack(fill='x',pady=6)
        self.result=tk.StringVar(self.window); self.status=tk.StringVar(self.window)
        buttons=ttk.Frame(f);buttons.pack(fill='x',pady=4)
        ttk.Button(buttons,text='Calcular',command=self.run).pack(side='left',fill='x',expand=True)
        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left',fill='x',expand=True,padx=(5,0))
        ttk.Label(f,text='Resultado').pack(anchor='w',pady=(8,0))
        ttk.Entry(f,textvariable=self.result,state='readonly',font=('Segoe UI',14)).pack(fill='x')
        ttk.Label(f,textvariable=self.status,wraplength=380).pack(anchor='w',pady=6)
        ttk.Label(f,text='Use vírgula ou ponto decimal, sem separador de milhares. Listas: 1; 2; 3. Resultados com 34 dígitos de precisão, sujeitos a arredondamento.',wraplength=380).pack(anchor='w')
        self.inputs=[]
        self.change_operation()
    def invalidate(self,*_):
        self.result.set('');self.status.set('')
    def change_operation(self,_=None):
        self.release_inputs()
        for w in self.fields.winfo_children(): w.destroy()
        self.inputs=[];self.invalidate()
        for label in OPERATIONS[self.operation.get()]:
            ttk.Label(self.fields,text=label).pack(anchor='w')
            v=tk.StringVar(self.window);v.trace_add('write',self.invalidate);self.inputs.append(v)
            entry=ttk.Entry(self.fields,textvariable=v);entry.pack(fill='x',pady=(0,4));entry.bind('<Return>',lambda _:self.run())
    def clear(self):
        for v in self.inputs:v.set('')
        self.invalidate()
    def run(self):
        self.invalidate()
        try:r=calculate(self.operation.get(),*(v.get() for v in self.inputs))
        except ValueError as e:self.status.set(str(e));return
        self.result.set(format_value(r.value)+r.unit);self.status.set(r.explanation)

    def release_inputs(self):
        for v in self.inputs:
            for mode, token in v.trace_info(): v.trace_remove(mode, token)

    def destroyed(self,event):
        if event.widget is self.window:
            try:self.clear()
            except tk.TclError:pass
            self.release_inputs()
