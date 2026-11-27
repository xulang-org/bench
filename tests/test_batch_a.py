"""Independent goldens and registry contract checks for Batch A benchmarks."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bench_clang_gap_reference as clang_gap_ref  # noqa: E402
import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402

BATCH_A = (
    "avl_tree",
    "chacha20_stream",
    "huffman_coding",
    "json_tokenizer",
    "lzw_codec",
)
GOLDEN = ROOT / "tests" / "bench" / "golden"


def _lzw_lsb8_encode(src: bytes) -> bytes:
    """Independent pure-Python LSB 8-bit LZW encoder aligned with Go/Xu."""
    clear = 256
    eof = 257
    max_code = 4095
    width = 9
    hi = eof
    overflow = 1 << width
    bits = 0
    nbits = 0
    out = bytearray()
    table: dict[tuple[int, int], int] = {}

    def emit(code: int) -> None:
        nonlocal bits, nbits
        bits |= code << nbits
        nbits += width
        while nbits >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            nbits -= 8

    if not src:
        emit(clear)
        emit(eof)
        if nbits > 0:
            out.append(bits & 0xFF)
        return bytes(out)

    emit(clear)
    saved = src[0]
    for lit in src[1:]:
        pair = (saved, lit)
        if pair in table:
            saved = table[pair]
            continue
        emit(saved)
        saved = lit
        hi += 1
        if hi == overflow:
            width += 1
            overflow <<= 1
        if hi == max_code:
            emit(clear)
            width = 9
            hi = eof
            overflow = clear * 2
            table.clear()
        else:
            table[pair] = hi

    emit(saved)
    hi += 1
    if hi == overflow:
        width += 1
        overflow <<= 1
    if hi == max_code:
        emit(clear)
        width = 9
    emit(eof)
    if nbits > 0:
        out.append(bits & 0xFF)
    return bytes(out)


def _lzw_lsb8_decode(src: bytes) -> bytes:
    """Independent pure-Python LSB 8-bit LZW decoder aligned with Go/Xu."""
    clear = 256
    eof = 257
    max_width = 12
    width = 9
    hi = eof
    overflow = 1 << width
    bits = 0
    nbits = 0
    pos = 0
    table: dict[int, bytes] = {i: bytes([i]) for i in range(clear)}
    last: bytes | None = None
    out = bytearray()

    while True:
        while nbits < width:
            bits |= src[pos] << nbits
            pos += 1
            nbits += 8
        code = bits & ((1 << width) - 1)
        bits >>= width
        nbits -= width

        if code == clear:
            width = 9
            hi = eof
            overflow = 1 << width
            table = {i: bytes([i]) for i in range(clear)}
            last = None
            continue
        if code == eof:
            break
        if code in table:
            entry = table[code]
        elif code == hi and last is not None:
            entry = last + last[:1]
        else:
            raise ValueError(f"invalid LZW code: {code}")
        out.extend(entry)
        if last is not None:
            table[hi] = last + entry[:1]
        last = entry
        hi += 1
        if hi >= overflow:
            if width == max_width:
                last = None
                hi -= 1
            else:
                width += 1
                overflow <<= 1
    return bytes(out)


class BatchATests(unittest.TestCase):
    def test_batch_a_registry_ports_and_descriptions(self):
        for name in BATCH_A:
            with self.subTest(bench=name):
                self.assertIn(name, suite.BY_NAME)
                bench = suite.BY_NAME[name]
                self.assertEqual(bench.langs, suite.CORE)
                xu_path = suite.xu_src(name)
                self.assertTrue(xu_path.is_file(), xu_path)
                self.assertEqual(xu_path.read_text(encoding="utf-8").splitlines()[0], "@main")
                for ext in suite.CORE:
                    peer = suite.cross_src(name, ext)
                    self.assertTrue(peer.is_file(), peer)
                self.assertIn(name, summary.BENCH_DESCRIPTIONS)
                _zh, _en, cat = summary.BENCH_DESCRIPTIONS[name]
                self.assertIn(cat, summary.CATEGORY_NAMES)

    def test_clang_gap_four_independent_goldens(self):
        for name in ("avl_tree", "chacha20_stream", "huffman_coding", "json_tokenizer"):
            with self.subTest(bench=name):
                expected = clang_gap_ref.REFERENCES[name]()
                self.assertEqual(suite.BY_NAME[name].expect, expected)
                self.assertEqual((GOLDEN / f"{name}.txt").read_text(encoding="utf-8"), expected)

    def test_lzw_codec_independent_golden(self):
        payload = b"TOBEORNOTTOBEORTOBEORNOT#" * 16
        self.assertEqual(len(payload), 400)
        enc = _lzw_lsb8_encode(payload)
        dec = _lzw_lsb8_decode(enc)
        self.assertEqual(dec, payload)
        self.assertEqual(len(enc), 106)
        total = 2500 * (len(enc) + len(dec)) + dec[0] + dec[-1]
        expected = f"{total}\n"
        self.assertEqual(expected, "1265119\n")
        self.assertEqual(suite.BY_NAME["lzw_codec"].expect, expected)
        self.assertEqual((GOLDEN / "lzw_codec.txt").read_text(encoding="utf-8"), expected)

    def test_benches_ast_contract(self):
        source = ROOT / "scripts" / "bench_crosslang.py"
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        values = []
        for node in tree.body:
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
                if isinstance(node, ast.AnnAssign)
                else []
            )
            if any(isinstance(t, ast.Name) and t.id == "BENCHES" for t in targets):
                values.append(node.value)
        self.assertEqual(len(values), 1)
        self.assertIsInstance(values[0], (ast.List, ast.Tuple))
        names = []
        for item in values[0].elts:
            self.assertIsInstance(item, ast.Call)
            self.assertIsInstance(item.func, ast.Name)
            self.assertEqual(item.func.id, "Bench")
            name = ast.literal_eval(item.args[0])
            self.assertRegex(name, r"^[a-z][a-z0-9_]*$")
            self.assertNotIn(name, names)
            names.append(name)
        self.assertGreaterEqual(len(names), 77)


if __name__ == "__main__":
    unittest.main()
