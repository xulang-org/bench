#!/usr/bin/env python3
"""Re-run archived benchmark binaries and verify their recorded fingerprints."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bench_rusage import run_one


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    report = json.loads((archive / 'report.json').read_text())
    if report.get('status') != 'PASS':
        raise SystemExit('archive is not a passing run')
    archived_manifest = archive / 'manifest.json'
    if not archived_manifest.is_file() or sha(archived_manifest) != report['manifest_sha256']:
        raise SystemExit('archived manifest hash mismatch')
    manifest = {e['name']: e for e in json.loads(archived_manifest.read_text())['entries']}
    if len(report['entries']) != (28 if report['scope'].startswith('full-28') else len(report['entries'])):
        raise SystemExit('archive entry count invalid')
    if len({e['name'] for e in report['entries']}) != len(report['entries']):
        raise SystemExit('archive has duplicate benchmark names')
    for row in report['entries']:
        name = row['name']
        if name not in manifest or row['args'] != manifest[name]['args']:
            raise SystemExit(f'{name}: manifest mismatch')
        work = archive / 'runs' / name.replace('/', '_')
        if not work.is_dir():
            raise SystemExit(f'{name}: missing working directory')
        for label, profile in row['profiles'].items():
            relative = Path(profile['binary'])
            if relative.is_absolute() or '..' in relative.parts:
                raise SystemExit(f'{name}/{label}: invalid archive binary path')
            binary = archive / relative
            if not binary.is_file() or sha(binary) != profile['sha256']:
                raise SystemExit(f'{name}/{label}: binary hash mismatch')
            if manifest[name]['kind'] == 'game':
                small = run_one([str(binary), *manifest[name]['verify_args']], cwd=work, timeout_s=120)
                got = hashlib.sha256(small.stdout).hexdigest()
                if small.returncode != 0 or got != manifest[name]['verify_golden_sha256']:
                    raise SystemExit(f'{name}/{label}: small-N golden mismatch')
            perf = run_one([str(binary), *row['args']], cwd=work, timeout_s=120)
            got = hashlib.sha256(perf.stdout).hexdigest()
            if perf.returncode != 0 or got != row['performance_stdout_sha256']:
                raise SystemExit(f'{name}/{label}: performance-N replay mismatch')
        print(f'PASS {name}')
    print(f'archive replay: PASS ({len(report["entries"])} benchmarks)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
