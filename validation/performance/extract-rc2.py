"""Read-only archive verification and safe extraction of exact RC2 portable bundle."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

OUTER = "628ff322f7ac3eba90741bb2142c8b79b0a331a33dd4d7a23a0b5e297e9688c3"
PORTABLE = "5b38a79f595a8a55c1643bce53fac9d74442d2a17fcb96927f89d18fb131fb10"
EXE = "1cfc9f494feb5d5b15646fef4c1dbbe6490377326abf59a309e0c56e4db551a4"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source, target = map(Path, sys.argv[1:])
    assert not target.exists(), "Fresh target required"
    raw = source.read_bytes()
    assert sha(raw) == OUTER, "Outer digest mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        name = "Aeris-1.0.0rc2-Windows-x64-portable.zip"
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
        assert set(manifest) == set(names) - {manifest_name} and len(manifest) == 91
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
