"""Paletas locais e estilos compartilhados. Sem integração com o tema do sistema."""
import tkinter as tk
from tkinter import ttk

PALETTES = {
    'Claro': dict(air='#F0F5F2', soft='#E0ECE5', natural='#8FC7A3', forest='#30694F', deep='#203D30', muted='#B8CEC1', field='#FFFFFF', selected='#DCEFE3', select_text='#285640'),
    'Escuro': dict(air='#172820', soft='#243D30', natural='#8FC7A3', forest='#A5D7B4', deep='#E3F1E7', muted='#456453', field='#101E17', selected='#345641', select_text='#F0FAF3'),
}


def configure(root, name):
    p = PALETTES[name]
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=p['air'], foreground=p['deep'], fieldbackground=p['field'], bordercolor=p['muted'], troughcolor=p['soft'], lightcolor=p['muted'], darkcolor=p['muted'], font=('Segoe UI', 10))
    style.configure('TButton', background=p['soft'], padding=(10,6), borderwidth=1, relief='flat')
    style.map('TButton', background=[('active', p['selected'])], foreground=[('disabled', p['muted'])])
    style.configure('TCheckbutton', background=p['air'])
    style.map('TCheckbutton', background=[('active', p['air'])], foreground=[('disabled', p['muted'])])
    style.configure('TCombobox', selectbackground=p['selected'], selectforeground=p['select_text'])
    style.map('TCombobox', fieldbackground=[('readonly', p['field'])], foreground=[('readonly', p['deep'])])
    style.configure('TEntry', padding=(7,5))
    style.configure('TCombobox', padding=(7,5))
    style.configure('TNotebook', borderwidth=0)
    style.configure('TNotebook.Tab', padding=(12,7))
    style.map('TNotebook.Tab', background=[('selected',p['field']),('active',p['selected'])])
    style.configure('TLabelframe', padding=8, borderwidth=1, relief='solid')
    style.configure('TLabelframe.Label', font=('Segoe UI',10,'bold'), foreground=p['deep'])
    style.configure('Treeview', rowheight=26, background=p['field'], fieldbackground=p['field'], foreground=p['deep'])
    style.configure('Treeview.Heading', font=('Segoe UI',10,'bold'), padding=(6,5))
    style.map('Treeview', background=[('selected',p['selected'])], foreground=[('selected',p['select_text'])])
    style.configure('Aeris.TCombobox', padding=5)
    root.option_add('*TCombobox*Listbox.background', p['field'])
    root.option_add('*TCombobox*Listbox.foreground', p['deep'])
    root.option_add('*TCombobox*Listbox.selectBackground', p['selected'])
    root.option_add('*TCombobox*Listbox.selectForeground', p['select_text'])
    return p


def apply_tree(widget, name):
    """Recolore widgets Tk comuns. Canvas de prévia e ícone têm desenho próprio."""
    p = PALETTES[name]
    if isinstance(widget, ttk.Widget):
        pass  # Estilos ttk são gerenciados globalmente.
    elif isinstance(widget, (tk.Tk, tk.Toplevel)):
        widget.configure(bg=p['air'])
    elif isinstance(widget, tk.Text) and getattr(widget, '_aeris_reader_palette', False):
        pass  # Paleta explícita do leitor, independente do tema do Hub.
    elif isinstance(widget, (tk.Text, tk.Listbox, tk.Entry)):
        opts = dict(bg=p['field'], fg=p['deep'], selectbackground=p['selected'], selectforeground=p['select_text'], highlightbackground=p['muted'], highlightcolor=p['forest'])
        if isinstance(widget, (tk.Entry, tk.Text)):
            opts['insertbackground'] = p['deep']
        widget.configure(**opts)
    elif isinstance(widget, tk.Scale):
        widget.configure(bg=p['air'], fg=p['deep'], troughcolor=p['soft'], activebackground=p['natural'], highlightbackground=p['air'])
    elif isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
        # Preserva as funções cromáticas existentes do Hub ao alternar temas.
        if not hasattr(widget, '_aeris_bg_role'):
            old = widget.cget('bg').lower()
            widget._aeris_bg_role = next((k for k in ('air','soft','muted','field') if old == PALETTES['Claro'][k].lower()), 'air')
        if not isinstance(widget, tk.Canvas) or getattr(widget,'_aeris_logo',False) or getattr(widget,'_aeris_scroll',False):
            widget.configure(bg=p[widget._aeris_bg_role])
        if isinstance(widget, tk.Label): widget.configure(fg=p['deep'])
        if getattr(widget,'_aeris_logo',False):
            widget.itemconfigure('all', fill=p['forest'])
    for child in widget.winfo_children():
        apply_tree(child, name)
