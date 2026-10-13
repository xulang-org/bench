"""Keep benchmark appendices bound to the compiler and workload in their report."""

from __future__ import annotations

import hashlib

import pytest

from scripts import bench_opt_full, bench_opt_levels


def test_oracle_timings_require_matching_snapshot(tmp_path) -> None:
    primer = tmp_path / "xu"
    primer.write_bytes(b"primer fixture")
    digest = hashlib.sha256(primer.read_bytes()).hexdigest()
    report = tmp_path / "report.txt"
    report.write_text(
        f"# lane: oracle\n# xu_sha256: {digest}\n# benches: loop_sum\n"
    )

    assert [bench.name for bench in bench_opt_full.snapshot_benches(report, primer)] == [
        "loop_sum"
    ]

    report.write_text(
        f"# lane: product\n# xu_sha256: {digest}\n# benches: loop_sum\n"
    )
    with pytest.raises(SystemExit, match="oracle snapshot"):
        bench_opt_full.snapshot_benches(report, primer)

    report.write_text(
        "# lane: oracle\n# xu_sha256: different\n# benches: loop_sum\n"
    )
    with pytest.raises(SystemExit, match="SHA differs"):
        bench_opt_full.snapshot_benches(report, primer)


def test_compile_appendix_rejects_mixed_identity_without_writing(tmp_path) -> None:
    report = tmp_path / "report.txt"
    original = (
        "# lane: product\n# xu_sha256: abc\n# benches: loop_sum\n"
        "## runtime + resources + binary size\nlocked runtime result\n"
    )
    report.write_text(original)
    block = "## compile wall median ms (already-built compiler)\nnew compile result\n"

    with pytest.raises(SystemExit, match="snapshot xu_sha256"):
        bench_opt_levels.splice_compile_section(report, block, "product", "def", "loop_sum")
    assert report.read_text() == original

    bench_opt_levels.splice_compile_section(report, block, "product", "abc", "loop_sum")
    assert "locked runtime result" in report.read_text()
    assert "new compile result" in report.read_text()
