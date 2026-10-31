#!/usr/bin/env python3
"""Archived, fail-closed Xu/Clang O3 comparison for the fixed 28-item suite.

The default run covers all 28 items. --benches is for explicitly labelled
smokes only; its output is never a full-suite baseline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
from pathlib import Path

from bench_clang_gap_manifest import MANIFEST, ROOT, load_manifest
from bench_crosslang import resolve_product_compiler
from bench_rusage import run_one
from product_compiler import product_compile_argv

XU_ROOT = Path(os.environ.get("XU_ROOT", ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(XU_ROOT / "scripts"))
from companion_repos import project_root

PRODUCT_RUNNER = XU_ROOT / "scripts/run_product_compiler.sh"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def cmd(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, check=False)


def source_closure() -> dict[str, str]:
    # Hash the local compiler, stdlib, runtime, benchmark and runner inputs.
    # Includes untracked files so a dirty source tree cannot hide dependencies.
    closure = {}
    for label, checkout, domains in (
        ("xu", XU_ROOT, ("src", "scripts")),
        ("xu-bench", ROOT, ("tests/bench", "scripts")),
    ):
        paths = []
        for domain in domains:
            folder = checkout / domain
            paths.extend(p for p in folder.rglob("*") if p.is_file() and
                         "__pycache__" not in p.parts and not p.name.endswith(".pyc"))
        paths.extend(p for p in (checkout / "Makefile", checkout / "VERSION") if p.is_file())
        closure.update({f"{label}/{p.relative_to(checkout)}": sha(p) for p in sorted(set(paths))})
    return closure


def execute(binary: Path, args: list[str], work: Path) -> dict:
    result = run_one([str(binary), *args], cwd=work, timeout_s=120)
    return {'rc': result.returncode, 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
            'stdout_bytes': len(result.stdout), 'stderr': result.stderr.decode(errors='replace')[-1000:],
            'wall_ms': result.wall_s * 1000, 'cpu_ms': result.cpu_s * 1000,
            'rss_mib': result.max_rss_mib}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True,
                        help='new directory; existing paths are refused')
    parser.add_argument('--xu', help='hosted baseline compiler (default: bin/xu)')
    parser.add_argument('--candidate', help='optional hosted candidate compiler')
    parser.add_argument('--clang', default='clang')
    parser.add_argument('--benches', help='comma-separated smoke subset')
    parser.add_argument('--pairs', type=int, default=15)
    args = parser.parse_args()
    entries = load_manifest()
    if args.pairs < 1:
        parser.error('--pairs must be positive')
    if args.benches is not None:
        if not args.benches:
            parser.error('--benches must not be empty')
        wanted = args.benches.split(',')
        if not wanted or len(set(wanted)) != len(wanted):
            parser.error('empty or duplicate benchmark names')
        known = {e['name'] for e in entries}
        if not set(wanted) <= known:
            parser.error(f'unknown benchmark: {sorted(set(wanted)-known)}')
        entries = [e for e in entries if e['name'] in wanted]
    baseline = resolve_product_compiler(args.xu)
    candidate = resolve_product_compiler(args.candidate) if args.candidate else None
    clang_version = cmd([args.clang, '--version'], 15)
    if clang_version.returncode:
        raise SystemExit('clang --version failed')
    clang_binary = shutil.which(args.clang)
    if clang_binary is None:
        raise SystemExit('clang executable not found')
    compilers = {'baseline': baseline}
    if candidate:
        compilers['candidate'] = candidate
    compiler_hashes = {name: sha(path) for name, path in compilers.items()}
    closure_before = source_closure()
    out = args.out_dir.expanduser().absolute()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(MANIFEST, out / 'manifest.json')
    report = {'schema': 1, 'started': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': ('smoke-subset' if args.benches is not None else
                        'full-28' if args.pairs >= 15 else 'full-28-exploratory'),
              'manifest_sha256': sha(MANIFEST),
              'host': platform.platform(), 'machine': platform.machine(),
              'clang_version': clang_version.stdout.decode(errors='replace').splitlines()[0],
              'clang_binary': clang_binary,
              'clang_sha256': sha(Path(clang_binary)),
              'compilers': {k: {'path': str(p), 'sha256': compiler_hashes[k]} for k,p in compilers.items()},
              'source_closure_before': closure_before,
              'git_head': cmd(['git', 'rev-parse', 'HEAD'], 15).stdout.decode().strip(),
              'git_status': cmd(['git', 'status', '--short'], 15).stdout.decode(),
              'pairs': args.pairs, 'entries': []}
    (out / 'artifacts').mkdir()
    (out / 'runs').mkdir()
    try:
        for entry in entries:
            name = entry['name']
            safe = name.replace('/', '_')
            paths: dict[str, Path] = {}
            row = {'name': name, 'args': entry['args'], 'profiles': {}, 'samples': []}
            report['entries'].append(row)
            for label in [*compilers, 'clang-O3']:
                # Explicit .bin keeps a known output path.
                suffix = '.bin'
                binary = out / 'artifacts' / f'{safe}-{label}{suffix}'
                source = ROOT / (entry['c_source'] if label == 'clang-O3' else entry['xu_source'])
                argv = ([args.clang, '-O3', str(source), '-o', str(binary), '-lm'] if label == 'clang-O3'
                        else product_compile_argv(compilers[label], 'build', str(source), '-O3', '-o', str(binary), runner=PRODUCT_RUNNER))
                compiled = cmd(argv)
                if compiled.returncode != 0 or not binary.is_file():
                    raise RuntimeError(f'{name}/{label}: compile failed: {compiled.stderr.decode(errors="replace")[-2000:]}')
                paths[label] = binary
                row['profiles'][label] = {'binary': str(binary.relative_to(out)), 'sha256': sha(binary),
                                          'bytes': binary.stat().st_size, 'command': argv}
            work = out / 'runs' / safe
            work.mkdir()
            if entry['kind'] == 'game':
                for label, binary in paths.items():
                    verify = execute(binary, entry['verify_args'], work)
                    row['profiles'][label]['verify'] = verify
                    if verify['rc'] != 0 or verify['stdout_sha256'] != entry['verify_golden_sha256']:
                        raise RuntimeError(f'{name}/{label}: small-N golden mismatch')
                expected = None  # Performance-N fingerprint established by cross-profile equality.
            else:
                expected = entry['golden_sha256']
            for label, binary in paths.items():
                probe = execute(binary, entry['args'], work)
                row['profiles'][label]['untimed_probe'] = probe
                if probe['rc'] != 0:
                    raise RuntimeError(f'{name}/{label}: performance-N probe failed')
                if expected is None:
                    expected = probe['stdout_sha256']
                    row['performance_golden_origin'] = 'cross-profile-equality'
                if probe['stdout_sha256'] != expected:
                    raise RuntimeError(f'{name}/{label}: performance-N stdout mismatch')
            row['performance_stdout_sha256'] = expected
            labels = list(paths)
            # One untimed probe above is the warm-up. Alternate a shuffled
            # profile order per pair; every sample is checked before recording.
            rng = random.Random(20260923)
            for pair in range(args.pairs):
                order = labels[:]
                rng.shuffle(order)
                if pair % 2:
                    order.reverse()
                for label in order:
                    sample = execute(paths[label], entry['args'], work)
                    sample.update(pair=pair, label=label)
                    row['samples'].append(sample)
                    if sample['rc'] != 0 or sample['stdout_sha256'] != expected:
                        raise RuntimeError(f'{name}/{label}: measured output mismatch, pair {pair}')
            print(f'PASS {name} ({args.pairs} pairs)', flush=True)
        if source_closure() != closure_before:
            raise RuntimeError('source closure changed during measurement')
        for label, path in compilers.items():
            if sha(path) != compiler_hashes[label]:
                raise RuntimeError(f'{label} compiler changed during measurement')
        report['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
        report['status'] = 'PASS'
    except Exception as exc:
        report['status'] = 'FAIL'
        report['error'] = str(exc)
        (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        raise
    (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'archived {out / "report.json"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
