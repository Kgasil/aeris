"""Painel sob demanda, relativo ao Hub."""
import tkinter as tk
from tkinter import ttk
from aeris.scroll_area import scroll_area
from aeris.settings import SIZES

def panel_bounds(corner,size,host,screen):
    x,y,hw,hh=host; sw,sh=screen
    w,h=min(size[0],sw),min(size[1],sh)
    px=x+hw-w if corner.endswith('direito') else x
    py=y+hh-h if corner.startswith('Inferior') else y
    return w,h,max(0,min(px,sw-w)),max(0,min(py,sh-h))

class QuickPanel:
    def __init__(self,hub):
        root=hub.root; p=hub.settings.appearance; root.update_idletasks()
        self.window=tk.Toplevel(root); self.window.title('Aeris · acesso rápido'); self.window.transient(root)
        w,h,x,y=panel_bounds(p.corner,SIZES[p.panel_size],(root.winfo_rootx(),root.winfo_rooty(),root.winfo_width(),root.winfo_height()),(root.winfo_screenwidth(),root.winfo_screenheight()))
        self.window.geometry(f'{w}x{h}+{x}+{y}')
        try: self.window.attributes('-alpha',p.opacity/100)
        except tk.TclError: pass
        self.window.bind('<Escape>',lambda _:self.window.destroy())
        frame=ttk.Frame(self.window,padding=12); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='aeris.',font=('Segoe UI',20)).pack(anchor='w')
        ttk.Label(frame,text='Ambiente: '+hub.workspace_store.active[:30] if getattr(hub,'workspace_store',None) and hub.workspace_store.active else 'Ferramentas ativas').pack(anchor='w',pady=(0,8))
        if len(hub.quick_tools())>3:
            footer=ttk.Frame(frame); footer.pack(side='bottom',fill='x')
        else: footer=frame
        tools=hub.quick_tools()
        if len(tools)>3:
            tool_frame=scroll_area(frame)
            for col in range(2): tool_frame.columnconfigure(col,weight=1,uniform='tool')
            for i,(name,action) in enumerate(tools):
                ttk.Button(tool_frame,text=name,command=lambda a=action:self.launch(a)).grid(row=i//2,column=i%2,sticky='ew',padx=2,pady=1)
        else:
            for name,action in tools:
                ttk.Button(frame,text=name,command=lambda a=action:self.launch(a)).pack(fill='x',pady=2)
        if not hub.quick_tools(): ttk.Label(frame,text='Nenhuma ferramenta ativa neste painel.').pack(anchor='w')
        ttk.Button(footer,text='Configurações',command=lambda:self.launch(hub.open_appearance)).pack(fill='x',pady=2)
        ttk.Button(footer,text='Fechar',command=self.window.destroy).pack(fill='x',pady=2)
    def launch(self,action): self.window.destroy(); action()
