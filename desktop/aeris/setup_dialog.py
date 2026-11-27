"""Explicit setup choice; no downloads or permission changes from this dialog."""
import tkinter as tk
from tkinter import ttk
from aeris.theme import wind_mark


def choose_setup(parent,theme):
    window=tk.Toplevel(parent); window.title('Aeris · Preparar IA local'); window.transient(parent)
    window.geometry('560x540'); window.minsize(480,460)
    model=tk.StringVar(window,'qwen2.5:1.5b'); consent=tk.BooleanVar(window,False); selected=[]
    frame=ttk.Frame(window,padding=18); frame.pack(fill='both',expand=True)
    mark=wind_mark(frame,theme,size=48,surface='air'); mark.pack(anchor='w')
    ttk.Label(frame,text='Prepare seu assistente',style='Experience.Title.TLabel').pack(anchor='w')
    ttk.Label(frame,text='O Ollama executa modelos de IA no computador. Após os downloads, a conversa local não precisa de um serviço de IA na nuvem.',wraplength=450,justify='left').pack(fill='x',pady=(4,12))
    for value,title,detail in (
        ('qwen2.5:1.5b','Modo leve · texto','Cerca de 1 GB de download. Reserve 3 GiB para o modelo.'),
        ('qwen2.5vl:3b','Modo multimodal · texto e imagens','Cerca de 3,2 GB de download. Reserve 6 GiB para o modelo.')):
        card=ttk.Frame(frame,padding=8,style='Experience.Card.TFrame'); card.pack(fill='x',pady=4)
        ttk.Radiobutton(card,text=title,value=value,variable=model).pack(anchor='w')
        ttk.Label(card,text=detail,style='Experience.Card.TLabel',wraplength=430).pack(anchor='w')
    ttk.Label(frame,text='Internet, WinGet e espaço adicional para o Ollama podem ser necessários. Voz e áudio de reuniões têm requisitos próprios. Termos: ollama.com e catálogo oficial do modelo.',wraplength=450,justify='left').pack(fill='x',pady=8)
    ttk.Checkbutton(frame,text='Autorizo os downloads e os termos aplicáveis do pacote e da fonte.',variable=consent).pack(anchor='w')
    ttk.Label(frame,text='Nenhum áudio, imagem ou dado pessoal será enviado no teste. Você pode cancelar a preparação; arquivos já baixados podem permanecer.',wraplength=450,justify='left').pack(fill='x',pady=4)
    buttons=ttk.Frame(frame); buttons.pack(side='bottom',fill='x',pady=(8,0))
    def accept():
        if consent.get():
            selected.append(model.get()); window.destroy()
    ttk.Button(buttons,text='Agora não',command=window.destroy).pack(side='left')
    start=ttk.Button(buttons,text='Preparar IA',command=accept,style='Experience.Primary.TButton',state='disabled'); start.pack(side='right')
    consent.trace_add('write',lambda *_:start.configure(state='normal' if consent.get() else 'disabled'))
    window.protocol('WM_DELETE_WINDOW',window.destroy); window.bind('<Escape>',lambda _:window.destroy())
    window.grab_set(); window.wait_window()
    return selected[0] if selected else None
