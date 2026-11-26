"""Read-only audit of an Aeris Windows portable ZIP; never extracts or executes code."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def audit(path):
    manifest_name = "Aeris/BUNDLE-MANIFEST.json"
    with zipfile.ZipFile(path) as archive:
        entries = [i.filename for i in archive.infolist() if not i.is_dir()]
        if len(entries) != len(set(entries)):
            raise ValueError("Duplicate archive entries")
        for name in entries:
            parts = name.split("/")
            if parts[0] != "Aeris" or any(p in ("", ".", "..") for p in parts) or "\\" in name or ":" in name:
                raise ValueError(f"Unexpected archive path: {name}")
        manifest = json.loads(archive.read(manifest_name))
        expected = set(entries) - {manifest_name}
        if set(manifest) != expected:
            raise ValueError("Bundle manifest coverage mismatch")
        verified = {}
        for name in sorted(expected):
            digest = sha256(archive.read(name))
            if digest != manifest[name]:
                raise ValueError(f"Hash mismatch: {name}")
            verified[name] = digest
        notices = [n for n in verified if "/NOTICES/" in n or "license" in n.lower() or "copying" in n.lower()]
        binaries = [n for n in verified if n.lower().endswith((".dll", ".pyd", ".exe"))]
        if not any(n.endswith("PYTHON-LICENSE.txt") for n in notices):
            raise ValueError("Missing Python license")
        return {
            "archive_sha256": sha256(Path(path).read_bytes()),
            "verified_manifest_files": len(verified),
            "notice_files": {n: verified[n] for n in notices},
            "binary_files": {n: verified[n] for n in binaries},
            "review_status": "INVENTORY_ONLY_NOT_REDISTRIBUTION_APPROVAL",
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("portable_zip")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(audit(args.portable_zip), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
