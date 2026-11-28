"""Bind exact Microsoft runtime inventory to verified source proof, not legal certification."""
import json,re,sys
from pathlib import Path
EXPECTED={"vcruntime140.dll":"d1f4225df2cd877dbf130d5668a021dce3f94118455ff5ec952061c30afc9ce7","vcruntime140_1.dll":"a7146c08f89fe5b04541ab507cdb59ff7b44534d4ba3c668a426c6450a03434e"}
PATTERN=re.compile(r"^(vcruntime|msvcp|msvcr|concrt|vcomp|ucrtbase|api-ms-win-crt|mfc|atl|vccorlib).*\.dll$",re.I)
def require(ok,msg):
    if not ok: raise ValueError(msg)
def verify(source,inventory,reduction):
    require(source.get("status")=="EXACT_SOURCE_MATCH" and source.get("release_approved") is False and source.get("artifact_id")==15261460820 and source.get("artifact_sha256")=="3ae069412bf5b194a2a37da6f3dfb595a8dfc0e3ed5a896b028d3bd0bc38759f" and source.get("files")==EXPECTED,"source evidence mismatch")
    actual={}
    for row in inventory:
        name=row["path"].replace("\\","/").rsplit("/",1)[-1].lower()
        if not PATTERN.fullmatch(name): continue
        require(name not in actual and row.get("authenticode")=="Valid","duplicate or unsigned Microsoft runtime")
        actual[name]=row["sha256"]
    require(actual==EXPECTED,"actual named Microsoft runtime files differ from reviewed source")
    rows=reduction["remaining_vcruntime"]
    require(len(rows)==2 and {r["name"].lower():r["sha256"] for r in rows}==EXPECTED and all(r.get("exact_python_match") is True and r["sha256"]==r["python_source_sha256"] for r in rows),"runtime source mismatch")
    return {"status":"EXACT_SOURCE_MATCH","files":actual,"artifact_id":15261460820,"scope":"named runtime DLL source provenance only","release_approved":False}
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
if __name__=="__main__":
    if len(sys.argv)!=5:raise SystemExit("usage: source inventory reduction output")
    report=verify(*map(read,sys.argv[1:4]))
    Path(sys.argv[4]).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
