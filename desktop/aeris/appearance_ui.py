"""Preferências com prévia local e aplicação explícita."""
import tkinter as tk
from aeris.window_lifecycle import trace_window
from tkinter import ttk,messagebox
from aeris.settings import Appearance,CORNERS,SIZES,FAVORITES,THEMES
from aeris.theme import PALETTES

class AppearanceWindow:
    def __init__(self,hub):
        self.hub=hub; self.window=tk.Toplevel(hub.root); self.window.title('Aeris · Aparência')
        self.window.transient(hub.root); self.window.geometry('620x650'); self.window.minsize(450,420)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _:self.close())
        p=hub.settings.appearance
        self.corner=tk.StringVar(self.window,p.corner); self.panel=tk.StringVar(self.window,p.panel_size)
        self.icon=tk.IntVar(self.window,p.icon_size); self.opacity=tk.IntVar(self.window,p.opacity)
        self.enabled=tk.BooleanVar(self.window,p.quick_enabled); self.floating=tk.BooleanVar(self.window,p.floating_enabled); self.topmost=tk.BooleanVar(self.window,p.floating_topmost)
        self.theme=tk.StringVar(self.window,p.theme)
        self.favorites_only=tk.BooleanVar(self.window,p.favorites_only)
        self.favorites={name:tk.BooleanVar(self.window,name in p.favorites) for name in FAVORITES}
        shell=ttk.Frame(self.window,padding=16); shell.pack(fill='both',expand=True)
        ttk.Label(shell,text='Aparência e preferências',style='Experience.Title.TLabel').pack(anchor='w')
        ttk.Label(shell,text='Escolha o tema e personalize seus atalhos.',style='Experience.Muted.TLabel').pack(anchor='w',pady=(2,12))
        buttons=ttk.Frame(shell); buttons.pack(side='bottom',fill='x',pady=(12,0))
        ttk.Button(buttons,text='Restaurar padrões',command=self.reset).pack(side='left')
        ttk.Button(buttons,text='Salvar',command=self.save,style='Aeris.Primary.TButton').pack(side='right')
        ttk.Button(buttons,text='Cancelar',command=self.close).pack(side='right',padx=6)
        tabs=ttk.Notebook(shell); tabs.pack(fill='both',expand=True); tabs.enable_traversal()
        general=ttk.Frame(tabs); favorites=ttk.Frame(tabs)
        tabs.add(general,text='Aparência'); tabs.add(favorites,text='Favoritos')
        frame=self.scroll_content(general)
        ttk.Label(frame,text='Tema do aplicativo',style='Experience.Subtitle.TLabel').pack(anchor='w',pady=(0,4))
        themes=ttk.Frame(frame); themes.pack(fill='x',pady=(0,12))
        for name in ('Escuro','Claro'):
            ttk.Radiobutton(themes,text=name+(' (padrão)' if name=='Escuro' else ''),value=name,variable=self.theme).pack(side='left',padx=(0,12))
        ttk.Label(frame,text='Painel e atalho flutuante',style='Experience.Subtitle.TLabel').pack(anchor='w',pady=(0,4))
        for text,var in [('Painel rápido no Hub',self.enabled),('Ícone flutuante Spotlight',self.floating),('Manter sobre outras janelas (oculte antes de jogar)',self.topmost)]:
            ttk.Checkbutton(frame,text=text,variable=var).pack(anchor='w',pady=2)
        for text,var,options in [('Canto',self.corner,CORNERS),('Tamanho do painel',self.panel,tuple(SIZES))]:
            ttk.Label(frame,text=text).pack(anchor='w',pady=(5,0)); ttk.Combobox(frame,textvariable=var,values=options,state='readonly').pack(fill='x')
        scales=ttk.Frame(frame); scales.pack(fill='x',pady=4)
        for text,var,low,high in [('Ícone (px)',self.icon,24,64),('Opacidade do painel (%)',self.opacity,80,100)]:
            cell=ttk.Frame(scales); cell.pack(side='left',fill='x',expand=True,padx=2)
            ttk.Label(cell,text=text).pack(anchor='w'); tk.Scale(cell,variable=var,from_=low,to=high,orient='horizontal',highlightthickness=0).pack(fill='x')
        favorite_content=self.scroll_content(favorites)
        ttk.Label(favorite_content,text='Atalhos favoritos',style='Experience.Subtitle.TLabel').pack(anchor='w')
        ttk.Label(favorite_content,text='Marque as ferramentas que deseja destacar.',wraplength=360,style='Experience.Muted.TLabel').pack(anchor='w',pady=(4,8))
        ttk.Checkbutton(favorite_content,text='Mostrar somente favoritos ativos',variable=self.favorites_only).pack(anchor='w',pady=(0,8))
        row=ttk.Frame(favorite_content); row.pack(fill='x',pady=4)
        for i,(name,var) in enumerate(self.favorites.items()): ttk.Checkbutton(row,text=name,variable=var).grid(row=i//2,column=i%2,sticky='w',padx=4,pady=3)
        ttk.Label(frame,text='Prévia · posição e tamanho aproximados').pack(anchor='w')
        self.canvas=tk.Canvas(frame,bg='#E7F0EA',height=100,highlightthickness=0); self.canvas.pack(fill='x',pady=(4,0))
        self.canvas.bind('<Configure>',self.preview)
        for v in (self.corner,self.panel,self.icon,self.opacity,self.enabled,self.floating,self.topmost,self.theme): trace_window(self.window, v, self.preview)
        self.bind_scroll_children(frame)
        self.bind_scroll_children(favorite_content)
    def scroll_content(self,parent):
        canvas=tk.Canvas(parent,highlightthickness=0,takefocus=True,height=200)
        canvas._aeris_scroll=True
        bar=ttk.Scrollbar(parent,orient='vertical',command=canvas.yview)
        bar.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
        canvas.configure(yscrollcommand=bar.set)
        content=ttk.Frame(canvas,padding=12); content._aeris_canvas=canvas
        item=canvas.create_window(0,0,anchor='nw',window=content)
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
        content.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        for key,amount,unit in (('<Up>',-1,'units'),('<Down>',1,'units'),('<Prior>',-1,'pages'),('<Next>',1,'pages')):
            canvas.bind(key,lambda e,a=amount,u=unit:canvas.yview_scroll(a,u))
        return content
    def bind_scroll_children(self,content):
        canvas=content._aeris_canvas
        def reveal(event):
            bounds=canvas.bbox('all'); visible=canvas.winfo_height()
            if not bounds or visible<=1 or bounds[3]<=visible: return
            y=event.widget.winfo_rooty()-content.winfo_rooty(); top=canvas.canvasy(0)
            bottom=y+event.widget.winfo_height()
            if y<top: canvas.yview_moveto(max(0,y/bounds[3]))
            elif bottom>top+visible: canvas.yview_moveto(max(0,(bottom-visible)/bounds[3]))
        def wheel(event):
            if event.delta: canvas.yview_scroll(-1 if event.delta>0 else 1,'units'); return 'break'
        def bind(widget):
            widget.bind('<MouseWheel>',wheel,add='+')
            widget.bind('<Button-4>',lambda e:canvas.yview_scroll(-1,'units'),add='+')
            widget.bind('<Button-5>',lambda e:canvas.yview_scroll(1,'units'),add='+')
            if isinstance(widget,(ttk.Checkbutton,ttk.Radiobutton,ttk.Combobox,tk.Scale)):
                widget.bind('<FocusIn>',reveal,add='+')
            for child in widget.winfo_children(): bind(child)
        bind(canvas)
    def values(self): return Appearance(self.corner.get(),self.icon.get(),self.panel.get(),self.opacity.get(),self.enabled.get(),self.floating.get(),self.topmost.get(),self.theme.get(),tuple(name for name,var in self.favorites.items() if var.get()),self.favorites_only.get())
    def preview(self,*_):
        c=self.canvas; c.delete('all'); w,h=c.winfo_width(),c.winfo_height()
        if min(w,h)<30: return
        p=self.values(); palette=PALETTES[p.theme]; c.configure(bg=palette['soft'])
        c.create_rectangle(10,10,w-10,h-10,fill=palette['field'],outline=palette['muted'])
        right=p.corner.endswith('direito'); bottom=p.corner.startswith('Inferior'); r=p.icon_size/3
        cx=w-18-r if right else 18+r; cy=h-18-r if bottom else 18+r
        if p.quick_enabled or p.floating_enabled:
            pw,ph=SIZES[p.panel_size]; pw=min(w*.42,pw*.32); ph=min(h-24,ph*.23)
            x=w-18-pw if right else 18; y=max(12,cy-r-ph-4) if bottom else min(h-ph-12,cy+r+4)
            a=p.opacity/100; color='#'+''.join(f'{round(a*int(palette["air"][i:i+2],16)+(1-a)*int(palette["field"][i:i+2],16)):02x}' for i in (1,3,5))
            c.create_rectangle(x,y,x+pw,y+ph,fill=color,outline=palette['forest']); c.create_text(x+8,y+12,text='aeris.',anchor='w',fill=palette['deep'])
        if p.floating_enabled:
            c.create_oval(cx-r,cy-r,cx+r,cy+r,fill='#285640',outline='')
            for dy in (-.35,0,.35): c.create_line(cx-r*.6,cy+r*dy,cx,cy+r*(dy-.25),cx+r*.6,cy+r*dy,smooth=True,fill='#DCEFE3',width=2)
    def reset(self):
        p=Appearance()
        for var,v in zip((self.corner,self.icon,self.panel,self.opacity,self.enabled,self.floating,self.topmost),(p.corner,p.icon_size,p.panel_size,p.opacity,p.quick_enabled,p.floating_enabled,p.floating_topmost)): var.set(v)
        self.theme.set(p.theme); self.favorites_only.set(p.favorites_only)
        for name,var in self.favorites.items(): var.set(name in p.favorites)
    def close(self):
        if self.values()==self.hub.settings.appearance or messagebox.askyesno('Descartar?','Descartar mudanças não salvas?',parent=self.window): self.window.destroy()
    def save(self):
        previous=self.hub.settings.appearance
        try: self.hub.settings.set_appearance(self.values())
        except (OSError,ValueError): messagebox.showerror('Aeris','Não foi possível salvar preferências.',parent=self.window); return
        if not previous.floating_enabled and self.hub.settings.appearance.floating_enabled: self.hub.spotlight_hidden=False
        self.hub.apply_appearance(); self.window.destroy()
