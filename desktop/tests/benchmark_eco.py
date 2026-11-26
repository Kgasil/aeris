"""Isolated-process benchmark, no inference, no microphone, no real records.
Run: python -m tests.benchmark_eco (or xvfb-run -a on Linux).
"""
import json
import sys
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris import __version__
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.health import sample, measure, resident_memory
from aeris.companion_ui import CompanionWindow


def main():
    with TemporaryDirectory() as d:
        root = tk.Tk(); hub = Hub(root, Settings(Path(d)/'settings.json'))
        rows = []; counts = [0]
        original = CompanionWindow.poll
        def counted(self):
            counts[0] += 1
            return original(self)
        CompanionWindow.poll = counted
        def start(stage, index=0):
            before = sample(); callbacks = counts[0]
            def finish():
                m = measure(before, sample(), resident_memory())
                rows.append(dict(stage=stage, seconds=round(m.seconds,3), cpu_percent_one_core=round(m.cpu_percent,3), resident_bytes=m.resident_bytes, companion_poll_callbacks=counts[0]-callbacks))
                if index < 2: root.after(300, lambda: start(stage,index+1))
                elif stage == 'Hub':
                    hub.toggle_tool('Copilot'); hub.open_tool('Copilot'); hub.copilot_window.open_companion()
                    root.after(500, lambda: start('Hub + Copilot + Companion idle'))
                else: root.destroy()
            root.after(2000, finish)
        try:
            root.after(500, lambda: start('Hub')); root.mainloop()
        finally: CompanionWindow.poll = original
        print(json.dumps(dict(version=__version__,platform=sys.platform,python=sys.version.split()[0],samples=rows),indent=2))

if __name__ == '__main__': main()
