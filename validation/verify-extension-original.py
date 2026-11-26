"""Verify both original Aeris Extension ZIPs and prepare a temporary test checkout."""
import hashlib, json, stat, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "Aeris-Extension-v1.0.0/"
HASHES = {"install":"e77e6e8596c14e54f22303e7a5d368356c19eaa79df8c8597752790755d9a0d9",
          "completa":"d0f064c1b73c46465171cc1fb208b530ed66573e054c2ca211b216547bbb3c00"}
RUNTIME = {"app.js","automation.js","connect.js","context.js","core.js","intelligent-text.js","session.js","index.html","manifest.json","style.css","icons/128.png","icons/16.png","icons/32.png","icons/48.png","icons/symbol.svg"}
SOURCE = {PREFIX+"extension/"+n for n in RUNTIME} | {PREFIX+n for n in ("PRIVACY.md","README.md","RELEASE.md","pack.py","package.json","tests/browser_smoke.py","tests/core.test.mjs","tests/ui_mock_smoke.py")}
def check(ok, message):
    if not ok:
        raise SystemExit(message)
def read(kind, names):
    p = ROOT/"downloads"/f"Aeris-Extension-v1.0.0-{kind}.zip"
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    check(h == HASHES[kind], f"{kind}: SHA-256 mismatch")
    with zipfile.ZipFile(p) as z:
        entries = z.infolist()
        check(len(entries)==len(names) and set(z.namelist())==names, "Unexpected or duplicate entries")
        check(all(not i.is_dir() and not (i.flag_bits&1) and not stat.S_ISLNK(i.external_attr>>16) and i.file_size<=100000 for i in entries), "Unexpected archive entry")
        check(z.testzip() is None, "CRC mismatch")
        print(f"{kind}: SHA-256, {len(entries)} entries, CRC PASS")
        return {n:z.read(n) for n in names}
def main():
    install, full = read("install", RUNTIME), read("completa", SOURCE)
    check(all(install[n]==full[PREFIX+"extension/"+n] for n in RUNTIME), "Runtime parity mismatch")
    m=json.loads(install["manifest.json"])
    check(m["manifest_version"]==3 and m["version"]=="1.0.0", "Version mismatch")
    check(m["permissions"]==["activeTab","scripting","storage"] and m["optional_host_permissions"]==["http://127.0.0.1/*"], "Permission change")
    check(set(m)=={"manifest_version","name","version","version_name","description","permissions","action","icons","content_security_policy","optional_host_permissions"}, "Manifest capability change")
    check(m["action"]["default_popup"]=="index.html", "Entry point changed")
    expected={"default-src":"'none'","script-src":"'self'","style-src":"'self'","img-src":"'self'","object-src":"'none'","connect-src":"http://127.0.0.1:11434","base-uri":"'none'","form-action":"'none'","frame-src":"'none'"}
    csp=dict(s.strip().split(None,1) for s in m["content_security_policy"]["extension_pages"].split(";") if s.strip())
    check(csp==expected, "CSP change")
    p=json.loads(full[PREFIX+"package.json"])
    check(not any(p.get(k) for k in ("dependencies","devDependencies","optionalDependencies","peerDependencies")), "Unexpected npm dependency")
    print("15/15 runtime files identical; manifest, CSP and npm dependency checks PASS")
    if len(sys.argv)>1:
        out=Path(sys.argv[1])
        out.mkdir(parents=True,exist_ok=False)
        for name, data in full.items():
            dest=out/name.removeprefix(PREFIX)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
    print("Integrity only; not an antivirus scan or approval.")
if __name__=="__main__":
    main()
