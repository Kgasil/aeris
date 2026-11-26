"""Bounded scrollable area for growing lists of tools and permissions."""
import tkinter as tk
from tkinter import ttk


def scroll_area(parent):
    outer=ttk.Frame(parent); outer.pack(fill='both',expand=True)
    canvas=tk.Canvas(outer,highlightthickness=0,height=100,takefocus=True)
    canvas._aeris_scroll=True
    scrollbar=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview)
    scrollbar.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)
    body=ttk.Frame(canvas); ident=canvas.create_window(0,0,window=body,anchor='nw')
    body.bind('<Configure>',lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e: canvas.itemconfigure(ident,width=e.width))
    canvas.bind('<Up>',lambda e: canvas.yview_scroll(-1,'units'))
    canvas.bind('<Down>',lambda e: canvas.yview_scroll(1,'units'))
    canvas.bind('<Prior>',lambda e: canvas.yview_scroll(-1,'pages'))
    canvas.bind('<Next>',lambda e: canvas.yview_scroll(1,'pages'))
    canvas.bind('<MouseWheel>',lambda e: canvas.yview_scroll(-1 if e.delta>0 else 1,'units') if e.delta else None)
    return body
