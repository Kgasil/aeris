"""Local conversion UI, no persistence or network."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk
from aeris.convert import UNITS, convert
from aeris.calculator import format_value

class ConvertWindow:
    def __init__(self,hub):
        self.hub=hub; self.window=tk.Toplevel(hub.root)
        self.window.title('Aeris Convert'); self.window.geometry('540x460'); self.window.minsize(420,410)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        f=ttk.Frame(self.window,padding=18);f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Convert',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Diferentes medidas. A mesma simplicidade.',wraplength=380).pack(anchor='w',pady=(0,8))
        self.category=tk.StringVar(self.window,'Comprimento');self.source=tk.StringVar(self.window);self.target=tk.StringVar(self.window);self.amount=tk.StringVar(self.window);self.result=tk.StringVar(self.window);self.status=tk.StringVar(self.window)
        ttk.Label(f,text='Categoria').pack(anchor='w')
        combo=ttk.Combobox(f,textvariable=self.category,values=tuple(UNITS),state='readonly');combo.pack(fill='x');combo.bind('<<ComboboxSelected>>',self.change_category)
        ttk.Label(f,text='De').pack(anchor='w');self.from_box=ttk.Combobox(f,textvariable=self.source,state='readonly');self.from_box.pack(fill='x')
        ttk.Label(f,text='Para').pack(anchor='w');self.to_box=ttk.Combobox(f,textvariable=self.target,state='readonly');self.to_box.pack(fill='x')
        ttk.Label(f,text='Valor (sem separador de milhares)').pack(anchor='w');entry=ttk.Entry(f,textvariable=self.amount);entry.pack(fill='x');entry.bind('<Return>',lambda _:self.run())
        buttons=ttk.Frame(f);buttons.pack(fill='x',pady=8)
        ttk.Button(buttons,text='Converter',command=self.run).pack(side='left',fill='x',expand=True)
        ttk.Button(buttons,text='Inverter unidades',command=self.swap).pack(side='left',fill='x',expand=True,padx=4)
        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left',fill='x',expand=True)
        self.reverse_button=ttk.Button(f,text='Usar resultado na conversão inversa',command=self.reverse_result)
        self.reverse_button.pack(fill='x',pady=(0,4))
        ttk.Label(f,text='Resultado').pack(anchor='w');ttk.Entry(f,textvariable=self.result,state='readonly',font=('Segoe UI',14)).pack(fill='x')
        ttk.Label(f,textvariable=self.status,wraplength=380).pack(anchor='w',pady=6)
        ttk.Label(f,text='Conversões locais. Temperaturas absolutas. gal US = galão americano. MB decimal; MiB binário.',wraplength=380).pack(anchor='w')
        for v in (self.amount,self.source,self.target,self.category):trace_window(self.window, v, self.invalidate)
        self.change_category()
        self.window.bind('<Destroy>',self.destroyed,add='+')
    def invalidate(self,*_):
        self.last_result=None; self.result.set(''); self.status.set('')
        self.reverse_button.configure(state='disabled')

    def reverse_result(self):
        if self.last_result is None: return
        value=format(self.last_result.value,'f')
        if len(value)>64:
            self.status.set('Resultado excede o limite de entrada para inverter.'); return
        a,b=self.source.get(),self.target.get()
        self.source.set(b); self.target.set(a); self.amount.set(value)
        self.run()
    def change_category(self,_=None):
        units=tuple(UNITS[self.category.get()]);self.from_box.configure(values=units);self.to_box.configure(values=units);self.source.set(units[0]);self.target.set(units[1]);self.invalidate()
    def swap(self):
        a,b=self.source.get(),self.target.get();self.source.set(b);self.target.set(a)
    def clear(self):self.amount.set('');self.invalidate()
    def run(self):
        self.invalidate()
        try:r=convert(self.category.get(),self.source.get(),self.target.get(),self.amount.get())
        except ValueError as e:self.status.set(str(e));return
        self.last_result=r
        self.result.set(format_value(r.value)+' '+r.unit);self.status.set(r.explanation)
        self.reverse_button.configure(state='normal')
    def destroyed(self,event):
        if event.widget is self.window:
            try:self.clear()
            except tk.TclError:pass
