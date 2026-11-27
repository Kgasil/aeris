"""Check antivirus evidence without authorizing distribution or changing scanner settings."""
import json
import re
import sys
from pathlib import Path

SETUP = "Aeris-1.1.0rc1-Windows-x64-Setup.exe"
PORTABLE = "Aeris-1.1.0rc1-Windows-x64-portable.zip"
TARGETS = {SETUP, PORTABLE, "Aeris"}
OK = "COMPLETED_NO_THREATS_REPORTED"


def read_json(path):
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def fresh(scan):
    age = scan.get("definition_age_seconds")
    return (scan.get("definitions_fresh") is True
            and type(age) in (int, float) and 0 <= age <= 86400)


def complete(rows):
    return (isinstance(rows, list) and len(rows) == 3
            and {row["target"] for row in rows} == TARGETS
            and all(row.get("outcome") == OK and type(row.get("exit_code")) is int
                    and row["exit_code"] == 0 for row in rows))


def verify(root, commit):
    errors = []
    inventory = read_json(root / "artifact-inventory.json")
    clam = read_json(root / "clamav-assurance.json")
    assurance = read_json(root / "assurance.json")
    defender = assurance.get("defender", {})
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("Invalid candidate commit")
    if any(report.get("commit") != commit for report in (clam, assurance)):
        errors.append("Report commit mismatch")
    if any(report.get("release_approved") is not False for report in (clam, assurance)):
        errors.append("Unexpected release authorization")
    if not isinstance(inventory, list) or len(inventory) != 2:
        errors.append("Invalid package inventory")
        hashes = {}
    else:
        hashes = {row["name"]: row["sha256"] for row in inventory}
        if (set(hashes) != {SETUP, PORTABLE}
                or not all(isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h)
                           for h in hashes.values())):
            errors.append("Invalid package hashes")
    if clam.get("candidate_package_hashes") != {"setup": hashes.get(SETUP),
                                                  "portable": hashes.get(PORTABLE)}:
        errors.append("ClamAV package hash mismatch")
    if (clam.get("status") != OK or not fresh(clam)
            or clam.get("scanner_archive_verified") is not True
            or clam.get("post_scan_integrity") != "PASS"
            or not complete(clam.get("targets"))):
        errors.append("ClamAV evidence incomplete, stale or failed")
    if (assurance.get("status") != "EVIDENCE_COLLECTED"
            or defender.get("status") != "COMPLETED_NO_MATCHED_DETECTIONS"
            or defender.get("antivirus_enabled") is not True
            or not fresh(defender) or not complete(defender.get("runs"))
            or type(defender.get("matched_detection_count")) is not int
            or defender["matched_detection_count"] != 0):
        errors.append("Defender evidence incomplete, stale or failed")
    return errors


def main():
    if len(sys.argv) != 3:
        print("Usage: check-scan-evidence.py EVIDENCE COMMIT", file=sys.stderr)
        return 2
    try:
        errors = verify(Path(sys.argv[1]), sys.argv[2])
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f"Evidence unavailable or invalid: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Antivirus evidence complete for candidate; independent release review still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
