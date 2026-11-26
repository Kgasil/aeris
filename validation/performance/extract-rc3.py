"""Read-only archive verification and safe extraction of exact RC3 portable bundle."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

OUTER = "de81221a8723a9c26f11db293e440c65243f4c4c53e8d2dd2d00afc0e94e270f"
PORTABLE = "4f8a6b6cdba4f4b4e43e5547d57cf48012c66f93cb72628c2a1fb7002a58cb23"
EXE = "94c329abe46a128719f8c951c7a8df2b8936d1550855089c9f0d25ed1cda37f5"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source, target = map(Path, sys.argv[1:])
    assert not target.exists(), "Fresh target required"
    raw = source.read_bytes()
    assert sha(raw) == OUTER, "Outer digest mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        name = "Aeris-1.0.0rc3-Windows-x64-portable.zip"
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
