"""Tests for wall-clock-optimal CI benchmark sharding and lossless platform shard merging."""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402


def _make_identity(target: str, xu_version: str = "0.14.1") -> dict:
    return {
        "xu_commit": "a" * 40,
        "bench_commit": "b" * 40,
        "xu_version": xu_version,
        "target": target,
        "compiler_sha256": (target.encode().hex() * 16)[:64],
        "source_closure_sha256": "c" * 64,
        "seed_sha256": "d" * 64,
        "fixed_point_pair": "gen2_gen3",
    }


def _make_shard_report(
    benches: list[str],
    shard_idx: int,
    shard_total: int,
    *,
    toolchains: dict[str, str | None] | None = None,
    rss_method: str = "linux-post-exec-vmhwm-v1",
    fail_xu_bench: str | None = None,
) -> str:
    tc = toolchains or {
        "clang": "Ubuntu clang version 18.1.3",
        "rustc": "rustc 1.84.0",
        "go": "go version go1.23.4 linux/arm64",
        "swiftc": "Swift version 6.0",
    }
    lines = [
        "# host: Linux aarch64",
        "# date: 2026-11-26 00:00",
        "# lane: product",
        "# xu: ../bench-compiler/xu (hosted product)",
        "# xu target: host default",
        "# run: best+median wall of 7 discard-first=yes; median peak RSS + CPU(user+sys)",
        "# curves: disabled (--sample-ms=0)",
        f"# rss_method: {rss_method}",
        f"# benches: {', '.join(benches)}",
        f"# shard: {shard_idx}/{shard_total}",
    ]
    for key in ("go", "clang", "rustc", "swiftc"):
        if tc.get(key):
            lines.append(f"# {key}: {tc[key]}")
    lines.extend([
        "",
        "## runtime + resources + binary size",
        f"{'impl':<22} {'bench':<14} {'best_ms':>8} {'med_ms':>8} {'rss_mib':>8} {'cpu_ms':>8} {'bytes':>10}  stdout",
    ])
    for i, name in enumerate(benches, start=1):
        if name == fail_xu_bench:
            rec_xu = {
                "impl": "Xu",
                "bench": name,
                "status": "compile_failed",
                "error": "synthetic failure",
            }
            lines.append("# result: " + json.dumps(rec_xu))
            lines.append(f"{'Xu':<22} {name:<14} {'FAIL':>8} {'':>8} {'':>8} {'':>8} {'':>10}  compile")
        else:
            med = round(1.0 + i * 0.1, 2)
            rec_xu = {
                "impl": "Xu",
                "bench": name,
                "status": "ok",
                "wall_ms": med,
                "best_ms": round(med * 0.9, 2),
                "rss_mib": 1.25,
                "cpu_ms": round(med * 0.8, 2),
                "bytes": 16384,
            }
            lines.append("# result: " + json.dumps(rec_xu))
            lines.append(
                f"{'Xu':<22} {name:<14} {rec_xu['best_ms']:8.1f} {med:8.1f} {1.25:8.2f} {rec_xu['cpu_ms']:8.1f} {16384:10d}  OK"
            )
        rec_c = {
            "impl": "clang -O3",
            "bench": name,
            "status": "ok",
            "wall_ms": 1.5,
            "best_ms": 1.4,
            "rss_mib": 1.1,
            "cpu_ms": 1.0,
            "bytes": 12288,
        }
        lines.append("# result: " + json.dumps(rec_c))
        lines.append(
            f"{'clang -O3':<22} {name:<14} {1.4:8.1f} {1.5:8.1f} {1.10:8.2f} {1.0:8.1f} {12288:10d}  OK"
        )
    lines.extend([
        "",
        "## compile (already-built compilers, best-of-5)",
        f"{'impl':<22} {'bench':<14} {'best_ms':>8}",
    ])
    for name in benches:
        lines.append(f"{'Xu':<22} {name:<14} {12.3:8.1f}")
    lines.extend([
        "",
        "## binary size (on-disk, not stripped)",
        f"{'impl':<22} {'bench':<14} {'bytes':>10} {'KiB':>8} {'vs Xu':>8}",
    ])
    for name in benches:
        if name != fail_xu_bench:
            lines.append(f"{'Xu':<22} {name:<14} {16384:10d} {16.0:8.1f} {'1.00×':>8}")
    lines.append(f"\n# wrote shard_{shard_idx}.txt")
    return "\n".join(lines) + "\n"


class TestShardPartitioning(unittest.TestCase):
    def test_parse_shard_validation(self) -> None:
        self.assertEqual(suite.parse_shard("1/1"), (1, 1))
        self.assertEqual(suite.parse_shard(" 2 / 4 "), (2, 4))
        for bad in ("0/4", "5/4", "1/0", "-1/3", "abc", "1/2/3", ""):
            with self.assertRaises(ValueError, msg=bad):
                suite.parse_shard(bad)

    def test_partition_covers_registry_with_order_and_balance(self) -> None:
        canonical = [b.name for b in suite.BENCHES]
        pos = {name: i for i, name in enumerate(canonical)}
        heavy_aes = {
            "aes128_encrypt", "aes128_decrypt",
            "aes192_encrypt", "aes192_decrypt",
            "aes256_encrypt", "aes256_decrypt",
        }

        for total in (1, 2, 3, 4):
            buckets = suite.partition_shards(list(suite.BENCHES), total)
            self.assertEqual(len(buckets), total)
            merged_names = [b.name for bucket in buckets for b in bucket]
            self.assertEqual(len(merged_names), len(canonical))
            self.assertEqual(set(merged_names), set(canonical))
            for idx, bucket in enumerate(buckets, start=1):
                self.assertTrue(bucket, f"empty bucket {idx}/{total}")
                self.assertEqual(
                    bucket,
                    suite.select_shard(list(suite.BENCHES), idx, total),
                )
                # Canonical relative order is preserved inside each bucket.
                indices = [pos[b.name] for b in bucket]
                self.assertEqual(indices, sorted(indices))
            if total >= 2:
                loads = [sum(suite.bench_shard_weight(b) for b in bucket) for bucket in buckets]
                self.assertLessEqual(max(loads) - min(loads), 8, f"unbalanced loads for N={total}: {loads}")
            if total >= 3:
                for bucket in buckets:
                    aes_count = sum(1 for b in bucket if b.name in heavy_aes)
                    self.assertLessEqual(aes_count, 3)


class TestMatrixPlanner(unittest.TestCase):
    def test_full_auto_respects_github_runner_concurrency_caps(self) -> None:
        plan = summary.plan_ci_matrix(mode="full", benches="", shards="auto")
        self.assertTrue(plan["expect_full_registry"])
        self.assertEqual(len(plan["build_matrix"]["include"]), 6)
        self.assertEqual(len(plan["bench_matrix"]["include"]), 20)
        self.assertEqual(
            plan["platform_shards"],
            {
                "linux-arm64": 3,
                "linux-x64": 4,
                "macos-arm64": 2,
                "macos-x64": 3,
                "windows-x64": 4,
                "windows-arm64": 4,
            },
        )
        macos_jobs = [
            e for e in plan["bench_matrix"]["include"]
            if e["platform_id"].startswith("macos-")
        ]
        self.assertEqual(len(macos_jobs), 5)

    def test_quick_custom_benches_and_manual_unsharded_fallback(self) -> None:
        quick = summary.plan_ci_matrix(mode="quick", benches="", shards="auto", macos_arm64_image="macos-15")
        self.assertFalse(quick["expect_full_registry"])
        self.assertEqual(len(quick["bench_matrix"]["include"]), 6)
        self.assertTrue(all(v == 1 for v in quick["platform_shards"].values()))
        mac_build = next(e for e in quick["build_matrix"]["include"] if e["platform_id"] == "macos-arm64")
        self.assertEqual(mac_build["os"], "macos-15")

        custom = summary.plan_ci_matrix(mode="full", benches="fib,matmul", shards="auto")
        self.assertFalse(custom["expect_full_registry"])
        self.assertEqual(len(custom["bench_matrix"]["include"]), 6)

        manual_one = summary.plan_ci_matrix(mode="full", benches="", shards="1")
        self.assertTrue(manual_one["expect_full_registry"])
        self.assertEqual(len(manual_one["bench_matrix"]["include"]), 6)


class TestShardMergeAndImportCompatibility(unittest.TestCase):
    def test_merge_full_registry_across_six_platforms_and_import_contract(self) -> None:
        plan = summary.plan_ci_matrix(mode="full", benches="", shards="auto")
        canonical = [b.name for b in suite.BENCHES]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shards_root = root / "all-shards"
            out_root = root / "all-reports"

            for pid, total in plan["platform_shards"].items():
                buckets = suite.partition_shards(list(suite.BENCHES), total)
                identity = _make_identity(pid)
                rss = "linux-post-exec-vmhwm-v1" if pid.startswith("linux-") else "wait4"
                for idx, bucket in enumerate(buckets, start=1):
                    sdir = shards_root / f"benchmark-shard-{pid}-{idx}-of-{total}"
                    sdir.mkdir(parents=True, exist_ok=True)
                    (sdir / "compiler-identity.json").write_text(
                        json.dumps(identity, indent=2) + "\n", encoding="utf-8"
                    )
                    (sdir / "crosslang.txt").write_text(
                        _make_shard_report([b.name for b in bucket], idx, total, rss_method=rss),
                        encoding="utf-8",
                    )

            merged = summary.merge_all_platform_shards(
                shards_root,
                out_root,
                platform_shards=plan["platform_shards"],
                expect_full_registry=True,
            )
            self.assertEqual(set(merged), set(plan["platform_shards"]))
            for pid, payload in merged.items():
                self.assertEqual(payload["metadata"]["total_benches"], len(canonical))
                self.assertEqual([b["name"] for b in payload["benches"]], canonical)
                pdir = out_root / f"benchmark-reports-{pid}"
                for fname in ("crosslang.txt", f"benchmarks-{pid}.json", "github_summary.md", "compiler-identity.json"):
                    self.assertTrue((pdir / fname).is_file(), f"missing {fname} for {pid}")

            # Verify compatibility with xulang-org/scripts/import-benchmarks.py if sibling repo is checked out.
            site_scripts = ROOT.parent / "xulang-org" / "scripts"
            if (site_scripts / "import-benchmarks.py").is_file():
                import importlib.util
                sys.path.insert(0, str(site_scripts))
                spec = importlib.util.spec_from_file_location("import_benchmarks", site_scripts / "import-benchmarks.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                with patch.object(mod, "require_bench_commit", return_value=None):
                    imported = mod.load(out_root, "0.14.1", "a" * 40, "12345678", "2026-11-26", bench_root=ROOT)
                self.assertEqual(imported["metadata"]["total_benches"], len(canonical))
                self.assertEqual(len(imported["platforms"]), 6)

    def test_merge_preserves_failure_records_and_rejects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pid = "linux-x64"
            buckets = suite.partition_shards(list(suite.BENCHES), 3)

            def write_shards(
                *,
                bad_sha_idx: int | None = None,
                bad_tc_idx: int | None = None,
                bad_rss_idx: int | None = None,
                skip_idx: int | None = None,
                dup_name: str | None = None,
                fail_bench: str | None = None,
            ) -> list[Path]:
                dirs = []
                for idx, bucket in enumerate(buckets, start=1):
                    if idx == skip_idx:
                        continue
                    sdir = root / f"case_{idx}"
                    sdir.mkdir(parents=True, exist_ok=True)
                    ident = _make_identity(pid)
                    if idx == bad_sha_idx:
                        ident["compiler_sha256"] = "f" * 64
                    (sdir / "compiler-identity.json").write_text(json.dumps(ident), encoding="utf-8")
                    tc = None
                    if idx == bad_tc_idx:
                        tc = {"clang": "clang 17.0", "rustc": "rustc 1.84.0", "go": "go1.23.4", "swiftc": "Swift 6.0"}
                    rss = "bad-rss" if idx == bad_rss_idx else "linux-post-exec-vmhwm-v1"
                    names = [b.name for b in bucket]
                    if idx == 2 and dup_name and dup_name not in names:
                        names.append(dup_name)
                    (sdir / "crosslang.txt").write_text(
                        _make_shard_report(names, idx, 3, toolchains=tc, rss_method=rss, fail_xu_bench=fail_bench),
                        encoding="utf-8",
                    )
                    dirs.append(sdir)
                return dirs

            # Passing failure-preservation case
            ok_dirs = write_shards(fail_bench=buckets[0][0].name)
            payload = summary.merge_platform_shards(
                ok_dirs, root / "out_fail", platform_id=pid, expected_shard_total=3, expect_full_registry=True
            )
            self.assertEqual(payload["metadata"]["xu_failed_benches"], 1)
            row = next(b for b in payload["benches"] if b["name"] == buckets[0][0].name)
            self.assertEqual(row["xu_status"], "compile_failed")
            self.assertIsNone(row["xu_wall_ms"])

            # Rejection cases
            with self.assertRaisesRegex(ValueError, "compiler-identity mismatch"):
                summary.merge_platform_shards(write_shards(bad_sha_idx=2), root / "o1", platform_id=pid)
            with self.assertRaisesRegex(ValueError, "toolchain"):
                summary.merge_platform_shards(write_shards(bad_tc_idx=3), root / "o2", platform_id=pid)
            with self.assertRaisesRegex(ValueError, "rss_method"):
                summary.merge_platform_shards(write_shards(bad_rss_idx=2), root / "o3", platform_id=pid)
            with self.assertRaisesRegex(ValueError, "missing shards"):
                summary.merge_platform_shards(write_shards(skip_idx=2), root / "o4", platform_id=pid, expected_shard_total=3)
            with self.assertRaisesRegex(ValueError, "duplicate benchmark"):
                summary.merge_platform_shards(write_shards(dup_name=buckets[0][0].name), root / "o5", platform_id=pid)

    def test_merge_accepts_patch_rollout_and_rejects_minor_drift(self) -> None:
        plan = summary.plan_ci_matrix(mode="full", benches="", shards="auto")
        canonical = [b.name for b in suite.BENCHES]
        tc_base = {
            "clang": "Ubuntu clang version 21.1.8 (6ubuntu1)",
            "rustc": "rustc 1.100.1 (20ddd0171 2026-11-25)",
            "go": "go version go1.27.4 linux/amd64",
            "swiftc": "Swift version 6.4.2 (swift-6.4.2-RELEASE)",
        }
        tc_patch = {
            **tc_base,
            "swiftc": "Swift version 6.4.3 (swift-6.4.3-RELEASE)",
        }
        tc_minor = {
            **tc_base,
            "swiftc": "Swift version 6.3.1 (swift-6.3.1-RELEASE)",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shards_root = root / "all-shards"
            out_root = root / "all-reports"

            for pid, total in plan["platform_shards"].items():
                buckets = suite.partition_shards(list(suite.BENCHES), total)
                identity = _make_identity(pid)
                rss = "linux-post-exec-vmhwm-v1" if pid.startswith("linux-") else "wait4"
                for idx, bucket in enumerate(buckets, start=1):
                    sdir = shards_root / f"benchmark-shard-{pid}-{idx}-of-{total}"
                    sdir.mkdir(parents=True, exist_ok=True)
                    (sdir / "compiler-identity.json").write_text(
                        json.dumps(identity, indent=2) + "\n", encoding="utf-8"
                    )
                    tc = tc_patch if (pid == "linux-x64" and idx == 2) else tc_base
                    (sdir / "crosslang.txt").write_text(
                        _make_shard_report([b.name for b in bucket], idx, total, toolchains=tc, rss_method=rss),
                        encoding="utf-8",
                    )

            merged = summary.merge_all_platform_shards(
                shards_root,
                out_root,
                platform_shards=plan["platform_shards"],
                expect_full_registry=True,
            )
            expected_swift = "Swift version 6.4.2 (swift-6.4.2-RELEASE) / Swift version 6.4.3 (swift-6.4.3-RELEASE)"
            self.assertEqual(merged["linux-x64"]["metadata"]["toolchains"]["swiftc"], expected_swift)
            merged_txt = (out_root / "benchmark-reports-linux-x64" / "crosslang.txt").read_text(encoding="utf-8")
            self.assertIn(f"# swiftc: {expected_swift}", merged_txt)

            site_scripts = ROOT.parent / "xulang-org" / "scripts"
            if (site_scripts / "import-benchmarks.py").is_file():
                import importlib.util
                sys.path.insert(0, str(site_scripts))
                spec = importlib.util.spec_from_file_location("import_benchmarks", site_scripts / "import-benchmarks.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                with patch.object(mod, "require_bench_commit", return_value=None):
                    imported = mod.load(out_root, "0.14.1", "a" * 40, "12345678", "2026-11-27", bench_root=ROOT)
                self.assertEqual(imported["platforms"]["linux-x64"]["toolchains"]["swiftc"], expected_swift)
                self.assertEqual(imported["metadata"]["total_benches"], len(canonical))

            # Minor version drift must still fail closed.
            bad_dirs = []
            buckets = suite.partition_shards(list(suite.BENCHES), 2)
            for idx, bucket in enumerate(buckets, start=1):
                sdir = root / f"minor_{idx}"
                sdir.mkdir(parents=True, exist_ok=True)
                (sdir / "compiler-identity.json").write_text(json.dumps(_make_identity("linux-x64")), encoding="utf-8")
                tc = tc_minor if idx == 2 else tc_base
                (sdir / "crosslang.txt").write_text(
                    _make_shard_report([b.name for b in bucket], idx, 2, toolchains=tc),
                    encoding="utf-8",
                )
                bad_dirs.append(sdir)
            with self.assertRaisesRegex(ValueError, "toolchain"):
                summary.merge_platform_shards(bad_dirs, root / "minor_out", platform_id="linux-x64")

    def test_workflow_yml_structure(self) -> None:
        wf = (ROOT / ".github" / "workflows" / "bench.yml").read_text(encoding="utf-8")
        for needle in (
            "resolve-xu:",
            "build-xu:",
            "benchmark:",
            "aggregate:",
            "--plan-ci-matrix",
            "--shard",
            "--merge-shards-root",
            'chmod +x "$XU_BIN"',
            "xu-compiler-${{ matrix.platform_id }}",
            "benchmark-shard-${{ matrix.platform_id }}-${{ matrix.shard }}-of-${{ matrix.shard_total }}",
        ):
            self.assertIn(needle, wf)
        for spec in summary.PLATFORM_SPECS:
            self.assertIn(f"benchmark-reports-{spec['platform_id']}", wf)
        # Ensure YAML parses cleanly if PyYAML is available in the environment.
        try:
            import yaml  # type: ignore
        except ImportError:
            yaml = None
        if yaml is not None:
            doc = yaml.safe_load(wf)
            self.assertEqual(list(doc["jobs"].keys()), ["resolve-xu", "build-xu", "benchmark", "aggregate"])


if __name__ == "__main__":
    unittest.main()
