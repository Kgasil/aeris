"""Opt-in speech interface. Worker communicates with Windows on explicit actions."""
import os
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from aeris.permissions import PLAY_VOICE
from aeris.voice import speech_payload, parse_voices, start_process, serialize

class VoiceWindow:
    capability = PLAY_VOICE
    tool_name = "Voice"
    description = "Leitura em voz alta pelo Windows. Use textos fictícios. Nenhum microfone."
    def __init__(self,hub):
        self.hub=hub; self.process=None; self.timer=None; self.job=0
        self.results=queue.Queue(); self.voices=()
        self.window=tk.Toplevel(hub.root); self.window.title('Aeris · '+self.tool_name)
        self.window.geometry('500x480'); self.window.minsize(420,420)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroyed,add='+')
        f=ttk.Frame(self.window,padding=12); f.pack(fill='both',expand=True); self.frame=f
        ttk.Label(f,text=self.tool_name,font=('Segoe UI',18)).pack(anchor='w')
        ttk.Label(f,text=self.description,wraplength=390).pack(anchor='w')
        self.text=tk.Text(f,height=6,wrap='word',undo=True); self.text.pack(fill='both',expand=True,pady=6)
        self.count=tk.StringVar(self.window,'0 caracteres')
        ttk.Label(f,textvariable=self.count).pack(anchor='w')
        self.text.bind('<<Modified>>',self.update_count); self.text.edit_modified(False)
        self.voice=tk.StringVar(self.window,'Voz padrão do Windows')
        self.choice=ttk.Combobox(f,textvariable=self.voice,values=('Voz padrão do Windows',),state='readonly'); self.choice.pack(fill='x')
        self.list_button=ttk.Button(f,text='Listar vozes instaladas',command=self.list_voices); self.list_button.pack(fill='x',pady=3)
        self.rate=tk.IntVar(self.window,0); self.volume=tk.IntVar(self.window,80)
        for label,var,lo,hi in [('Velocidade',self.rate,-5,5),('Volume (%)',self.volume,0,100)]:
            row=ttk.Frame(f); row.pack(fill='x'); ttk.Label(row,text=label,width=15).pack(side='left')
            tk.Scale(row,from_=lo,to=hi,orient='horizontal',variable=var,resolution=1,highlightthickness=0).pack(side='left',fill='x',expand=True)
        row=ttk.Frame(f); row.pack(fill='x',pady=5)
        self.play_button=ttk.Button(row,text='Ler em voz alta',command=self.play); self.play_button.pack(side='left',fill='x',expand=True)
        self.stop_button=ttk.Button(row,text='Parar',command=self.stop); self.stop_button.pack(side='left',padx=4)
        ttk.Button(row,text='Limpar',command=self.clear).pack(side='left')
        self.status=tk.StringVar(self.window,f'Autorize {self.tool_name} → Áudio em Permissões.' if os.name=='nt' else 'Reprodução nativa disponível somente no Windows.')
        ttk.Label(f,textvariable=self.status,wraplength=390).pack(anchor='w')
        self.permissions_changed()
    def update_count(self,_=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.count.set(f"{len(self.text.get('1.0','end-1c'))} caracteres")

    def permissions_changed(self):
        allowed=self.hub.permissions.allowed(self.capability)
        if not allowed and self.process is not None: self.stop(); self.status.set('Permissão revogada.')
        self.play_button.configure(state='normal' if allowed and self.process is None else 'disabled')
        self.list_button.configure(state='normal' if allowed and self.process is None else 'disabled')
        self.stop_button.configure(state='normal' if self.process is not None else 'disabled')
    def play(self):
        if not self.hub.permissions.allowed(self.capability) or self.process is not None: return
        try:
            payload=speech_payload(self.text.get('1.0','end-1c'),self.voice.get() if self.voice.get() in self.voices else '',self.rate.get(),self.volume.get())
        except (ValueError,tk.TclError) as e: self.status.set(str(e)); return
        self.start(payload)
    def list_voices(self):
        if self.hub.permissions.allowed(self.capability) and self.process is None: self.start({'action':'list'})
    def start(self,payload):
        if not self.hub.permissions.allowed(self.capability) or self.process is not None: return
        try: process=start_process()
        except OSError: self.status.set('Motor nativo indisponível. Requer Windows PowerShell e System.Speech.'); return
        self.process=process; self.job+=1; job=self.job; action=payload['action']
        def run():
            try:
                out,_=process.communicate(serialize(payload),timeout=20 if action=='list' else 600)
                if process.returncode: raise RuntimeError('Falha')
                result=parse_voices(out) if action=='list' else ()
                self.results.put((job,action,True,result))
            except Exception:
                try:
                    if process.poll() is None: process.kill()
                    process.communicate()
                except OSError: pass
                self.results.put((job,action,False,()))
        threading.Thread(target=run,daemon=True).start()
        self.status.set('Consultando vozes…' if action=='list' else 'Leitura solicitada ao Windows…')
        self.permissions_changed(); self.timer=self.window.after(80,self.poll)
    def poll(self):
        self.timer=None
        while True:
            try: job,action,ok,data=self.results.get_nowait()
            except queue.Empty: break
            if job!=self.job: continue
            self.process=None
            if ok and action=='list':
                self.set_voices(data)
            else: self.status.set('Leitura concluída.' if ok else 'Falha no motor de voz ou tempo limite excedido.')
            self.permissions_changed(); return
        if self.process is not None: self.timer=self.window.after(80,self.poll)
    def set_voices(self,data):
        selected=self.voice.get()
        self.voices=data; self.choice.configure(values=('Voz padrão do Windows',*data))
        self.voice.set(selected if selected in data else 'Voz padrão do Windows')
        self.status.set(f'{len(data)} vozes instaladas encontradas.')
    def cancel(self):
        self.job+=1
        if self.timer is not None:
            try: self.window.after_cancel(self.timer)
            except tk.TclError: pass
            self.timer=None
        if self.process is not None:
            try:
                if self.process.poll() is None: self.process.kill()
            except OSError: pass
            self.process=None
    def stop(self):
        self.cancel(); self.status.set('Parada solicitada.'); self.permissions_changed()
    def clear(self):
        self.stop(); self.text.delete('1.0','end'); self.text.edit_reset(); self.text.edit_modified(False)
        self.count.set('0 caracteres'); self.status.set('Texto removido da sessão.')
    def close(self): self.cancel(); self.window.destroy()
    def destroyed(self,event):
        if event.widget is self.window: self.cancel()
