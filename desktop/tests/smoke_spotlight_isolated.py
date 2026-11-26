import tkinter as tk
from types import SimpleNamespace
from aeris.spotlight import Spotlight

def main():
    root=tk.Tk(); root.geometry('400x300'); root.update()
    calls=[]
    prefs=SimpleNamespace(corner='Inferior direito',icon_size=36,panel_size='Normal',opacity=100,floating_topmost=False,theme='Claro')
    hub=SimpleNamespace(root=root,settings=SimpleNamespace(appearance=prefs,capture_enabled=True,snippets_enabled=False,search_enabled=True),open_capture=lambda:calls.append('Capture'),open_snippets=lambda:calls.append('Snippets'),open_search=lambda:calls.append('Search'))
    hub.quick_tools=lambda:[('Capture',hub.open_capture),('Search',hub.open_search)]
    hub.hide_spotlight=lambda: icon.destroy()
    icon=Spotlight(hub); root.update(); assert icon.window.winfo_exists()
    icon.button.event_generate('<ButtonRelease-1>',x=12,y=12); root.update(); assert icon.panel and icon.panel.winfo_exists()
    from tkinter import ttk
    buttons=[w for frame in icon.panel.winfo_children() for w in frame.winfo_children() if isinstance(w,ttk.Button)]
    assert [b.cget('text') for b in buttons]==['Capture','Search','Hub / Configurações','Ocultar ícone']
    buttons[0].invoke(); root.update(); assert calls==['Capture'] and icon.panel is None
    icon.toggle(); root.update(); assert icon.panel.winfo_exists(); icon.toggle(); root.update(); assert icon.panel is None
    icon.toggle(); root.update(); icon.dismiss(); assert icon.panel is None
    icon.destroy(); root.destroy(); print('Smoke isolado Spotlight: OK')

if __name__ == "__main__":
    main()
