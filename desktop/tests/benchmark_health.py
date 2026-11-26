"""Manual repeatable idle snapshot; never run at app startup. Not a Windows certification."""
import json
import sys
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.health import sample, measure, resident_memory


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk(); hub=Hub(root,Settings(Path(d)/'settings.json'))
        rows=[]
        def start(stage, index=0):
            before=sample()
            def finish():
                result=measure(before,sample(),resident_memory())
                rows.append({'stage':stage,'seconds':round(result.seconds,3),'cpu_percent_one_core':round(result.cpu_percent,3),'resident_bytes':result.resident_bytes})
                if index<2: root.after(300,lambda:start(stage,index+1))
                elif stage=='Hub':
                    hub.toggle_tool('Health'); hub.open_tool('Health'); root.after(500,lambda:start('Hub + Health'))
                else: root.destroy()
            root.after(2000,finish)
        root.after(500,lambda:start('Hub')); root.mainloop()
        print(json.dumps({'platform':sys.platform,'python':sys.version.split()[0],'samples':rows},indent=2))

if __name__=='__main__': main()
