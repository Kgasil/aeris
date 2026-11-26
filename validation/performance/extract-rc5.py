"""Read-only archive verification and safe extraction of exact RC5 portable bundle."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

OUTER = "09aa2076cac6f9bc8a543869027fe2617f0590fd4509a6f18261def0e797ba9a"
PORTABLE = "ffbda95354b563e1d6a1b8f90fc43184a197585488c3da8609ac6970ffee9701"
EXE = "4cb9ed45a6e9cce9c1f86a9d71e6f915aba987ab3532e034e34bd9300b7d0025"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source, target = map(Path, sys.argv[1:])
    assert not target.exists(), "Fresh target required"
    raw = source.read_bytes()
    assert sha(raw) == OUTER, "Outer digest mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        name = "Aeris-1.0.0rc5-Windows-x64-portable.zip"
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
