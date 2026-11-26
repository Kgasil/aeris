"""Local transformations and opt-in automatic correction within this editor."""
import tkinter as tk
import queue
from aeris.local_worker import worker_for
from aeris.window_lifecycle import trace_window
from tkinter import ttk, messagebox, simpledialog
from aeris.text import OPERATIONS, LIMIT, stats, transform
from aeris.permissions import COPY_TEXT, TEXT_AI
from aeris.intelligent_text import LANGUAGES, review, cursor_after, dictionary_words
from aeris.contextual_text import contextual_review, validate_source

class TextWindow:
    def __init__(self, hub):
        self.hub=hub; self.output=None; self.result_context=None; self.result_generation=0; self.pending=None; self.reviewed=None; self.snapshot=None; self.changing=False
        self.dictionary={lang:frozenset() for lang in LANGUAGES}; self.ai_generation=0; self.ai_busy=False; self.ai_timer=None; self.ai_results=queue.Queue(); self.ai_preview=False
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris · Text')
        self.window.geometry('660x760'); self.window.minsize(480,660)
        self.window.protocol('WM_DELETE_WINDOW', self.window.destroy)
        self.window.bind('<Escape>', lambda _:self.window.destroy())
        self.window.bind('<Destroy>', self.destroyed, add='+')
        f=ttk.Frame(self.window,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Text',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='Transformações locais. Revise antes de copiar. Use dados fictícios.',wraplength=410).pack(anchor='w')
        self.input=tk.Text(f,height=6,wrap='word',undo=True); self.input.pack(fill='both',expand=True,pady=4)
        self.count=tk.StringVar(self.window); ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.operation=tk.StringVar(self.window,OPERATIONS[0]); choice=ttk.Combobox(f,textvariable=self.operation,values=OPERATIONS,state='readonly'); choice.pack(fill='x',pady=4)
        trace_window(self.window, self.operation, self.invalidate)
        self.go=ttk.Button(f,text='Transformar',command=self.apply); self.go.pack(fill='x')
        options=ttk.Frame(f); options.pack(fill='x',pady=4)
        self.language=tk.StringVar(self.window,LANGUAGES[0]); self.mode=tk.StringVar(self.window,'Desligado')
        ttk.Combobox(options,textvariable=self.language,values=LANGUAGES,state='readonly',width=16).pack(side='left',fill='x',expand=True)
        ttk.Combobox(options,textvariable=self.mode,values=('Desligado','Sugerir','Automático'),state='readonly',width=13).pack(side='left',padx=4)
        ttk.Button(options,text='Revisar agora',command=self.review_now).pack(side='left')
        extras=ttk.Frame(f); extras.pack(fill='x',pady=3)
        ttk.Button(extras,text='Dicionário da sessão',command=self.edit_dictionary).pack(side='left')
        self.ai_button=ttk.Button(extras,text='Revisar com IA local',command=self.ask_ai); self.ai_button.pack(side='left',padx=4)
        ttk.Button(extras,text='Permissões',command=self.hub.open_permissions).pack(side='left')
        correction=ttk.Frame(f); correction.pack(fill='x')
        self.accept_button=ttk.Button(correction,text='Aplicar revisão',command=self.accept); self.accept_button.pack(side='left',fill='x',expand=True)
        self.undo_button=ttk.Button(correction,text='Desfazer revisão',command=self.undo_review,state='disabled'); self.undo_button.pack(side='left',fill='x',expand=True)
        trace_window(self.window, self.language, self.mode_changed); trace_window(self.window, self.mode, self.mode_changed)
        self.details=tk.StringVar(self.window,'Correção local limitada; modo automático altera apenas este editor.'); ttk.Label(f,textvariable=self.details,wraplength=500).pack(anchor='w')
        ttk.Label(f,text='Resultado (prévia; original preservado)').pack(anchor='w',pady=(6,0))
        self.result=tk.Text(f,height=6,wrap='word',state='disabled'); self.result.pack(fill='both',expand=True,pady=4)
        self.input.tag_configure('revision',background='#F3D5D5',foreground='#632828'); self.result.tag_configure('revision',background='#DCEFE3',foreground='#285640')
        self.result_count=tk.StringVar(self.window); ttk.Label(f,textvariable=self.result_count).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x')
        self.copy_button=ttk.Button(row,text='Copiar resultado',command=self.copy); self.copy_button.pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Limpar',command=self.clear).pack(side='left',padx=4)
        self.status=tk.StringVar(self.window,'Selecione uma operação.'); ttk.Label(f,textvariable=self.status,wraplength=410).pack(anchor='w',pady=4)
        self.input.bind('<<Modified>>', self.modified); self.input.edit_modified(False)
        self.invalidate()
    def modified(self,_=None):
        if self.input.edit_modified():
            self.input.edit_modified(False)
            if not self.changing: self.invalidate(); self.schedule()
    def original(self): return self.input.get('1.0','end-1c')
    def invalidate(self,*_):
        self.invalidate_ai(); self.cancel_pending(); self.reviewed=None; self.accept_button.configure(state='disabled'); self.details.set('Correção local limitada; revise os resultados.'); self.set_result(None)
        try:
            s=stats(self.original()); self.count.set(f'{s.words} palavras · {s.characters}/{LIMIT} caracteres · {s.lines} linhas'); self.go.configure(state='normal')
        except ValueError:
            self.count.set('Entrada inválida ou acima do limite.'); self.go.configure(state='disabled')
        self.status.set('Selecione uma operação e revise o resultado.')
    def context(self):
        return (self.original(),self.operation.get(),self.language.get(),self.mode.get(),self.dictionary[self.language.get()])

    def set_result(self,value):
        self.result_generation+=1
        self.result_context=self.context() if value is not None else None
        self.input.tag_remove('revision','1.0','end'); self.result.tag_remove('revision','1.0','end')
        self.output=value; self.result.configure(state='normal'); self.result.delete('1.0','end'); self.result.insert('1.0',value or ''); self.result.configure(state='disabled')
        if value is not None:
            s=stats(value); self.result_count.set(f'{s.words} palavras · {s.characters} caracteres · {s.lines} linhas')
        else: self.result_count.set('')
        self.permissions_changed()
    def permissions_changed(self):
        allowed=self.hub.permissions.allowed(TEXT_AI)
        if not allowed and (self.ai_busy or self.ai_preview):
            self.ai_generation+=1
            if self.ai_preview:
                self.ai_preview=False; self.reviewed=None; self.accept_button.configure(state='disabled'); self.set_result(None); self.status.set('Permissão de IA revogada; prévia descartada.')
        self.ai_button.configure(state='normal' if allowed and not self.ai_busy else 'disabled')
        self.copy_button.configure(state='normal' if self.output is not None and self.hub.permissions.allowed(COPY_TEXT) else 'disabled')
    def apply(self):
        self.invalidate_ai(); self.cancel_pending(); self.reviewed=None; self.accept_button.configure(state='disabled')
        try: self.set_result(transform(self.original(),self.operation.get()))
        except ValueError as e: self.set_result(None); self.status.set(str(e)); return
        self.status.set('Resultado local. Revise espaçamento e formatação; não é correção gramatical.')
    def copy(self):
        if self.output is None or not self.hub.permissions.allowed(COPY_TEXT): return
        if self.result_context!=self.context() or (self.ai_preview and not self.hub.permissions.allowed(TEXT_AI)):
            self.invalidate(); return
        reviewed=self.output; generation=self.result_generation
        if not messagebox.askyesno('Copiar resultado?', 'O clipboard será substituído e poderá reter o texto no histórico.',parent=self.window): return
        if not self.window.winfo_exists() or not self.hub.permissions.allowed(COPY_TEXT): return
        if self.result_generation!=generation or self.result_context!=self.context() or self.output!=reviewed or (self.ai_preview and not self.hub.permissions.allowed(TEXT_AI)):
            self.invalidate(); return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(reviewed)
        except tk.TclError: self.status.set('Falha ao copiar.'); return
        self.status.set('Copiado. Cole manualmente no destino.')
    def cancel_pending(self):
        if self.pending is not None:
            self.window.after_cancel(self.pending); self.pending=None
    def destroyed(self,event):
        if event.widget is self.window:
            self.cancel_pending(); self.ai_generation+=1; self.dictionary.clear()
            if self.ai_timer is not None: self.window.after_cancel(self.ai_timer); self.ai_timer=None
    def mode_changed(self,*_):
        self.invalidate(); self.schedule()
    def schedule(self):
        self.cancel_pending()
        if self.mode.get()!='Desligado': self.pending=self.window.after(450,self.live_review)
    def live_review(self):
        self.pending=None
        if self.mode.get()=='Automático':
            try:
                result=review(self.original(),self.language.get(),automatic=True,ignored=self.dictionary[self.language.get()])
                if result.edits: self.replace_original(result)
            except ValueError as e: self.status.set(str(e)); return
        self.review_now()
    def review_now(self):
        self.invalidate_ai(); self.cancel_pending(); original=self.original()
        try: result=review(original,self.language.get(),ignored=self.dictionary[self.language.get()])
        except ValueError as e: self.invalidate(); self.status.set(str(e)); return
        self.show_review(original,result)
        self.details.set(f'{len(result.edits)} sugestão(ões). '+ ' · '.join(f'{e.before} → {e.after} ({e.kind})' for e in result.edits[:3]))
        self.status.set('Prévia de regras locais; não valida todo o texto.')
    def replace_original(self,result):
        original=self.original(); offset=len(self.input.get('1.0','insert')); offset=cursor_after(offset,result.edits)
        self.snapshot=(original,result.text); self.changing=True
        try:
            self.input.edit_separator(); self.input.delete('1.0','end'); self.input.insert('1.0',result.text); self.input.edit_separator()
            self.input.mark_set('insert',f'1.0 + {offset} chars'); self.input.edit_modified(False)
        finally: self.changing=False
        self.invalidate(); self.undo_button.configure(state='normal')
    def accept(self):
        if self.reviewed is None or self.original()!=self.reviewed[0] or self.result_context!=self.context(): self.invalidate(); return
        if self.ai_preview and not self.hub.permissions.allowed(TEXT_AI): self.invalidate(); return
        result=self.reviewed[1]
        if self.ai_preview: self.mode.set('Desligado') if self.mode.get()!='Desligado' else None
        # mode changes invalidate previews, so capture the approved result first.
        self.replace_original(result); self.review_now()
    def undo_review(self):
        if self.snapshot is None: return
        before,after=self.snapshot
        if self.original()!=after:
            self.status.set('O texto mudou. Use Ctrl+Z para desfazer edições anteriores.'); return
        self.mode.set('Desligado'); self.cancel_pending(); self.changing=True
        try:
            self.input.delete('1.0','end'); self.input.insert('1.0',before); self.input.edit_modified(False)
        finally: self.changing=False
        self.snapshot=None; self.undo_button.configure(state='disabled'); self.invalidate(); self.status.set('Revisão desfeita; modo automático desligado.')
    def clear(self):
        self.cancel_pending(); self.snapshot=None; self.undo_button.configure(state='disabled')
        self.input.delete('1.0','end'); self.input.edit_reset(); self.invalidate(); self.status.set('Textos da sessão removidos.')

    def invalidate_ai(self):
        self.ai_generation+=1; self.ai_preview=False
    def edit_dictionary(self):
        lang=self.language.get()
        raw=simpledialog.askstring('Dicionário da sessão','Palavras a ignorar nas regras locais, separadas por vírgula (até 100). Não será salvo em disco.',initialvalue=', '.join(sorted(self.dictionary[lang])),parent=self.window)
        if raw is None: return
        try: self.dictionary[lang]=dictionary_words(raw)
        except ValueError as exc: self.status.set(str(exc)); return
        self.invalidate(); self.schedule(); self.status.set(f'{len(self.dictionary[lang])} palavras ignoradas neste idioma.')
    def show_review(self,original,result):
        self.reviewed=(original,result); self.set_result(result.text)
        shift=0
        for edit in result.edits:
            self.input.tag_add('revision',f'1.0 + {edit.start} chars',f'1.0 + {edit.end} chars')
            start=edit.start+shift
            self.result.tag_add('revision',f'1.0 + {start} chars',f'1.0 + {start+len(edit.after)} chars')
            shift+=len(edit.after)-(edit.end-edit.start)
        self.accept_button.configure(state='normal' if result.edits else 'disabled')
    def ask_ai(self):
        if self.ai_busy or not self.hub.permissions.allowed(TEXT_AI): return
        original=self.original(); lang=self.language.get(); generation=self.ai_generation
        try: validate_source(original,lang)
        except ValueError as exc: self.status.set(str(exc)); return
        model=simpledialog.askstring('Ollama local','Nome do modelo local instalado. Desative cloud no Ollama (OLLAMA_NO_CLOUD=1).',parent=self.window)
        if not model: return
        if not messagebox.askyesno('Enviar texto ao Ollama local?','Somente este texto será enviado ao servidor local. Não use informações sensíveis. A IA pode mudar o sentido; confira a prévia.',parent=self.window): return
        if generation!=self.ai_generation or original!=self.original() or lang!=self.language.get() or not self.hub.permissions.allowed(TEXT_AI): return
        self.start_ai(original,lang,model.strip())
    def start_ai(self,original,lang,model):
        self.hub.permissions.require(TEXT_AI)
        if self.ai_busy: return
        validate_source(original,lang)
        generation=self.ai_generation+1; results=self.ai_results
        def worker():
            try: return (generation,original,lang,contextual_review(original,lang,model))
            except Exception: return (generation,original,lang,None)
        try: started=worker_for(self.hub).start(worker, results.put)
        except RuntimeError:
            self.status.set('Não foi possível iniciar a revisão. Tente novamente.'); return
        if not started:
            self.status.set('Outra operação local ainda está em execução. Aguarde sua conclusão.'); return
        self.invalidate(); self.ai_busy=True
        self.permissions_changed(); self.status.set('Revisando com modelo local...')
        self.ai_timer=self.window.after(100,self.poll_ai)
    def dirty(self):
        return bool(self.original() or self.output or self.ai_busy)
    def poll_ai(self):
        self.ai_timer=None
        try: generation,original,lang,result=self.ai_results.get_nowait()
        except queue.Empty:
            self.ai_timer=self.window.after(100,self.poll_ai); return
        self.ai_busy=False; self.permissions_changed()
        if generation!=self.ai_generation or original!=self.original() or lang!=self.language.get() or not self.hub.permissions.allowed(TEXT_AI): return
        if result is None: self.status.set('Revisão indisponível. Confira o modelo local e o formato da resposta.'); return
        self.ai_preview=True; self.show_review(original,result)
        self.details.set(f'{len(result.edits)} diferenças sugeridas pela IA; revise significado e dados.')
        self.status.set('Prévia da IA local. Nenhuma alteração aplicada.')
