"""Conversation UI; no automatic access to other modules or disk."""
import json
import queue
import subprocess
from aeris.local_worker import worker_for
from aeris.safe_input import strict_json
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk
from aeris.companion import chat, suggest_command, validate_message, speech_process, MAX_HISTORY
from aeris.permissions import COMPANION_CHAT, COMPANION_MIC, COMPANION_SPEAK, COPILOT_RUN

class CompanionWindow:
    def __init__(self, copilot):
        self.copilot=copilot; self.hub=copilot.hub; self.history=[]; self.results=queue.Queue(); self.job=0; self.busy=False; self.process=None; self.timer=None; self.closed=False; self.chat_allowed=False; self.kind=None; self.candidate=None
        self.window=tk.Toplevel(copilot.window); w=self.window; w.title('Aeris AI Companion'); w.geometry('780x720'); w.minsize(600,590)
        w.protocol('WM_DELETE_WINDOW',w.destroy); w.bind('<Escape>',lambda _:w.destroy()); w.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(w,padding=12); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Aeris AI Companion',font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text='IA opcional local via Ollama. Instale um modelo local e desative cloud no Ollama (OLLAMA_NO_CLOUD=1). Não informe dados sensíveis. Sem cobrança pelo Aeris.',wraplength=485).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=5); ttk.Label(row,text='Modelo instalado:').pack(side='left'); self.model=tk.StringVar(w,''); self.model_entry=ttk.Entry(row,textvariable=self.model); self.model_entry.pack(side='left',fill='x',expand=True)
        trace_window(self.window, self.model, self.model_changed)
        self.transcript=tk.Text(f,wrap='word',height=12,state='disabled'); self.transcript.pack(fill='both',expand=True)
        self.input=tk.Text(f,wrap='word',height=4); self.input.pack(fill='x',pady=5)
        self.count=tk.StringVar(w,'0 / 4000 caracteres')
        ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.input.bind('<<Modified>>',self.input_changed); self.input.edit_modified(False)
        self.input.bind('<Control-Return>',self.keyboard_send)
        row=ttk.Frame(f); row.pack(fill='x')
        self.send_button=ttk.Button(row,text='Conversar',command=self.send); self.send_button.pack(side='left')
        self.mic_button=ttk.Button(row,text='Ditar (pt-BR)',command=lambda:self.speech('listen')); self.mic_button.pack(side='left',padx=4)
        self.speak_button=ttk.Button(row,text='Ouvir resposta',command=lambda:self.speech('speak')); self.speak_button.pack(side='left')
        self.auto_speak=tk.BooleanVar(w,False); self.auto_button=ttk.Checkbutton(f,text='Ler novas respostas automaticamente (nesta janela)',variable=self.auto_speak); self.auto_button.pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=5)
        self.prepare_button=ttk.Button(row,text='Preparar ação no Copilot',command=self.prepare_action); self.prepare_button.pack(side='left')
        self.suggest_button=ttk.Button(row,text='Sugerir comando por IA',command=self.suggest); self.suggest_button.pack(side='left',padx=4)
        ttk.Button(row,text='Permissões',command=self.hub.open_permissions).pack(side='left',padx=4)
        row=ttk.Frame(f); row.pack(fill='x',pady=3)
        self.candidate_label=tk.StringVar(w,''); ttk.Label(f,textvariable=self.candidate_label,wraplength=550,justify='left').pack(anchor='w')
        self.accept_button=ttk.Button(row,text='Usar sugestão no editor',command=self.accept_candidate); self.accept_button.pack(side='left')
        self.stop_button=ttk.Button(row,text='Parar solicitação / voz',command=self.stop); self.stop_button.pack(side='left',padx=4)
        ttk.Button(row,text='Limpar conversa',command=self.clear).pack(side='left')
        self.status=tk.StringVar(w,'Autorize as funções nas permissões.'); ttk.Label(f,textvariable=self.status,wraplength=490).pack(anchor='w')
        self.permissions_changed()
    def input_changed(self,_=None):
        if not self.input.edit_modified(): return
        self.input.edit_modified(False)
        text=self.input.get('1.0','end-1c')
        self.count.set(f'{len(text)} / 4000 caracteres')
        if self.candidate and self.candidate[0]!=text:
            self.discard_candidate(); self.refresh()
    def keyboard_send(self,_=None):
        self.send()
        return 'break'
    def model_changed(self,*_):
        # Changing model invalidates history and any pending operation, not the unsent draft.
        self.stop(); self.history.clear(); self.draw()
        self.status.set('Modelo alterado. Histórico limpo; texto não enviado preservado.')
        self.refresh()
    def refresh(self):
        for button,cap in ((self.send_button,COMPANION_CHAT),(self.mic_button,COMPANION_MIC),(self.speak_button,COMPANION_SPEAK)):
            button.configure(state='normal' if not self.busy and self.hub.permissions.allowed(cap) and (cap!=COMPANION_SPEAK or bool(self.history)) else 'disabled')
        both=self.hub.permissions.allowed(COMPANION_CHAT) and self.hub.permissions.allowed(COPILOT_RUN)
        voice=self.hub.permissions.allowed(COMPANION_CHAT) and self.hub.permissions.allowed(COMPANION_SPEAK)
        if not voice: self.auto_speak.set(False)
        self.auto_button.configure(state='normal' if voice else 'disabled')
        self.suggest_button.configure(state='normal' if both and not self.busy else 'disabled')
        self.accept_button.configure(state='normal' if both and not self.busy and self.candidate else 'disabled')
        self.prepare_button.configure(state='normal' if not self.busy and self.hub.permissions.allowed(COPILOT_RUN) else 'disabled')
        self.stop_button.configure(state='normal' if self.busy else 'disabled')
    def discard_candidate(self):
        self.candidate=None; self.candidate_label.set('')
    def permissions_changed(self):
        if not self.hub.permissions.allowed(COPILOT_RUN):
            self.discard_candidate()
            if self.busy and self.kind=='suggest': self.stop()
        if self.busy and not self.hub.permissions.allowed(self.cap): self.stop()
        allowed=self.hub.permissions.allowed(COMPANION_CHAT)
        if self.chat_allowed and not allowed: self.clear()
        self.chat_allowed=allowed; self.refresh()
    def draw(self):
        self.transcript.configure(state='normal'); self.transcript.delete('1.0','end')
        for role,text in self.history: self.transcript.insert('end',('Você' if role=='user' else 'Aeris (IA)')+': '+text+'\n\n')
        self.transcript.configure(state='disabled'); self.transcript.see('end')
    def stop(self):
        self.job+=1; self.discard_candidate()
        if self.process is not None:
            try: self.process.kill()
            except OSError: pass
        self.status.set('Interrompido. A solicitação local pode demorar a terminar; resultado descartado.' if self.busy else 'Interrompido.'); self.refresh()
    def clear(self):
        self.stop(); self.history.clear(); self.draw(); self.input.delete('1.0','end'); self.status.set('Conversa limpa. Solicitação local em andamento pode demorar a terminar.' if self.busy else 'Conversa limpa.'); self.refresh()
    def start(self,cap,fn,kind=None):
        self.hub.permissions.require(cap)
        if self.busy or self.closed: return False
        job=self.job+1; results=self.results
        def worker():
            try: return (job,True,fn())
            except Exception: return (job,False,None)
        try:
            started=worker_for(self.hub).start(worker, results.put)
        except RuntimeError:
            self.status.set('Não foi possível iniciar a solicitação. Tente novamente.'); return False
        if not started:
            self.status.set('Outra operação local ainda está em execução. Aguarde sua conclusão.'); return False
        self.busy=True; self.cap=cap; self.kind=kind; self.job=job
        self.refresh(); self.schedule_poll(); return True
    def dirty(self):
        return bool(self.busy or self.history or self.input.get('1.0','end-1c'))
    def send(self):
        if self.busy: return
        try:
            text=validate_message(self.input.get('1.0','end-1c')); model=self.model.get().strip(); history=tuple(self.history); self.discard_candidate()
            if not self.start(COMPANION_CHAT,lambda:(text,chat(model,history,text))): return
        except (ValueError,PermissionError) as exc: self.status.set(str(exc)); return
        self.input.delete('1.0','end'); self.status.set('Consultando modelo local...')
    def suggest(self):
        if self.busy: return
        try:
            self.hub.permissions.require(COPILOT_RUN)
            self.hub.permissions.require(COMPANION_CHAT)
            original=self.input.get('1.0','end-1c'); text=validate_message(original)
            if len(text)>500: raise ValueError('Solicitação de ação: até 500 caracteres.')
            model=self.model.get().strip(); self.discard_candidate()
            if not self.start(COMPANION_CHAT,lambda:(original,suggest_command(model,text)),kind='suggest'): return
        except (ValueError,PermissionError) as exc: self.status.set(str(exc)); return
        self.status.set('Interpretando solicitação no modelo local. Nenhuma ação executada.')
    def accept_candidate(self):
        if self.busy or not self.candidate: return
        original,candidate=self.candidate; self.discard_candidate()
        if not (self.hub.permissions.allowed(COMPANION_CHAT) and self.hub.permissions.allowed(COPILOT_RUN)) or self.input.get('1.0','end-1c')!=original:
            self.status.set('Sugestão expirada. Prepare outra.'); self.refresh(); return
        self.input.delete('1.0','end'); self.input.insert('1.0',candidate)
        self.status.set('Revise o comando sugerido e pressione Preparar ação no Copilot.'); self.refresh()
    def speech(self,action):
        if self.busy: return
        if action=='listen' and self.input.get('1.0','end-1c').strip():
            self.status.set('Limpe ou envie o texto atual antes de ditar.'); return
        cap=COMPANION_MIC if action=='listen' else COMPANION_SPEAK
        try:
            self.hub.permissions.require(cap)
            text=self.history[-1][1] if action=='speak' else ''
            if action=='listen': self.discard_candidate()
            if worker_for(self.hub).busy:
                self.status.set('Outra operação local ainda está em execução. Aguarde sua conclusão.'); return
            p=speech_process(); self.process=p
            def run():
                try:
                    out,_=p.communicate(json.dumps({'action':action,'text':text},ensure_ascii=True),timeout=18 if action=='listen' else 90)
                    if p.returncode: raise OSError('Falha de voz.')
                    return validate_message(strict_json(out, 32768)) if action=='listen' else None
                except subprocess.TimeoutExpired: p.kill(); p.communicate(); raise
            if not self.start(cap,run):
                try: p.kill()
                except OSError: pass
                try: p.communicate(timeout=2)
                except (OSError,subprocess.TimeoutExpired): pass
                self.process=None; return
        except (OSError,PermissionError,IndexError): self.status.set('Voz indisponível. Verifique Windows, permissão e voz/reconhecedor pt-BR.'); return
        self.status.set('Microfone ativo — fale agora (até 18 s).' if action=='listen' else 'Reproduzindo resposta em voz masculina local...')
    def prepare_action(self):
        if self.busy: return
        try: text=validate_message(self.input.get('1.0','end-1c'))
        except ValueError as exc: self.status.set(str(exc)); return
        self.discard_candidate(); self.refresh(); self.copilot.command.set(text); self.copilot.prepare(); self.copilot.window.lift(); self.status.set('Confira a prévia no Copilot. Nenhuma ação foi executada.' if self.copilot.session.pending else 'Comando não preparado; confira o motivo no Copilot.')
    def schedule_poll(self):
        # Poll only while a request is outstanding, including cancelled jobs
        # whose worker has not returned yet. Tk is touched only by the UI thread.
        if not self.closed and self.busy and self.timer is None:
            self.timer=self.window.after(100,self.poll)
    def poll(self):
        self.timer=None
        if self.closed: return
        try: job,ok,result=self.results.get_nowait()
        except queue.Empty: pass
        else:
            self.busy=False; self.process=None
            auto=False
            if job==self.job and self.hub.permissions.allowed(self.cap):
                if not ok: self.status.set('Não concluído. Verifique servidor/modelo local ou recursos de voz pt-BR.')
                elif self.kind=='suggest':
                    original,candidate=result
                    if self.hub.permissions.allowed(COPILOT_RUN) and self.input.get('1.0','end-1c')==original:
                        self.candidate=(original,candidate); self.candidate_label.set('Sugestão da IA (confira os dados): '+candidate); self.status.set('Sugestão pronta. Use no editor somente se refletir seu pedido.')
                    else: self.status.set('Sugestão descartada: texto ou permissão mudou.')
                elif self.cap==COMPANION_CHAT:
                    text,response=result; self.history.extend((('user',text),('assistant',response))); self.history=self.history[-MAX_HISTORY:]; self.draw(); self.status.set('Resposta recebida. A IA pode errar.'); auto=self.auto_speak.get() and self.hub.permissions.allowed(COMPANION_SPEAK)
                elif self.cap==COMPANION_MIC:
                    if self.input.get('1.0','end-1c').strip(): self.status.set('Ditado descartado para preservar o texto digitado durante a captura.')
                    else: self.input.insert('1.0',result); self.status.set('Revise a transcrição antes de conversar ou preparar ação.')
                else: self.status.set('Reprodução concluída.')
            self.refresh()
            if auto: self.speech('speak')
        self.schedule_poll()
    def destroyed(self,event):
        if event.widget is self.window:
            self.closed=True; self.job+=1; self.history.clear()
            if self.timer is not None:
                self.window.after_cancel(self.timer); self.timer=None
            if self.process is not None:
                try: self.process.kill()
                except OSError: pass
