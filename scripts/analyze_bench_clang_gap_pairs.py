#!/usr/bin/env python3
"""Summarize paired benchmark samples with a bootstrap CI on log time ratios."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from pathlib import Path


def pair_map(samples: list[dict], label: str, pairs: int) -> dict[int, float]:
    selected = [s for s in samples if s['label'] == label]
    result = {s['pair']: s['wall_ms'] for s in selected}
    if len(selected) != pairs or len(result) != pairs or set(result) != set(range(pairs)):
        raise ValueError(f'{label}: missing or duplicated pair')
    if any(value <= 0 for value in result.values()):
        raise ValueError(f'{label}: nonpositive wall time')
    return result


def summarize(report: dict, baseline: str, candidate: str) -> list[dict]:
    if report.get('status') != 'PASS':
        raise ValueError('report is not a passing run')
    pairs = report['pairs']
    if pairs < 1:
        raise ValueError('report has no pairs')
    rows = []
    for entry in report['entries']:
        a = pair_map(entry['samples'], baseline, pairs)
        b = pair_map(entry['samples'], candidate, pairs)
        logs = [math.log(b[i] / a[i]) for i in range(pairs)]
        rng = random.Random(20260923)
        draws = sorted(math.exp(statistics.mean(rng.choices(logs, k=pairs))) for _ in range(10000))
        low, high = draws[250], draws[9750]
        status = ('improved' if high < 0.95 else
                  'regressed' if low > 1.05 else 'unclear')
        rows.append({'bench': entry['name'], 'pairs': pairs,
                     'base_median_ms': round(statistics.median(a.values()), 4),
                     'candidate_median_ms': round(statistics.median(b.values()), 4),
                     'paired_geomean_ratio': round(math.exp(statistics.mean(logs)), 6),
                     'ci95_low': round(low, 6), 'ci95_high': round(high, 6),
                     'status': status})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--base', default='baseline')
    parser.add_argument('--candidate', default='candidate')
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    rows = summarize(report, args.base, args.candidate)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
