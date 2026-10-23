"""Benchmarks use the shared hosted compiler policy."""
import importlib
import os
import subprocess
import sys
from pathlib import Path
import pytest

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH / 'scripts'))


@pytest.mark.parametrize('name,resolver', [
    ('bench_crosslang', 'resolve_product_compiler'),
    ('bench_game', 'resolve_product_xu'),
    ('bench_stdlib', 'resolve_product_xu'),
    ('bench_opt_levels', 'resolve_product_xu'),
])
def test_product_resolution_delegates_to_shared_policy(monkeypatch, name, resolver):
    module = importlib.import_module(name)
    calls = []
    expected = Path('/tmp/hosted-compiler')
    def resolve(explicit):
        calls.append(explicit)
        return expected
    monkeypatch.setattr(module, 'resolve_hosted_compiler', resolve)
    assert getattr(module, resolver)('/tmp/requested') == expected
    assert calls == ['/tmp/requested']


@pytest.mark.parametrize('name', ['bench_stdlib', 'bench_opt_levels'])
def test_retired_lane_is_rejected(name):
    module = importlib.import_module(name)
    with pytest.raises(ValueError, match='unsupported compiler lane'):
        module.resolve_compiler(None, 'oracle')


def test_shared_policy_accepts_windows_suffix_and_rejects_directories(tmp_path, monkeypatch):
    module = importlib.import_module('product_compiler')
    root = tmp_path / 'xu'
    (root / 'scripts').mkdir(parents=True)
    core = Path(os.environ['XU_ROOT'])
    import shutil
    shutil.copy2(core / 'scripts/xu_host_seed.sh', root / 'scripts/xu_host_seed.sh')
    compiler = tmp_path / 'compiler.exe'
    compiler.write_text('#!/bin/sh\nexit 0\n')
    compiler.chmod(0o755)
    monkeypatch.setattr(module, 'ROOT', root)
    assert module.resolve_product_compiler(str(compiler)[:-4]) == compiler
    with pytest.raises(SystemExit):
        module.resolve_product_compiler(root)
