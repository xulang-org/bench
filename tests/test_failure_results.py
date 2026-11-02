"""Failed compiles/runs are evidence, never zero or fabricated timings."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import format_summary as summary
import bench_rusage as rusage


def report(records):
    names = list(dict.fromkeys(r['bench'] for r in records))
    return '# benches: ' + ', '.join(names) + '\n' + '\n'.join('# result: ' + json.dumps(r) for r in records)


class FailureResultsTests(unittest.TestCase):
    def test_failed_xu_and_failed_peer_preserve_case_and_null_metrics(self):
        raw = report([
            dict(bench='method_sum', impl='Xu', status='compile_failed', error='index out of bounds'),
            dict(bench='method_sum', impl='clang -O3', status='ok', wall_ms=4, best_ms=3, rss_mib=2, cpu_ms=1, bytes=100),
            dict(bench='method_sum', impl='go build', status='measurement_failed', error='RSS unavailable'),
        ])
        payload = summary.build_benchmark_payload(summary.parse_crosslang_txt(raw), {'xu_version': '0.11.2'})
        row, = payload['benches']
        self.assertEqual(payload['metadata']['total_benches'], 1)
        self.assertEqual(payload['metadata']['xu_failed_benches'], 1)
        self.assertEqual(row['xu_status'], 'compile_failed')
        self.assertEqual(row['xu_error'], 'index out of bounds')
        for key in ('xu_wall_ms', 'xu_best_ms', 'xu_rss_mib', 'xu_bytes', 'ratio_vs_c', 'go_wall_ms'):
            self.assertIsNone(row[key], key)
        self.assertEqual(row['c_wall_ms'], 4)
        self.assertIn('compile_failed', summary.generate_markdown_summary(payload))

    def test_mismatch_discards_even_supplied_metrics(self):
        parsed = summary.parse_crosslang_txt(report([dict(bench='fib', impl='Xu', status='stdout_mismatch',
                                                       error='wrong stdout', wall_ms=0.01, bytes=1)]))
        self.assertNotIn('wall_ms', parsed['fib']['Xu'])
        self.assertNotIn('bytes', parsed['fib']['Xu'])

    def test_partial_and_duplicate_records_are_rejected(self):
        one = dict(bench='fib', impl='Xu', status='run_failed', error='exit 1')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            summary.parse_crosslang_txt(report([one, one]))
        with self.assertRaisesRegex(ValueError, 'cover'):
            summary.parse_crosslang_txt(report([one]).replace('# benches: fib', '# benches: fib, method_sum'))

    def test_rss_exit_race_retries_a_complete_sample_and_verifies_output(self):
        calls = []
        def sample(args, **kwargs):
            calls.append(args)
            result = type('Result', (), {})()
            if len(calls) == 1:
                kwargs['stderr'].write(b'PTRACE_CONT: No such process')
                result.returncode = 2
            else:
                kwargs['stdout'].write(b'correct\n')
                Path(args[1]).write_text('4096 0\n')
                result.returncode = 0
            return result
        with patch.object(rusage, '_linux_rss_helper', return_value=(Path('/helper'), None)), \
             patch.object(rusage.subprocess, 'run', side_effect=sample):
            self.assertEqual(rusage._linux_peak_rss(['/program'], None, 1, b'correct\n', b'', 0, True), 4096)
            self.assertEqual(len(calls), 2)
            with self.assertRaisesRegex(RuntimeError, 'differs'):
                rusage._linux_peak_rss(['/program'], None, 1, b'wrong\n', b'', 0, True)

    def test_rss_retries_are_bounded_and_other_errors_fail_immediately(self):
        for error, expected in ((b'PTRACE_CONT: No such process', 3), (b'permission denied', 1)):
            def sample(args, **kwargs):
                kwargs['stderr'].write(error)
                return type('Result', (), {'returncode': 2})()
            with patch.object(rusage, '_linux_rss_helper', return_value=(Path('/helper'), None)), \
                 patch.object(rusage.subprocess, 'run', side_effect=sample) as run:
                with self.assertRaisesRegex(RuntimeError, 'RSS measurement failed'):
                    rusage._linux_peak_rss(['/program'], None, 1, b'', b'', 0, True)
                self.assertEqual(run.call_count, expected)
