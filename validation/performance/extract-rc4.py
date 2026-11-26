"""Read-only archive verification and safe extraction of exact RC4 portable bundle."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

OUTER = "34e010bb31a574211185f9b6729669c1b7a794856fdbbf10ae425b665aba6d8b"
PORTABLE = "133ee4b5f861535740dca98639d6e4ed4c4fcc15079362434d203b61f498574f"
EXE = "05272bdfa2be694cba686171a91a55d51c9ff014344b91ba33fe77a47be5b37e"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source, target = map(Path, sys.argv[1:])
    assert not target.exists(), "Fresh target required"
    raw = source.read_bytes()
    assert sha(raw) == OUTER, "Outer digest mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        name = "Aeris-1.0.0rc4-Windows-x64-portable.zip"
        assert outer.namelist().count(name) == 1
        raw = outer.read(name)
    assert sha(raw) == PORTABLE, "Portable digest mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as inner:
        entries = [x for x in inner.infolist() if not x.is_dir()]
        names = [x.filename for x in entries]
        assert len(names) == len(set(x.casefold() for x in names)), "Duplicate paths"
        for info in entries:
            n = info.filename
            parts = n.split("/")
            assert parts[0] == "Aeris" and len(parts) > 1
            assert all(x and x not in (".", "..") and not x.endswith((".", " ")) for x in parts)
            assert "\\" not in n and ":" not in n
            assert (info.external_attr >> 16) & 0o170000 != 0o120000, "Symlink entry"
        manifest_name = "Aeris/BUNDLE-MANIFEST.json"
        manifest = json.loads(inner.read(manifest_name))
        assert set(manifest) == set(names) - {manifest_name} and len(manifest) == 47
        for n, digest in manifest.items():
            assert sha(inner.read(n)) == digest, "Manifest mismatch: " + n
        assert manifest["Aeris/Aeris.exe"] == EXE
        target.mkdir()
        for info in entries:
            path = target.joinpath(*PurePosixPath(info.filename).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as f:
                f.write(inner.read(info))
    print(json.dumps({"outer_sha256": OUTER, "portable_sha256": PORTABLE, "exe_sha256": EXE, "manifest_files": len(manifest), "integrity": "PASS", "release_approved": False}))

if __name__ == "__main__":
    main()
