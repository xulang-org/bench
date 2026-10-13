#!/usr/bin/env python3
"""Independent semantic references for four extended Clang-gap microbenches.

Run with --check to compare against the committed golden files. This is not a
performance implementation and does not import or execute either language port.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/bench/golden"
MASK32 = (1 << 32) - 1


def lcg(seed: int) -> int:
    return (seed * 1103515245 + 12345) & 2147483647


def avl_tree() -> str:
    # A dictionary models the observable insert/replace/search contract;
    # balancing and node layout are intentionally absent from this oracle.
    items: dict[int, int] = {}
    seed = 123456789
    for i in range(80000):
        seed = lcg(seed)
        items[seed % 200000] = (i * 3 + 7) & 2147483647
    checksum = 0
    for _ in range(300000):
        seed = lcg(seed)
        checksum = (checksum * 31 + items.get(seed % 200000, 0)) % 1000000007
    return f"{checksum}\n"


def chacha20_stream() -> str:
    def rotl(v: int, n: int) -> int:
        return ((v << n) | (v >> (32 - n))) & MASK32

    total = 0
    for block in range(30000):
        s = [1634760805, 857760878, 2036477234, 1797285236]
        s.extend(((i * 16843009) + block) & MASK32 for i in range(8))
        s.extend([block, 305419896, 2596069104, 267246505])

        def qr(a: int, b: int, c: int, d: int) -> None:
            s[a] = (s[a] + s[b]) & MASK32
            s[d] = rotl(s[d] ^ s[a], 16)
            s[c] = (s[c] + s[d]) & MASK32
            s[b] = rotl(s[b] ^ s[c], 12)
            s[a] = (s[a] + s[b]) & MASK32
            s[d] = rotl(s[d] ^ s[a], 8)
            s[c] = (s[c] + s[d]) & MASK32
            s[b] = rotl(s[b] ^ s[c], 7)

        for _ in range(10):
            for q in ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14),
                      (3, 7, 11, 15), (0, 5, 10, 15), (1, 6, 11, 12),
                      (2, 7, 8, 13), (3, 4, 9, 14)):
                qr(*q)
        total = (total + s[0] + s[5] + s[10] + s[15]) & MASK32
    return f"{total}\n"


def huffman_coding() -> str:
    # Any lossless prefix encoding followed by decoding must recover the
    # original symbols. This oracle computes the observable decoded checksum
    # directly from the generated sequence, independent of heap/code layout.
    seed = 123456789
    checksum = 0
    for _ in range(20000):
        seed = lcg(seed)
        symbol = __import__("math").isqrt(seed % 4096)
        checksum = (checksum * 33 + symbol) & 2147483647
    return f"{(checksum * 50) & 2147483647}\n"


def json_tokenizer() -> str:
    import json
    base = '{"project":"Xu","version":1.0,"active":true,"count":100,"flag":false,"note":null,"data":[1,2,-3,40]}'
    # Validate the fixture as JSON; the benchmark's checksum is over lexical
    # tokens, so use a small independent scanner with one token per scalar.
    json.loads(base)
    src = base * 10
    types = {'{': 1, '}': 2, '[': 3, ']': 4, ':': 5, ',': 6}
    chk = pos = 0
    while pos < len(src):
        ch = src[pos]
        if ch.isspace():
            pos += 1
            continue
        start = pos
        if ch in types:
            kind = types[ch]
            pos += 1
        elif ch == '"':
            kind = 7
            pos += 1
            while True:
                if src[pos] == '\\':
                    pos += 2
                elif src[pos] == '"':
                    pos += 1
                    break
                else:
                    pos += 1
        elif ch == '-' or ch.isdigit():
            kind = 8
            pos += 1
            while pos < len(src) and src[pos].isdigit():
                pos += 1
            if pos < len(src) and src[pos] == '.':
                pos += 1
                while pos < len(src) and src[pos].isdigit():
                    pos += 1
        else:
            literal = next(x for x in ('true', 'false', 'null') if src.startswith(x, pos))
            kind = {'true': 9, 'false': 10, 'null': 11}[literal]
            pos += len(literal)
        chk = (chk * 37 + kind * 101 + pos - start) % 1000000007
    total = 0
    for _ in range(1000):
        total = (total * 31 + chk) % 1000000007
    return f"{total}\n"


REFERENCES = {
    'avl_tree': avl_tree,
    'chacha20_stream': chacha20_stream,
    'huffman_coding': huffman_coding,
    'json_tokenizer': json_tokenizer,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, reference in REFERENCES.items():
        value = reference()
        if args.check:
            path = GOLDEN / f'{name}.txt'
            if not path.is_file() or path.read_text() != value:
                raise SystemExit(f'{name}: independent golden mismatch or missing')
            print(f'{name}: PASS {value.strip()}')
        else:
            print(f'{name}: {value.strip()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
