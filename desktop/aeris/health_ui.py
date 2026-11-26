"""One-shot diagnostic; no periodic polling when idle or closed."""
import tkinter as tk
from tkinter import ttk
from aeris.health import sample, measure, resident_memory

class HealthWindow:
    def __init__(self, hub):
        self.hub=hub; self.pending=None; self.start=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris Health')
        self.window.geometry('610x440'); self.window.minsize(460,360)
        self.window.protocol('WM_DELETE_WINDOW',self.window.destroy)
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=14); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris Health',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Diagnóstico do processo atual. Não inclui processos auxiliares, navegador ou sistema. Nenhum histórico ou envio.',wraplength=425).pack(anchor='w',pady=8)
        self.status=tk.StringVar(self.window,'Pronto para medir.'); self.report=tk.StringVar(self.window,'Sem amostra.')
        ttk.Label(f,textvariable=self.report,wraplength=420,justify='left').pack(fill='both',expand=True)
        ttk.Label(f,textvariable=self.status,wraplength=420).pack(anchor='w',pady=8)
        self.button=ttk.Button(f,text='Medir por aproximadamente 2 segundos',command=self.run); self.button.pack(fill='x')
        self.stop=ttk.Button(f,text='Cancelar / limpar',command=self.clear); self.stop.pack(fill='x',pady=4)
        ttk.Label(f,text='CPU: 100% equivale a um núcleo lógico. Memória: conjunto residente (MiB), não alocação exclusiva. Sem veredito de desempenho.',wraplength=425).pack(anchor='w',pady=5)

    def run(self):
        if self.pending is not None or not self.hub.enabled('Health'): return
        self.report.set('Sem amostra.'); self.status.set('Medindo… deixe o Aeris em repouso para uma estimativa de ociosidade.')
        self.button.configure(state='disabled'); self.start=sample()
        self.pending=self.window.after(2000,self.finish)

    def finish(self):
        self.pending=None
        start=self.start; self.start=None
        self.button.configure(state='normal')
        if start is None or not self.hub.enabled('Health'):
            self.status.set('Medição cancelada.'); self.report.set('Sem amostra.')
            return
        try: result=measure(start,sample(),resident_memory())
        except ValueError: self.status.set('Amostra inválida. Tente novamente.'); return
        memory='Indisponível' if result.resident_bytes is None else f'{result.resident_bytes/1048576:.2f} MiB'
        names=[name for name,_ in self.hub.active_tools()]
        self.report.set(f'CPU do processo: {result.cpu_percent:.2f}%\nMemória residente: {memory}\nIntervalo real: {result.seconds:.2f} s\nMódulos opcionais ativos ao final: {len(names)}\n'+', '.join(names))
        self.status.set('Amostra concluída. Não é benchmark de inicialização nem de atalhos.')

    def cancel(self):
        if self.pending is not None:
            self.window.after_cancel(self.pending); self.pending=None
        self.start=None

    def clear(self):
        self.cancel(); self.button.configure(state='normal'); self.status.set('Pronto para medir.'); self.report.set('Sem amostra.')

    def destroyed(self,event):
        if event.widget is self.window: self.cancel()
