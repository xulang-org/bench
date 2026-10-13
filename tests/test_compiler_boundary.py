"""Keep product/oracle selection anchored to the companion Xu checkout."""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.mark.parametrize("name,guard", [
    ("bench_game", "_is_frozen_primer"),
    ("bench_stdlib", "is_frozen_primer"),
    ("bench_opt_levels", "is_frozen_primer"),
    ("bench_opt_full", "is_frozen_primer"),
    ("opt_stage_bisect", "is_frozen_primer"),
])
def test_oracle_rejects_arbitrary_binaries_and_symlinks(tmp_path, monkeypatch, name, guard):
    module = importlib.import_module(name)
    compiler = tmp_path / "bootstrap/target/debug/xu"
    compiler.parent.mkdir(parents=True)
    compiler.write_text("#!/bin/sh\nexit 0\n")
    compiler.chmod(0o755)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "FROZEN_PRIMER_PATHS", frozenset({compiler.absolute()}))
    check = getattr(module, guard)
    assert check(compiler)
    assert not check(Path("/bin/echo"))
    alias = tmp_path / "alias"
    alias.symlink_to(compiler)
    assert not check(alias)
    compiler.unlink()
    compiler.symlink_to("/bin/echo")
    assert not check(compiler)


@pytest.mark.parametrize("name,classifier", [
    ("bench_crosslang", "_is_primer"),
    ("bench_game", "_is_primer"),
    ("bench_stdlib", "is_primer"),
    ("bench_opt_levels", "is_primer"),
])
def test_product_classifier_follows_bootstrap_alias(tmp_path, monkeypatch, name, classifier):
    module = importlib.import_module(name)
    bootstrap = tmp_path / "bootstrap"
    bootstrap.mkdir()
    compiler = bootstrap / "xu"
    compiler.write_text("primer")
    alias = tmp_path / "hosted-looking-xu"
    alias.symlink_to(compiler)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    assert getattr(module, classifier)(alias)


def test_stdlib_default_oracle_rejects_symlink(tmp_path, monkeypatch):
    module = importlib.import_module("bench_stdlib")
    candidate = tmp_path / "bootstrap/target/debug/xu"
    candidate.parent.mkdir(parents=True)
    candidate.symlink_to("/bin/echo")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BOOT_XU", candidate)
    monkeypatch.setattr(module, "FROZEN_PRIMER_PATHS", frozenset({candidate.absolute()}))
    with pytest.raises(SystemExit):
        module.resolve_compiler(None, "oracle")


def test_product_resolution_retains_symlink_provenance(tmp_path, monkeypatch):
    module = importlib.import_module("bench_stdlib")
    candidate = tmp_path / "bootstrap/target/debug/xu"
    candidate.parent.mkdir(parents=True)
    candidate.symlink_to("/bin/echo")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PRODUCT_RUNNER", Path("/bin/echo"))
    with pytest.raises(SystemExit):
        module.resolve_compiler(str(candidate), "product")
