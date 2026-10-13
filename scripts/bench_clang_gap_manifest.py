#!/usr/bin/env python3
"""Validate the frozen 22 micro + 6 Game Xu/Clang comparison manifest."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tests/bench/clang_gap_manifest.json'
sys.path.insert(0, str(ROOT / 'scripts'))
from bench_crosslang import BY_NAME as MICRO  # noqa: E402
from bench_game import BY_NAME as GAME, QUICK_PERF_N  # noqa: E402
from bench_clang_gap_reference import REFERENCES  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> list[dict]:
    document = json.loads(MANIFEST.read_text())
    if document.get('schema') != 1:
        raise ValueError('unsupported manifest schema')
    entries = document.get('entries')
    if not isinstance(entries, list) or len(entries) != 28:
        raise ValueError('manifest must contain exactly 28 entries')
    names = [e['name'] for e in entries]
    if len(set(names)) != len(names):
        raise ValueError('duplicate benchmark name')
    manifest_micros = {e['name'] for e in entries if e.get('kind') == 'micro'}
    manifest_games = {e['name'] for e in entries if e.get('kind') == 'game'}
    expected_game = {f'game/{name}' for name in GAME}
    if manifest_games != expected_game:
        raise ValueError(f'game names differ: missing={sorted(expected_game - manifest_games)}, extra={sorted(manifest_games - expected_game)}')
    if not (manifest_micros <= (set(MICRO) | set(REFERENCES))):
        raise ValueError(f'unknown micro names: {sorted(manifest_micros - (set(MICRO) | set(REFERENCES)))}')
    if len(manifest_micros) != 22:
        raise ValueError(f'manifest must contain 22 micro entries, got {len(manifest_micros)}')
    for e in entries:
        name = e['name']
        for field in ('xu_source', 'c_source'):
            path = ROOT / e[field]
            if not path.is_file() or not path.resolve().is_relative_to(ROOT):
                raise ValueError(f'{name}: missing or invalid {field}')
        if e['kind'] == 'micro':
            if e['args']:
                raise ValueError(f'{name}: micro arguments changed')
            if name in REFERENCES:
                if e['golden_origin'] != 'independent-reference':
                    raise ValueError(f'{name}: independent reference origin missing')
                actual = (ROOT / f'tests/bench/golden/{name}.txt').read_bytes()
                if actual != REFERENCES[name]().encode():
                    raise ValueError(f'{name}: independent reference changed')
            else:
                if e['golden_origin'] != 'bench_crosslang-locked':
                    raise ValueError(f'{name}: locked golden origin changed')
                actual = MICRO[name].expect.encode()
            if digest(actual) != e['golden_sha256']:
                raise ValueError(f'{name}: micro golden hash mismatch')
        else:
            short = name.split('/', 1)[1]
            game = GAME[short]
            if e['args'] != [str(QUICK_PERF_N[short])] or e['verify_args'] != [str(game.verify_n)]:
                raise ValueError(f'{name}: Game input changed')
            golden = ROOT / e['verify_golden']
            if golden != ROOT / 'tests/bench/game/golden' / game.golden:
                raise ValueError(f'{name}: Game golden path changed')
            if digest(golden.read_bytes()) != e['verify_golden_sha256']:
                raise ValueError(f'{name}: Game golden hash mismatch')
    return entries


if __name__ == '__main__':
    try:
        entries = load_manifest()
    except (ValueError, KeyError, FileNotFoundError, TypeError) as exc:
        raise SystemExit(f'clang-gap manifest: FAIL: {exc}')
    print(f'clang-gap manifest: PASS ({len(entries)} entries; 22 micro, 6 Game)')
