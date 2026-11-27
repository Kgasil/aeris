"""Aeris-owned consent dialogs. The caller grants only after revision checks."""
import tkinter as tk
from tkinter import ttk
from aeris.permissions import CAPABILITIES
from aeris.theme import wind_mark, apply_tree


def _dialog(parent,theme,title,description,detail,approve):
    """Explicit affirmative button; dismissing, Escape or closing means no."""
    selected=False
    previous=parent.grab_current()
    window=tk.Toplevel(parent); window.withdraw()
    window.title('Aeris · '+title); window.transient(parent)
    window.resizable(True,True)
    frame=ttk.Frame(window,padding=18); frame.pack(fill='both',expand=True)
    buttons=ttk.Frame(frame); buttons.pack(side='bottom',fill='x',pady=(14,0))
    def accept():
        nonlocal selected
        selected=True; window.destroy()
    deny=ttk.Button(buttons,text='Agora não',command=window.destroy); deny.pack(side='left')
    ttk.Button(buttons,text=approve,command=accept,style='Aeris.Primary.TButton').pack(side='right')
    head=ttk.Frame(frame); head.pack(fill='x',pady=(0,8))
    wind_mark(head,theme,size=40,surface='air').pack(side='left',padx=(0,10))
    ttk.Label(head,text=title,style='Experience.Subtitle.TLabel',wraplength=365,justify='left').pack(side='left',fill='x',expand=True)
    ttk.Label(frame,text=description,wraplength=440,justify='left').pack(fill='x',pady=(2,10))
    card=ttk.Frame(frame,padding=12,style='Experience.Card.TFrame'); card.pack(fill='x')
    ttk.Label(card,text=detail,style='Experience.Card.TLabel',wraplength=416,justify='left').pack(fill='x')
    window.protocol('WM_DELETE_WINDOW',window.destroy); window.bind('<Escape>',lambda _:window.destroy())
    apply_tree(window,theme)
    window.update_idletasks()
    w=max(490,window.winfo_reqwidth()); h=window.winfo_reqheight()
    window.geometry(f'{w}x{h}+{max(0,parent.winfo_rootx()+(parent.winfo_width()-w)//2)}+{max(0,parent.winfo_rooty()+(parent.winfo_height()-h)//2)}')
    window.minsize(w,h); window.deiconify()
    try:
        window.wait_visibility(); window.grab_set(); deny.focus_set(); window.wait_window()
    except tk.TclError:
        selected=False
        try: window.destroy()
        except tk.TclError: pass
    finally:
        if previous is not None:
            try:
                if previous.winfo_exists(): previous.grab_set()
            except tk.TclError: pass
    return selected


def ask_permission(parent,theme,cap,purpose=None):
    if cap not in CAPABILITIES: return False
    label,scope=CAPABILITIES[cap]
    return _dialog(parent,theme,'Permitir acesso? '+label, purpose or scope,
                   'Escopo: '+scope+'\n\nVálido somente nesta sessão. Revogue em Permissões. Autorizar não inicia uma captura por si só.',
                   'Autorizar nesta sessão')


def ask_confirmation(parent,theme,title,description):
    return _dialog(parent,theme,title,description,
                   'Confirme somente se concordar com esta ação específica. As permissões necessárias continuam sendo verificadas.',
                   'Confirmar')
