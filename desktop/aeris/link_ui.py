"""Manual inspection only; no browser launching or clipboard access."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk
from aeris.link import inspect_url

class LinkWindow:
    def __init__(self, hub):
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Link')
        self.window.geometry('650x520'); self.window.minsize(490,400)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        frame=ttk.Frame(self.window,padding=18); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Analisar endereço de site',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Análise estrutural local. Nenhum endereço é visitado. HTTPS e ausência de indicadores não garantem segurança.',wraplength=450).pack(anchor='w',pady=6)
        ttk.Label(frame,text='1. Informe o endereço (URL)',font=('Segoe UI',11,'bold')).pack(anchor='w')
        self.url=tk.StringVar(self.window); self.entry=ttk.Entry(frame,textvariable=self.url); self.entry.pack(fill='x',pady=4)
        self.entry.bind('<Return>',lambda _:self.analyze())
        ttk.Button(frame,text='2. Analisar estrutura',command=self.analyze,style='Aeris.Primary.TButton').pack(fill='x')
        ttk.Label(frame,text='3. Revise os indicadores',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,0))
        panel=ttk.Frame(frame); panel.pack(fill='both',expand=True,pady=8)
        self.report=tk.Text(panel,wrap='word',height=12,state='disabled',padx=12,pady=10,relief='flat',highlightthickness=1)
        bar=ttk.Scrollbar(panel,command=self.report.yview); self.report.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y'); self.report.pack(fill='both',expand=True)
        ttk.Button(frame,text='Limpar URL e resultado',command=self.clear).pack(fill='x')
        trace_window(self.window, self.url, lambda *_:self.show('Informe uma URL completa e analise.'))
        self.show('Informe uma URL completa e analise.'); self.entry.focus_set()
    def show(self,value):
        self.report.configure(state='normal'); self.report.delete('1.0','end'); self.report.insert('1.0',value); self.report.configure(state='disabled')
    def analyze(self):
        try: result=inspect_url(self.url.get())
        except ValueError as error: self.show('Não analisado: '+str(error)); return
        lines=[f'Host interpretado localmente: {result.host}',f'Protocolo: {result.scheme.upper()}', '']
        if result.indicators:
            lines.append(f'Indicadores para revisar: {len(result.indicators)} (não é pontuação de risco)'); lines.extend('• '+note for note in result.indicators)
        else: lines.append('Nenhum indicador estrutural desta lista foi encontrado.')
        lines.extend(['','Não é um veredito de segurança. Sem consulta de reputação, DNS, certificado, redirecionamentos ou conteúdo. Confira a origem por um canal confiável.'])
        self.show('\n'.join(lines))
    def clear(self): self.url.set(''); self.entry.focus_set()
