"""Rebuild the ten reviewed overlays against the reconstructed historical source.
No expired Actions artifact is required. The manifest pins the reviewed UI/logic
bytes; the only new changes below are test-lifecycle cleanup and source metadata.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PHASES=("core","productivity","memory","quick-actions","communication","learning","intelligence","business","files","security")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integrate(desktop, evidence):
    desktop=Path(desktop).resolve()
    evidence=Path(evidence).resolve()
    here=Path(__file__).resolve().parent
    if (desktop/"aeris"/"__init__.py").read_text(encoding="utf-8").strip()!='__version__ = "1.0.0rc5"':
        raise ValueError("Expected reconstructed RC5 build metadata")
    manifest=json.loads((here/"security-source-hashes.json").read_text(encoding="utf-8"))
    for phase in PHASES:
        subprocess.run([sys.executable,str(here/f"apply-{phase}.py"),str(desktop)],check=True)
        name="test_"+phase.replace("-","_")+"_refinement.py"
        raw=(here/name).read_bytes()
        text=raw.decode("utf-8").replace("\r\n","\n")
        marker="    def setUp(self):\n"
        if text.count(marker)!=1: raise ValueError("Unexpected fixture: "+name)
        # Collect orphaned Tk references on the main test thread, after the
        # existing cleanup callbacks destroy their windows and release storage.
        # Never disable collection or suppress unraisable exceptions.
        text=text.replace(marker, """    def _collect_ui(self):
        import gc
        self.h=None
        self.root=None
        gc.collect()

    def setUp(self):
        self.addCleanup(self._collect_ui)
""",1)
        compile(text,name,"exec")
        target=desktop/"tests"/name
        target.write_bytes(text.encode("utf-8"))
    files=manifest["files"]
    if len(files)!=54: raise ValueError("Expected 54 reviewed source files")
    for name,expected in files.items():
        if Path(name).name!=name or sha(desktop/"aeris"/name)!=expected:
            raise ValueError("Refined source hash mismatch: "+name)
    if sha(desktop/"tests"/"smoke_autofill.py")!=manifest["autofill_smoke_sha256"]:
        raise ValueError("Autofill smoke mismatch")
    # Complete source inventory, not just the refined files.
    paths=sorted(p for p in desktop.parent.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    inventory={p.relative_to(desktop.parent).as_posix():sha(p) for p in paths}
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/"integrated-source-manifest.json").write_text(json.dumps({"reviewed_source":files,"source_files":inventory,"scope":"exact assembled source before packaging; no public release approval"},indent=2)+"\n",encoding="utf-8")
    print(f"All {len(files)} reviewed files match Security evidence; ten phases integrated into {len(inventory)} source files.")

if __name__=="__main__":
    integrate(sys.argv[1],sys.argv[2])
