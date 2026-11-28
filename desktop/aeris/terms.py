"""Offline terms acceptance for normal source/frozen Aeris startup."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timezone

def terms_path():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)/"distribution"/"TERMS-REVIEW.txt"
    return Path(__file__).resolve().parents[2]/"distribution"/"TERMS-REVIEW.txt"

def receipt_path():
    from aeris.settings import default_path
    return default_path().parent/"terms-acceptance.json"

def read_terms():
    raw=terms_path().read_bytes()
    if not 0<len(raw)<=65536: raise ValueError("Invalid terms length")
    return raw.decode("utf-8-sig"),hashlib.sha256(raw).hexdigest()

def accepted(path,digest):
    try:
        if path.is_symlink() or path.stat().st_size>4096: return False
        row=json.loads(path.read_text(encoding="utf-8"))
        return (set(row)=={"schema","terms_sha256","accepted_utc"} and type(row["schema"]) is int
                and row["schema"]==1 and row["terms_sha256"]==digest
                and isinstance(row["accepted_utc"],str)
                and datetime.fromisoformat(row["accepted_utc"]).utcoffset()==timezone.utc.utcoffset(None))
    except (OSError,ValueError,TypeError,KeyError): return False

def record(path,digest):
    if path.is_symlink(): raise ValueError("Receipt link refused")
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".terms-",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as out:
            json.dump({"schema":1,"terms_sha256":digest,"accepted_utc":datetime.now(timezone.utc).isoformat()},out)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def prompt(text,digest):
    import tkinter as tk
    root=tk.Tk()
    result=False
    try:
        root.title("Project Aeris — Termos / Terms")
        root.configure(bg="#172332")
        root.geometry("720x540")
        root.minsize(480,360)
        frame=tk.Frame(root,bg="#172332");frame.pack(fill="both",expand=True,padx=16,pady=12)
        tk.Label(frame,text="Project Aeris · Termos de uso / Terms of use",bg="#172332",fg="#E1EDF9",font=("TkDefaultFont",14,"bold")).pack(anchor="w")
        body=tk.Frame(frame);body.pack(fill="both",expand=True,pady=8)
        box=tk.Text(body,wrap="word",bg="#21354A",fg="#F0F5FA",padx=10,pady=10)
        scroll=tk.Scrollbar(body,command=box.yview);box.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y");box.pack(side="left",fill="both",expand=True)
        box.insert("1.0",text+"\n\nAceite apenas local; nenhum dado enviado. / Local acceptance only; no data transmitted.\nSHA-256: "+digest)
        box.configure(state="disabled")
        buttons=tk.Frame(frame,bg="#172332");buttons.pack(fill="x")
        def agree():
            nonlocal result
            result=True;root.destroy()
        decline=tk.Button(buttons,text="Recusar / Decline",command=root.destroy);decline.pack(side="left")
        tk.Button(buttons,text="Aceito / I accept",command=agree).pack(side="right")
        root.protocol("WM_DELETE_WINDOW",root.destroy)
        root.bind("<Escape>",lambda _:root.destroy())
        decline.focus_set()
        root.mainloop()
    finally:
        try: root.destroy()
        except tk.TclError: pass
    return result

def require_acceptance(path=None,ask=prompt):
    path=receipt_path() if path is None else Path(path)
    text,digest=read_terms()
    if accepted(path,digest): return True
    if not ask(text,digest): return False
    record(path,digest)
    return True

def forget():
    receipt_path().unlink(missing_ok=True)
