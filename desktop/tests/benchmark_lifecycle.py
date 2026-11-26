"""Isolated repeatable UI lifetime benchmark, no personal data or inference."""
import gc
import json
import sys
import tkinter as tk
import weakref
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris import __version__
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.health import resident_memory

TOOLS = ('Capture','Snippets','Search','Text','Calculator','Convert','Decision','Email','Link','Clipboard','Translate','Copilot')


def main():
    with TemporaryDirectory() as d:
        root=tk.Tk(); hub=Hub(root,Settings(Path(d)/'settings.json'))
        root.update(); gc.collect()
        initial = resident_memory()
        initial_modules = sorted(m for m in sys.modules if m.startswith('aeris.'))
        refs=[]
        cycles=5
        try:
            for _ in range(cycles):
                for name in TOOLS:
                    if not hub.enabled(name): hub.toggle_tool(name)
                    hub.open_tool(name)
                    obj=getattr(hub,name.lower()+'_window')
                    root.update()
                    if name=='Copilot':
                        obj.open_companion(); root.update()
                        refs.append(weakref.ref(obj.companion))
                        obj.companion.window.destroy()
                    refs.append(weakref.ref(obj)); obj.window.destroy(); del obj
                    root.update()
            gc.collect()
            retained=sum(ref() is not None for ref in refs)
            closed_references=sum(getattr(hub,name.lower()+'_window') is not None for name in TOOLS)
            result=dict(version=__version__, platform=sys.platform, python=sys.version.split()[0], tools=list(TOOLS), cycles=cycles, windows=len(refs), retained_objects=retained, closed_hub_references=closed_references, rss_initial_bytes=initial, rss_after_bytes=resident_memory(), initial_aeris_modules=initial_modules)
        finally: root.destroy()
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
