"""Read-only verification of an exact Aeris installer CI artifact; never approves release."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

def digest(data):
    return hashlib.sha256(data).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify(path, expected):
    raw = Path(path).read_bytes()
    require(re.fullmatch(r"[0-9a-fA-F]{64}", expected) is not None, "Expected independent SHA-256")
    require(digest(raw) == expected.lower(), "Outer archive digest mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [i.filename for i in z.infolist() if not i.is_dir()]
        require(len(names) == len(set(names)), "Duplicate outer archive entries")
        def load(name):
            return json.loads(z.read(name).decode("utf-8-sig"))
        setup = [n for n in names if re.fullmatch(r"Aeris-[0-9a-z.]+-Windows-x64-Setup\.exe", n)]
        portable = [n for n in names if re.fullmatch(r"Aeris-[0-9a-z.]+-Windows-x64-portable\.zip", n)]
        require(len(setup) == len(portable) == 1, "Expected exactly two distribution assets")
        require(setup[0].replace("-Setup.exe", "") == portable[0].replace("-portable.zip", ""), "Asset version mismatch")
        sums = {}
        for line in z.read("SHA256SUMS.txt").decode("utf-8-sig").splitlines():
            parts = line.split(None, 1)
            require(len(parts) == 2 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]), "Invalid checksum line")
            require(parts[1] not in sums, "Duplicate checksum")
            sums[parts[1]] = parts[0].lower()
        assets = {n: digest(z.read(n)) for n in setup + portable}
        require(sums == assets, "Asset checksums mismatch")
        checks = load("setup-validation.json")
        for key in ("install", "reinstall_same_version", "uninstall", "synthetic_data_preserved", "shortcut_targets", "shortcut_cleanup", "silent_no_launch"):
            require(checks.get(key) == "PASS", "Missing CI check: " + key)
        exe_hash = z.read("AERIS-EXE-SHA256.txt").decode("utf-8-sig").strip().lower()
        for name in ("portable-validation.json", "installed-validation.json", "reinstalled-validation.json"):
            e = load(name)
            require(e.get("self_test_full") == "PASS" and e.get("exe_sha256", "").lower() == exe_hash, "Invalid packaged validation: " + name)
        with zipfile.ZipFile(io.BytesIO(z.read(portable[0]))) as p:
            entries = [i.filename for i in p.infolist() if not i.is_dir()]
            require(len(entries) == len(set(entries)), "Duplicate portable entries")
            manifest_name = "Aeris/BUNDLE-MANIFEST.json"
            for n in entries:
                require(n.startswith("Aeris/") and not any(x in ("", ".", "..") for x in n.split("/")) and "\\" not in n and ":" not in n, "Unsafe portable path")
            manifest = json.loads(p.read(manifest_name))
            require(set(manifest) == set(entries) - {manifest_name}, "Manifest coverage mismatch")
            for n, sha in manifest.items():
                require(digest(p.read(n)) == sha, "Manifest mismatch: " + n)
            require(manifest.get("Aeris/Aeris.exe") == exe_hash, "Executable hash mismatch")
        return {"outer_sha256": expected.lower(), "asset_sha256": assets, "manifest_verified": len(manifest), "exe_sha256": exe_hash, "ci_checks": checks, "security_inventory_present": "security-evidence/binary-inventory.json" in names, "release_approved": False, "scope": "Integrity and reported CI checks only; not malware, rights, signature or OS certification."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact")
    parser.add_argument("--expected-sha256", required=True, help="Independent GitHub Actions artifact digest")
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact, args.expected_sha256), indent=2))
