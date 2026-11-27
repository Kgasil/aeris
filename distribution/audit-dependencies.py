"""Query OSV for the exact PyPI build inventory; no binary uploads."""
import datetime
import json
from pathlib import Path
import re
import sys
import urllib.request

URL = 'https://api.osv.dev/v1/querybatch'


def parse_inventory(text):
    packages = []
    seen = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.!+~-]*)', line.strip())
        if not match:
            raise ValueError('Unpinned or unsupported inventory entry')
        name, version = match.groups()
        name = re.sub(r'[-_.]+', '-', name).lower()
        if name in seen:
            raise ValueError('Duplicate package')
        seen.add(name)
        packages.append({'package': {'name': name, 'ecosystem': 'PyPI'}, 'version': version})
    if not 1 <= len(packages) <= 100:
        raise ValueError('Unexpected package count')
    return packages


def check_response(queries, response):
    results = response.get('results') if isinstance(response, dict) else None
    if not isinstance(results, list) or len(results) != len(queries):
        raise ValueError('Incomplete OSV response')
    findings = []
    for query, result in zip(queries, results):
        if not isinstance(result, dict) or result.get('next_page_token'):
            raise ValueError('Incomplete OSV result')
        vulns = result.get('vulns', [])
        if not isinstance(vulns, list) or any(not isinstance(v, dict) or not isinstance(v.get('id'), str) or not v['id'] for v in vulns):
            raise ValueError('Invalid OSV vulnerability record')
        findings.append({'name': query['package']['name'], 'version': query['version'], 'advisories': sorted({v['id'] for v in vulns})})
    return findings


def main(inventory, destination):
    report = {'scope': 'PyPI build inventory only; excludes embedded CPython libraries, Inno Setup, OS and optional external applications', 'source': URL, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'release_approved': False, 'status': 'INCONCLUSIVE'}
    try:
        queries = parse_inventory(Path(inventory).read_text(encoding='utf-8-sig'))
        report['queries'] = queries
        request = urllib.request.Request(URL, data=json.dumps({'queries': queries}).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.geturl() != URL:
                raise ValueError('Unexpected redirect')
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Response too large')
        report['packages'] = check_response(queries, json.loads(raw))
        report['status'] = 'ADVISORIES_FOUND' if any(p['advisories'] for p in report['packages']) else 'NO_REPORTED_ADVISORIES'
    except (OSError, ValueError, TypeError) as exc:
        report['error'] = str(exc)
    Path(destination).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('OSV build dependency review:', report['status'])
    # Missing or incomplete advisory evidence must not pass the candidate gate.
    return {'NO_REPORTED_ADVISORIES': 0, 'ADVISORIES_FOUND': 1, 'INCONCLUSIVE': 2}[report['status']]


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
