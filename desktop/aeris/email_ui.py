"""Manual draft composition and explicitly authorized clipboard actions."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox
from aeris.email_draft import LANGUAGES, TONES, PURPOSES, compose
from aeris.permissions import COPY_EMAIL

class EmailWindow:
    def __init__(self, hub):
        self.hub=hub; self.draft=None; self.snapshot=None
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris · Email')
        self.window.geometry('600x720'); self.window.minsize(460,610)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Escrever e-mail',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Prepare uma mensagem com modelos locais. Revise antes de copiar; nada será enviado.',wraplength=425).pack(anchor='w')
        opts=ttk.Frame(f); opts.pack(fill='x',pady=(12,8))
        self.language=tk.StringVar(self.window,LANGUAGES[0]); self.tone=tk.StringVar(self.window,TONES[0]); self.purpose=tk.StringVar(self.window,PURPOSES[0])
        for i,(label,var,values) in enumerate((('Idioma',self.language,LANGUAGES),('Tom',self.tone,TONES),('Finalidade',self.purpose,PURPOSES))):
            opts.columnconfigure(i,weight=1); ttk.Label(opts,text=label).grid(row=0,column=i,sticky='w'); ttk.Combobox(opts,textvariable=var,values=values,state='readonly',width=12).grid(row=1,column=i,sticky='ew',padx=2)
        self.recipient=tk.StringVar(self.window); self.subject=tk.StringVar(self.window); self.signature=tk.StringVar(self.window)
        for label,var in (('Nome do destinatário (opcional)',self.recipient),('Assunto (opcional)',self.subject)):
            ttk.Label(f,text=label).pack(anchor='w'); ttk.Entry(f,textvariable=var).pack(fill='x')
        ttk.Label(f,text='1. O que você quer comunicar?').pack(anchor='w')
        self.details=tk.Text(f,height=4,wrap='word',undo=True,padx=10,pady=8,relief='flat',highlightthickness=1); self.details.pack(fill='both',expand=True,pady=3)
        ttk.Label(f,text='Assinatura (opcional)').pack(anchor='w'); ttk.Entry(f,textvariable=self.signature).pack(fill='x')
        ttk.Button(f,text='2. Gerar rascunho',style='Aeris.Primary.TButton',command=self.generate).pack(fill='x',pady=4)
        ttk.Label(f,text='3. Confira a mensagem',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,0))
        self.preview_subject=tk.StringVar(self.window); ttk.Label(f,textvariable=self.preview_subject,wraplength=425).pack(anchor='w')
        self.preview=tk.Text(f,height=5,wrap='word',state='disabled',padx=10,pady=8,relief='flat',highlightthickness=1); self.preview.pack(fill='both',expand=True,pady=3)
        buttons=ttk.Frame(f); buttons.pack(fill='x')
        self.copy_subject=ttk.Button(buttons,text='Copiar assunto',command=lambda:self.copy('subject')); self.copy_subject.pack(side='left',expand=True,fill='x')
        self.copy_body=ttk.Button(buttons,text='Copiar mensagem',command=lambda:self.copy('body')); self.copy_body.pack(side='left',expand=True,fill='x')
        ttk.Button(buttons,text='Limpar',command=self.clear).pack(side='left')
        self.copy_full=ttk.Button(f,text='Copiar assunto e mensagem',command=lambda:self.copy('full'))
        self.copy_full.pack(fill='x',pady=(4,0))
        self.status=tk.StringVar(self.window,'Use dados fictícios. Revise o rascunho antes de copiar.'); ttk.Label(f,textvariable=self.status,wraplength=425).pack(anchor='w',pady=4)
        for v in (self.language,self.tone,self.purpose,self.recipient,self.subject,self.signature): trace_window(self.window, v, self.invalidate)
        self.details.bind('<<Modified>>',self.modified); self.details.edit_modified(False)
        self.permissions_changed()
    def values(self):
        return (self.language.get(),self.tone.get(),self.purpose.get(),self.recipient.get(),self.subject.get(),self.details.get('1.0','end-1c'),self.signature.get())
    def dirty(self): return any(self.values()[3:])
    def modified(self,_=None):
        if self.details.edit_modified():
            self.details.edit_modified(False); self.invalidate()
    def invalidate(self,*_):
        self.draft=None; self.snapshot=None; self.preview_subject.set('Assunto: —')
        self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.configure(state='disabled'); self.permissions_changed()
        self.status.set('Gere um novo rascunho após alterações.')
    def generate(self):
        self.invalidate()
        try: self.draft=compose(*self.values())
        except ValueError as exc: self.status.set(str(exc)); return
        self.snapshot=self.values(); self.preview_subject.set('Assunto: '+self.draft.subject)
        self.preview.configure(state='normal'); self.preview.insert('1.0',self.draft.body); self.preview.configure(state='disabled')
        self.permissions_changed(); self.status.set('Revise os dados; o modelo não traduz nem corrige os detalhes.')
    def permissions_changed(self):
        state='normal' if self.draft is not None and self.hub.permissions.allowed(COPY_EMAIL) else 'disabled'
        self.copy_subject.configure(state=state); self.copy_body.configure(state=state); self.copy_full.configure(state=state)
    def copy(self,part):
        if part not in ('subject','body','full') or self.draft is None or self.snapshot!=self.values() or not self.hub.permissions.allowed(COPY_EMAIL): return
        reviewed=self.draft; snapshot=self.snapshot
        payload=('Assunto: '+reviewed.subject+'\n\n'+reviewed.body) if part=='full' else getattr(reviewed,part)
        if not messagebox.askyesno('Copiar rascunho?', 'O conteúdo substituirá o clipboard e poderá permanecer no histórico do sistema.',parent=self.window): return
        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_EMAIL): return
        if self.draft is not reviewed or self.snapshot!=snapshot or snapshot!=self.values():
            self.invalidate(); self.status.set('Rascunho alterado. Gere novamente.'); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(payload)
        except tk.TclError: self.status.set('Não foi possível copiar.'); return
        self.status.set('Copiado. Cole manualmente no aplicativo de e-mail.')
    def clear(self):
        for v in (self.recipient,self.subject,self.signature): v.set('')
        self.details.delete('1.0','end'); self.details.edit_reset(); self.invalidate(); self.status.set('Rascunho descartado; clipboard não alterado.')
    def close(self):
        if self.dirty() and not messagebox.askyesno('Fechar Email?', 'Descartar rascunho desta janela?',parent=self.window): return
        self.window.destroy()
