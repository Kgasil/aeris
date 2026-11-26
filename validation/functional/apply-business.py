"""Checked Business refinement: local calculations and reviewed CSV analysis."""
from pathlib import Path
import hashlib
import sys

def replace(s,old,new):
    if s.count(old)!=1: raise ValueError("Unexpected anchor: "+old[:100])
    return s.replace(old,new,1)

def apply(root):
    root=Path(root)/"aeris"
    hashes={
        "data_ui.py":"78ef4f44af78a3d9e9588a9e0a44d777ce82fea78f3ccab4f634f3cc4e2ee0df",
        "dashboard_ui.py":"48ccb38d5a5544c281034bf6529104ab7119e51e4513fef425cd7d4289f98e78",
        "report_ui.py":"e0e92d05dd3d0dde7da56dc1e992c93327191f43e9ca1abb2ccde42c06eef4aa",
        "report.py":"152e5c07c95c8a260047603c2dbcc913a326fe0d4591de3cab35bf4f9b346fd5",
        "calculator.py":"d37164637e8ce130f32029e45da47cbe45c80e4fd60e2750a623576efaaf433e",
        "decision_ui.py":"a10b29a7a853fc354144f3faf668eda1814adcbc21126e03c224f0ec1701f1d9",
    }
    files={}
    for name,expected in hashes.items():
        raw=(root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("Unexpected RC4 file: "+name)
        files[name]=raw.decode("utf-8").replace("\r\n","\n")
    s=files["data_ui.py"]
    s=replace(s,"from aeris.organizer import safe_name","from aeris.organizer import safe_name\nfrom aeris.window_lifecycle import trace_window")
    s=replace(s,"self.job=None; self.timer=None; self.path=None","self.job=None; self.timer=None; self.path=None; self.revision=0; self.request=None")
    s=replace(s,"        for widget in (self.delim_box,self.dec_box): widget.bind('<<ComboboxSelected>>',lambda _:self.show('Resultado pendente.'))","")
    s=replace(s,"        self.permissions_changed()\n    def show", """        self.permissions_changed()
        for var in (self.delimiter,self.decimal): trace_window(self.window,var,self.options_changed)
    def context(self):
        return (self.revision,self.path,self.delimiter.get(),self.decimal.get())
    def options_changed(self,*_):
        self.revision+=1; self.cancel(); self.show('Separadores alterados. Analise novamente.')
    def show""")
    s=replace(s,"        value=filedialog.askopenfilename", "        reviewed=self.context()\n        value=filedialog.askopenfilename")
    s=replace(s,"        if value and self.hub.permissions.allowed(self.permission):\n            self.path=value;", """        if value and self.window.winfo_exists() and self.hub.permissions.allowed(self.permission) and self.job is None and reviewed==self.context():
            self.revision+=1; self.path=value;""")
    s=replace(s,"        if not messagebox.askyesno('Analisar CSV?',","        reviewed=self.context()\n        if not messagebox.askyesno('Analisar CSV?',")
    s=replace(s,"        if not self.window.winfo_exists() or not self.path or not self.hub.permissions.allowed(self.permission): return\n        event=threading.Event();", """        if not self.window.winfo_exists() or not self.path or self.job or not self.hub.permissions.allowed(self.permission): return
        if reviewed!=self.context(): self.show('Seleção alterada. Confirme novamente.'); return
        self.request=reviewed
        event=threading.Event();""")
    s=replace(s,"        self.job=None; self.controls()\n        if event.is_set() or not self.hub.permissions.allowed(self.permission): return","""        self.job=None; reviewed=self.request; self.request=None; self.controls()
        if event.is_set() or reviewed!=self.context() or not self.hub.permissions.allowed(self.permission): return""")
    s=replace(s,"        for col in result.columns:\n            lines.append", """        cells=result.rows*len(result.columns)
        missing=f'{100*result.missing/cells:.2f}%' if cells else '—'
        duplicates=f'{100*result.duplicates/result.rows:.2f}%' if result.rows else '—'
        lines.append(f'Células ausentes: {missing} | Duplicatas adicionais por registro: {duplicates}')
        for col in result.columns:
            lines.append""")
    s=replace(s,"        self.cancel(); self.path=None;", "        self.revision+=1; self.cancel(); self.path=None;")
    files["data_ui.py"]=s
    s=files["dashboard_ui.py"]
    s=replace(s,"        lines=[f'Registros usados: {s.included} | Ignorados: {s.skipped} | Categorias: {len(s.groups)} | Total/média global: {overall}',f'Gráfico e lista: até {DISPLAY_GROUPS} categorias por valor decrescente; total global considera todas. Duplicatas mantidas.']", """        mode=self.mode_box.get()
        metric='Média global por registro' if mode=='Média' else 'Total global'
        total=s.included+s.skipped
        coverage=f'{100*s.included/total:.2f}%' if total else '—'
        lines=[f'Registros usados: {s.included} | Ignorados: {s.skipped} | Categorias: {len(s.groups)} | {metric}: {overall}',
               f'Cobertura dos registros: {coverage} | Categorias exibidas: {min(len(s.groups),DISPLAY_GROUPS)}/{len(s.groups)}',
               f'Gráfico e lista: até {DISPLAY_GROUPS} categorias por valor decrescente; cálculo global considera todas. Duplicatas mantidas.']""")
    files["dashboard_ui.py"]=s
    s=files["report.py"]
    s=replace(s,"    lines=['AERIS REPORT", """    cells=p.rows*len(p.columns)
    missing=f'{100*p.missing/cells:.2f}%' if cells else '—'
    duplicates=f'{100*p.duplicates/p.rows:.2f}%' if p.rows else '—'
    lines=['AERIS REPORT""")
    s=replace(s,"           'Ausentes = campos vazios ou somente espaços.", """           f'Taxa de células ausentes: {missing} | Duplicatas adicionais por registro: {duplicates}',
           'Ausentes = campos vazios ou somente espaços.""")
    s=replace(s,"        lines.append(f'Registros usados: {summary.included} | Ignorados: {summary.skipped} | Categorias: {len(summary.groups)}')", """        lines.append(f'Registros usados: {summary.included} | Ignorados: {summary.skipped} | Categorias: {len(summary.groups)}')
        total=summary.included+summary.skipped
        coverage=f'{100*summary.included/total:.2f}%' if total else '—'
        lines.append(f'Cobertura dos registros: {coverage}')""")
    files["report.py"]=s
    s=files["report_ui.py"]
    s=replace(s,"self.dataset=None; self.output=None; self.metric_indices=[]\n        super().__init__", "self.dataset=None; self.output=None; self.metric_indices=[]; self.output_context=None; self.generation=0\n        super().__init__")
    s=replace(s,"        self.dataset=None; self.output=None; self.metric_indices=[]\n        if hasattr", "        self.dataset=None; self.output=None; self.metric_indices=[]; self.output_context=None; self.generation+=1\n        if hasattr")
    s=replace(s,"    def generate(self):\n        self.output=None; self.status.set('')","""    def report_context(self):
        return (self.context(),id(self.dataset),self.group_box.current(),self.mode_box.get(),self.metric_box.current())
    def generate(self):
        self.generation+=1; self.output=None; self.output_context=None; self.status.set('')""")
    s=replace(s,"        else: super().show(self.output)","        else: self.output_context=self.report_context(); super().show(self.output)")
    s=replace(s,"        if not messagebox.askyesno('Copiar relatório?',","        if self.output_context!=self.report_context(): self.generate(); return\n        generation=self.generation; reviewed=self.output_context\n        if not messagebox.askyesno('Copiar relatório?',")
    s=replace(s,"        if not self.window.winfo_exists() or self.output is not output or not all(self.hub.permissions.allowed(p) for p in (REPORT_READ,REPORT_COPY)): return", """        if not self.window.winfo_exists() or not all(self.hub.permissions.allowed(p) for p in (REPORT_READ,REPORT_COPY)): return
        if self.generation!=generation or self.output is not output or self.output_context!=reviewed or self.report_context()!=reviewed:
            self.generate(); self.status.set('Relatório alterado. Revise novamente.'); return""")
    files["report_ui.py"]=s
    s=files["calculator.py"]
    s=replace(s,"    'Margem (%)': ('Receita', 'Custo'), 'Markup (%)': ('Receita', 'Custo'),","    'Margem (%)': ('Receita', 'Custo'), 'Markup (%)': ('Receita', 'Custo'),\n    'Variação (%)': ('Valor inicial positivo', 'Valor final'),")
    s=replace(s,"    'Desvio padrão populacional': ('Valores separados por ponto e vírgula',),","    'Desvio padrão populacional': ('Valores separados por ponto e vírgula',),\n    'Desvio padrão amostral': ('Valores separados por ponto e vírgula',),")
    s=replace(s,"if operation in ('Média','Mediana','Desvio padrão populacional'):","if operation in ('Média','Mediana','Desvio padrão populacional','Desvio padrão amostral'):")
    s=replace(s,"                else: v=(sum((x-mean)**2 for x in nums)/n).sqrt(); formula='Raiz da soma dos desvios quadráticos / n (variância populacional)'", """                elif operation=='Desvio padrão amostral':
                    if n<2: raise ValueError('Informe pelo menos dois valores para a amostra.')
                    v=(sum((x-mean)**2 for x in nums)/(n-1)).sqrt(); formula='Raiz da soma dos desvios quadráticos / (n - 1)'
                else: v=(sum((x-mean)**2 for x in nums)/n).sqrt(); formula='Raiz da soma dos desvios quadráticos / n (variância populacional)'""")
    s=replace(s,"                elif operation=='Juros compostos':","""                elif operation=='Variação (%)':
                    if a<=0: raise ValueError('O valor inicial deve ser positivo.')
                    v=(vals[1]-a)/a*100; unit='%'; formula='(Valor final - Valor inicial) / Valor inicial × 100'
                elif operation=='Juros compostos':""")
    files["calculator.py"]=s
    s=files["decision_ui.py"]
    s=replace(s,"self.result=(); self.fields=[]","self.result=(); self.fields=[]; self.matrix_generation=0")
    s=replace(s,"        self.release_fields()\n        for widget", "        self.matrix_generation+=1\n        self.release_fields()\n        for widget")
    s=replace(s,"    def resize(self):\n        nc,na=self.nc.get(),self.na.get(); old=self.values()", """    def snapshot(self):
        return (self.matrix_generation,self.values(),self.nc.get(),self.na.get())
    def confirmed(self,title,prompt):
        reviewed=self.snapshot()
        if self.dirty() and not messagebox.askyesno(title,prompt,parent=self.window): return False
        if not self.window.winfo_exists(): return False
        if reviewed!=self.snapshot():
            self.status.set('Matriz alterada. Confirme novamente.'); return False
        return True
    def resize(self):
        nc,na=self.nc.get(),self.na.get(); old=self.values()""")
    s=replace(s,"        if (nc<len(old[0]) or na<len(old[2])) and self.dirty() and not messagebox.askyesno('Redimensionar?', 'Descartar campos que ficarem fora da matriz?',parent=self.window):\n            self.nc.set(len(old[0])); self.na.set(len(old[2])); return", """        if (nc<len(old[0]) or na<len(old[2])) and not self.confirmed('Redimensionar?', 'Descartar campos que ficarem fora da matriz?'):
            if self.window.winfo_exists(): self.nc.set(len(self.criteria)); self.na.set(len(self.alternatives))
            return""")
    s=replace(s,"        if self.dirty() and not messagebox.askyesno('Exemplo?', 'Substituir a matriz atual?',parent=self.window): return","        if not self.confirmed('Exemplo?', 'Substituir a matriz atual?'): return")
    s=replace(s,"        self.status.set('Ranking calculado. Revise as notas e os pesos antes de decidir.')", """        leaders=sum(x.rank==1 for x in self.result)
        if leaders>1:
            detail=f'Empate exato na primeira posição: {leaders} alternativas.'
        else:
            gap=self.result[0].score-self.result[1].score
            detail=f'Primeira posição: {self.result[0].name}. Diferença para a segunda: {display_score(gap)} pontos (arredondada).'
        self.status.set(detail+' Revise as notas e os pesos antes de decidir.')""")
    s=replace(s,"        if not self.dirty() or messagebox.askyesno('Limpar?', 'Descartar a matriz?',parent=self.window):","        if self.confirmed('Limpar?', 'Descartar a matriz?'):")
    s=replace(s,"        if not self.dirty() or messagebox.askyesno('Fechar Decision?', 'Descartar a matriz temporária?',parent=self.window): self.window.destroy()","        if self.confirmed('Fechar Decision?', 'Descartar a matriz temporária?'): self.window.destroy()")
    files["decision_ui.py"]=s
    for name,code in files.items(): compile(code,name,"exec")
    for name,code in files.items(): (root/name).write_bytes(code.encode("utf-8"))
    print("Business: six original RC4 files verified and refined")

if __name__=="__main__": apply(sys.argv[1])
