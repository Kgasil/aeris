"""Check recorded release evidence; never certifies the evidence itself."""
import json
from pathlib import Path
import sys

REQUIRED = frozenset({
    'windows_build_x64', 'windows_10_clean_vm', 'windows_11_clean_vm',
    'installer_upgrade_uninstall_data', 'native_dpapi_mutex',
    'real_ollama_audio_ocr', 'performance_accessibility',
    'license_and_trust_review', 'published_artifacts_and_hashes',
})


def pending_checks(record, expected_version):
    if not isinstance(record, dict) or record.get('version') != expected_version:
        raise ValueError('Version mismatch')
    checks = record.get('checks')
    if not isinstance(checks, dict) or set(checks) != REQUIRED:
        raise ValueError('Missing or unexpected release checks')
    pending = []
    for name in sorted(REQUIRED):
        entry = checks[name]
        if not isinstance(entry, dict) or set(entry) != {'status', 'evidence'}:
            raise ValueError(f'Invalid check: {name}')
        if entry['status'] not in ('pending', 'failed', 'passed') or not isinstance(entry['evidence'], str):
            raise ValueError(f'Invalid evidence: {name}')
        if entry['status'] != 'passed' or not entry['evidence'].strip():
            pending.append(name)
    return pending


def main():
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root.parent / 'desktop'))
    from aeris import __version__
    from aeris.safe_input import strict_json
    try:
        with (root / 'release-gate.json').open('rb') as stream:
            record = strict_json(stream.read(65537), 65536)
        pending = pending_checks(record, __version__)
    except (OSError, ValueError, TypeError) as exc:
        print(f'Invalid release record: {exc}', file=sys.stderr)
        return 2
    if pending:
        print('BINARY RELEASE BLOCKED: ' + ', '.join(pending))
        return 1
    print('All checks have recorded evidence. Independent human review still required.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
