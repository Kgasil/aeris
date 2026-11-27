"""Paletas locais e estilos compartilhados. Sem integração com o tema do sistema."""
import tkinter as tk
from tkinter import ttk

PALETTES = {
    'Claro': dict(air='#F5F7F6', soft='#E8EEEA', natural='#8FC7A3', forest='#30694F', deep='#203D30', muted='#BCCBC2', secondary='#476553', focus='#30694F', field='#FFFFFF', selected='#DCEFE3', select_text='#285640', primary='#285640', primary_hover='#397557', primary_text='#FFFFFF', sidebar='#193D30', sidebar_text='#E3F1E7', sidebar_muted='#A5D7B4', sidebar_hover='#37614E', nav_selected='#DCEFE3', nav_text='#193D30', success='#286446', info='#245D8C', warning='#805500', danger='#A52E36'),
    'Escuro': dict(air='#101A15', soft='#23382C', natural='#8FC7A3', forest='#A5D7B4', deep='#E3F1E7', muted='#456453', secondary='#B4CCBD', focus='#A5D7B4', field='#192D23', selected='#345641', select_text='#F0FAF3', primary='#8FC7A3', primary_hover='#A5D7B4', primary_text='#193D30', sidebar='#192D23', sidebar_text='#E3F1E7', sidebar_muted='#A5D7B4', sidebar_hover='#294D3A', nav_selected='#345641', nav_text='#F0FAF3', success='#A5D7B4', info='#9EC9F4', warning='#F2C56E', danger='#FFB4B7'),
}

SPACE = (4, 8, 12, 16, 24, 32)
FONT = 'Segoe UI'
TYPE = {'body': (FONT,10), 'section': (FONT,10,'bold'), 'subtitle': (FONT,13,'bold'), 'title': (FONT,21,'bold'), 'detail': (FONT,17,'bold'), 'brand': (FONT,30,'bold')}

# Exact cubic geometry of the website asset assets/aeris-symbol.svg (viewBox 0 0 100 100).
WIND_CURVES = ((15,38,40,9,55,59,81,25), (12,56,42,27,62,81,88,45), (24,74,49,52,62,90,79,70))


def wind_points(curve, size):
    """Sample the SVG cubic, rather than fitting a different Tk spline."""
    result=[]
    for i in range(65):
        t=i/64; u=1-t
        for axis in (0,1):
            result.append((u**3*curve[axis]+3*u*u*t*curve[axis+2]+3*u*t*t*curve[axis+4]+t**3*curve[axis+6])*size/100)
    return result


def wind_mark(parent, name, *, size=64, surface='field', ink='forest'):
    """Render the existing website symbol with theme-aware native strokes."""
    p=PALETTES[name]
    mark=tk.Canvas(parent,width=size,height=size,bg=p[surface],highlightthickness=0,borderwidth=0)
    mark._aeris_wind_roles=(surface,ink)
    for curve in WIND_CURVES:
        mark.create_line(*wind_points(curve,size),width=max(2,size*.05),fill=p[ink],capstyle=tk.ROUND,joinstyle=tk.ROUND)
    return mark


# Legacy Hub widgets are created before the shared theme is applied.
LEGACY_BACKGROUNDS={'#f6faf7':'air','#dcefe3':'soft','#cfdfd5':'muted','#ffffff':'field','#f0f5f2':'air','#e0ece5':'soft','#b8cec1':'muted'}

def background_role(value):
    color=value.lower()
    for role in ('air','soft','muted','field'):
        if color==PALETTES['Claro'][role].lower(): return role
    return LEGACY_BACKGROUNDS.get(color,'air')

def configure(root, name):
    p = PALETTES[name]
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=p['air'], foreground=p['deep'], fieldbackground=p['field'], bordercolor=p['muted'], troughcolor=p['soft'], lightcolor=p['muted'], darkcolor=p['muted'], font=('Segoe UI', 10))
    style.configure('TButton', background=p['soft'], padding=(12,8), borderwidth=1, relief='flat')
    style.map('TButton', background=[('disabled', p['soft']),('active', p['selected'])], foreground=[('disabled', p['secondary'])], bordercolor=[('focus',p['focus'])], focuscolor=[('focus',p['focus'])])
    style.configure('TCheckbutton', background=p['air'])
    style.map('TCheckbutton', background=[('active', p['air'])], foreground=[('disabled', p['secondary'])])
    style.configure('TCombobox', selectbackground=p['selected'], selectforeground=p['select_text'])
    style.map('TCombobox', fieldbackground=[('readonly', p['field'])], foreground=[('readonly', p['deep'])])
    for role in ('Aeris.Primary.TButton','Experience.Primary.TButton'):
        style.configure(role,background=p['primary'],foreground=p['primary_text'],padding=(16,8),borderwidth=1)
        style.map(role,background=[('disabled',p['soft']),('active',p['primary_hover']),('!disabled',p['primary'])],foreground=[('disabled',p['secondary']),('!disabled',p['primary_text'])],focuscolor=[('focus',p['primary_text'])],bordercolor=[('focus',p['focus'])])
    style.configure('TEntry', padding=(7,5))
    style.map('TEntry',bordercolor=[('focus',p['focus'])],lightcolor=[('focus',p['focus'])],darkcolor=[('focus',p['focus'])])
    style.map('TCombobox',bordercolor=[('focus',p['focus'])],lightcolor=[('focus',p['focus'])],darkcolor=[('focus',p['focus'])])
    # Keep focus visible on keyboard-operated controls, including catalogue filters.
    for control in ('TRadiobutton','TCheckbutton','Experience.Goal.TRadiobutton','Treeview'):
        style.map(control,focuscolor=[('focus',p['focus'])])
    style.configure('Aeris.Muted.TLabel',foreground=p['secondary'])
    style.configure('TCombobox', padding=(7,5))
    style.configure('TNotebook', borderwidth=0)
    style.configure('TNotebook.Tab', padding=(12,7))
    style.map('TNotebook.Tab', background=[('selected',p['field']),('active',p['selected'])],foreground=[('selected',p['deep']),('!selected',p['secondary'])],focuscolor=[('focus',p['focus'])])
    style.configure('TLabelframe', padding=8, borderwidth=1, relief='solid')
    style.configure('TLabelframe.Label', font=('Segoe UI',10,'bold'), foreground=p['deep'])
    style.configure('Treeview', rowheight=30, background=p['field'], fieldbackground=p['field'], foreground=p['deep'])
    style.configure('Treeview.Heading', font=('Segoe UI',10,'bold'), padding=(6,5))
    style.map('Treeview', background=[('selected',p['selected'])], foreground=[('selected',p['select_text'])])
    style.configure('Aeris.TCombobox', padding=5)
    root.option_add('*TCombobox*Listbox.background', p['field'])
    root.option_add('*TCombobox*Listbox.foreground', p['deep'])
    root.option_add('*TCombobox*Listbox.selectBackground', p['selected'])
    root.option_add('*TCombobox*Listbox.selectForeground', p['select_text'])
    configure_experience(style,p)
    return p


def configure_experience(style,p):
    """Workspace styles also follow the global theme."""
    style.configure('Experience.Goal.TRadiobutton',padding=(8,5),font=('Segoe UI',10))
    style.configure('Experience.Title.TLabel',font=('Segoe UI',21,'bold'))
    style.configure('TNotebook.Tab',padding=(12,8),font=('Segoe UI',10))
    style.configure('Experience.Brand.TLabel',font=('Segoe UI',30,'bold'),background=p['sidebar'],foreground=p['sidebar_text'])
    style.configure('Experience.Side.TFrame',background=p['sidebar'])
    style.configure('Experience.Side.TLabel',background=p['sidebar'],foreground=p['sidebar_text'],font=('Segoe UI',10))
    style.configure('Experience.SideSection.TLabel',background=p['sidebar'],foreground=p['sidebar_muted'],font=('Segoe UI',9,'bold'))
    style.configure('Experience.Connection.TLabel',font=('Segoe UI',10,'bold'),foreground=p['forest'])
    style.configure('Experience.Activity.TLabel',background=p['field'],foreground=p['deep'],font=('Segoe UI',10,'bold'))
    style.configure('Experience.Horizontal.TProgressbar',background=p['forest'],troughcolor=p['soft'],bordercolor=p['muted'],thickness=6)
    style.configure('Experience.Card.TFrame',background=p['field'])
    style.configure('Experience.Card.TLabel',background=p['field'],foreground=p['deep'])
    style.configure('Experience.Detail.TLabel',background=p['field'],foreground=p['deep'],font=TYPE['detail'])
    style.configure('Experience.Welcome.TLabel',background=p['field'],foreground=p['deep'],font=TYPE['title'])
    style.configure('Experience.WelcomeMuted.TLabel',background=p['field'],foreground=p['secondary'],font=TYPE['body'])
    style.configure('Experience.CompactBrand.TLabel',background=p['sidebar'],foreground=p['sidebar_text'],font=(FONT,18,'bold'))
    style.configure('Experience.Section.TLabel',font=('Segoe UI',10,'bold'),foreground=p['forest'])
    style.configure('Experience.Subtitle.TLabel',font=('Segoe UI',13,'bold'))
    style.configure('Experience.Muted.TLabel',font=('Segoe UI',10),foreground=p['secondary'])
    style.configure('Experience.Nav.TButton',padding=(12,8),anchor='w',background=p['sidebar'],foreground=p['sidebar_text'],borderwidth=0,relief='flat')
    style.map('Experience.Nav.TButton',background=[('active',p['sidebar_hover']),('!disabled',p['sidebar'])],foreground=[('!disabled',p['sidebar_text'])],focuscolor=[('focus',p['sidebar_muted'])])
    style.configure('Experience.Active.TButton',padding=(12,8),anchor='w',background=p['nav_selected'],foreground=p['nav_text'],borderwidth=0,relief='flat')
    style.map('Experience.Active.TButton',background=[('active',p['nav_selected']),('!disabled',p['nav_selected'])],foreground=[('!disabled',p['nav_text'])],focuscolor=[('focus',p['nav_text'])])
    for role in ('success','info','warning','danger'):
        style.configure('Aeris.'+role.title()+'.TLabel',foreground=p[role],background=p['air'],font=TYPE['section'])
    style.configure('Aeris.Stop.TButton',foreground=p['danger'],background=p['field'],padding=(12,8),borderwidth=1)
    style.map('Aeris.Stop.TButton',foreground=[('disabled',p['secondary']),('!disabled',p['danger'])],background=[('disabled',p['soft']),('active',p['soft']),('!disabled',p['field'])],focuscolor=[('focus',p['focus'])])


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
        opts = dict(bg=p['field'], fg=p['deep'], selectbackground=p['selected'], selectforeground=p['select_text'], highlightbackground=p['muted'], highlightcolor=p['focus'])
        if isinstance(widget, (tk.Entry, tk.Text)):
            opts['insertbackground'] = p['deep']
        widget.configure(**opts)
    elif isinstance(widget, tk.Scale):
        widget.configure(bg=p['air'], fg=p['deep'], troughcolor=p['soft'], activebackground=p['natural'], highlightbackground=p['air'])
    elif isinstance(widget, tk.Canvas) and hasattr(widget,'_aeris_wind_roles'):
        surface,ink=widget._aeris_wind_roles
        widget.configure(bg=p[surface]); widget.itemconfigure('all',fill=p[ink])
    elif isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
        # Preserva as funções cromáticas existentes do Hub ao alternar temas.
        if not hasattr(widget, '_aeris_bg_role'):
            old = widget.cget('bg').lower()
            widget._aeris_bg_role = background_role(old)
        if not isinstance(widget, tk.Canvas) or getattr(widget,'_aeris_logo',False) or getattr(widget,'_aeris_scroll',False):
            widget.configure(bg=p[widget._aeris_bg_role])
        if isinstance(widget, tk.Canvas) and getattr(widget,'_aeris_scroll',False):
            widget.configure(highlightbackground=p['muted'],highlightcolor=p['focus'])
        if isinstance(widget, tk.Label): widget.configure(fg=p['deep'])
        if getattr(widget,'_aeris_logo',False):
            widget.itemconfigure('all', fill=p['forest'])
    for child in widget.winfo_children():
        apply_tree(child, name)


# Conservative visual normalization: no callbacks, layout managers, values or permissions change.
# Explicit action labels only; ambiguous operations keep their original style.
_STOP_LABELS=frozenset(('Cancelar','Parar','Parar reprodução','Parar transcrição','Excluir','Excluir lista','Excluir tarefa','Excluir reunião','Revogar acesso','Revogar todos os acessos','Apagar registro','Limpar sessão'))


def polish_tool_window(window):
    """Use the shared action hierarchy without changing any tool semantics."""
    for widget in window.winfo_children():
        if isinstance(widget,tk.Toplevel): continue
        if isinstance(widget,ttk.Button) and widget.cget('style') in ('','TButton') and widget.cget('text') in _STOP_LABELS:
            widget.configure(style='Aeris.Stop.TButton')
        if isinstance(widget,ttk.Label) and widget.cget('style') in ('','TLabel'):
            # Existing explicit heading fonts encode intent; leave custom previews alone.
            font=str(widget.cget('font'))
            if font in ('{Segoe UI} 21 bold','{Segoe UI} 18 bold','Segoe UI 21 bold','Segoe UI 18 bold'):
                widget.configure(font=TYPE['title'])
        polish_tool_window(widget)
