"""Verify report identity before appending measurements."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path


def metadata(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise SystemExit(f"missing benchmark snapshot: {path}")
    return dict(re.findall(r"^# ([a-z_0-9]+): (.*)$", path.read_text(), re.MULTILINE))


def compiler_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_identity(path: Path, lane: str, sha256: str, benches: str) -> None:
    saved = metadata(path)
    wanted = {"lane": lane, "xu_sha256": sha256,
              "benches": ", ".join(x.strip() for x in benches.split(","))}
    for key, value in wanted.items():
        actual = saved.get(key)
        if key == "benches" and actual:
            actual = ", ".join(x.strip() for x in actual.split(","))
        if actual != value:
            raise SystemExit(f"snapshot {key} differs: {actual!r} != {value!r}")
