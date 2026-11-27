"""Independent goldens and registry contract checks for Batch E (Storage/Databases/Search) benchmarks."""
from __future__ import annotations

import ast
import bisect
from pathlib import Path
import re
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402

GOLDEN = ROOT / "tests" / "bench" / "golden"
MOD = 1_000_000_007

BATCH_E_NAMES = (
    "btree_index",
    "lsm_compaction",
    "bm25_search",
    "sql_query_exec",
    "consistent_hash",
    "wal_log_recovery",
)


class TestBatchERegistryAndGoldens(unittest.TestCase):
    def test_registry_and_files(self) -> None:
        source = (ROOT / "scripts" / "bench_crosslang.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        benches_node = None
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "BENCHES":
                benches_node = node.value
                break
        self.assertIsNotNone(benches_node)
        ast_names = [elt.args[0].value for elt in benches_node.elts]
        self.assertGreaterEqual(len(ast_names), 107)
        self.assertEqual(len(set(ast_names)), len(ast_names))
        name_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in ast_names:
            self.assertRegex(name, name_re)

        self.assertIn("storage", summary.CATEGORY_NAMES)
        for name in BATCH_E_NAMES:
            self.assertIn(name, suite.BY_NAME)
            self.assertEqual(suite.BY_NAME[name].langs, suite.CORE)
            self.assertIn(name, summary.BENCH_DESCRIPTIONS)
            self.assertEqual(summary.BENCH_DESCRIPTIONS[name][2], "storage")
            golden_bytes = (GOLDEN / f"{name}.txt").read_bytes()
            self.assertNotIn(b"\r", golden_bytes)
            self.assertEqual(golden_bytes.decode("ascii"), suite.BY_NAME[name].expect)
            self.assertTrue((ROOT / "tests" / "bench" / f"{name}.xu").is_file())
            for ext in suite.CORE:
                self.assertTrue((ROOT / "tests" / "bench" / "cross" / f"{name}.{ext}").is_file())

    def test_btree_index_oracle(self) -> None:
        rng = 123456789
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        kv: dict[int, int] = {}
        for i in range(80000):
            k = nxt() % 1000000
            v = (i * 17 + (nxt() & 1023)) % 1000000
            kv[k] = v

        hits, ck = 0, 0
        for _ in range(120000):
            k = nxt() % 1000000
            v = kv.get(k, -1)
            if v >= 0:
                hits += 1
                ck = (ck * 31 + v) % MOD

        sorted_keys = sorted(kv)
        rcnt = 0
        for _ in range(2000):
            lo_k = nxt() % 999000
            hi_k = lo_k + 1000
            li = bisect.bisect_left(sorted_keys, lo_k)
            ri = bisect.bisect_right(sorted_keys, hi_k)
            cnt = ri - li
            s = sum(kv[sorted_keys[p]] for p in range(li, ri)) % MOD
            rcnt += cnt
            ck = (ck * 37 + s + cnt) % MOD

        expected = f"{hits + rcnt}\n{ck}\n"
        self.assertEqual(expected, "156642\n923128089\n")
        self.assertEqual(suite.BY_NAME["btree_index"].expect, expected)

    def test_lsm_compaction_oracle(self) -> None:
        rng = 555123456
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        state: dict[int, int] = {}
        hits, ck = 0, 0
        for _ in range(4):
            for _rn in range(8):
                for _j in range(12000):
                    k = nxt() % 40000
                    tomb = 1 if (nxt() % 10) == 0 else 0
                    if tomb == 1:
                        state.pop(k, None)
                    else:
                        state[k] = 1 + (nxt() % 100000)
            ck = (ck * 37 + len(state)) % MOD
            for _ in range(60000):
                q = nxt() % 40000
                v = state.get(q, -1)
                if v >= 0:
                    hits += 1
                    ck = (ck * 31 + v) % MOD

        expected = f"{hits}\n{ck}\n"
        self.assertEqual(expected, "210492\n473464819\n")
        self.assertEqual(suite.BY_NAME["lsm_compaction"].expect, expected)

    def test_bm25_search_oracle(self) -> None:
        rng = 777654321
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        n_docs, vocab = 6000, 2048
        lut = (0, 87, 170, 248, 322, 392, 459, 524, 585, 644, 700, 755, 807, 858, 907, 954)
        def ilog2_x1000(x: int) -> int:
            b = x.bit_length() - 1
            frac = ((x - (1 << b)) << 4) >> b
            return b * 1000 + lut[frac]

        postings: list[list[tuple[int, int]]] = [[] for _ in range(vocab)]
        doc_len = [0] * n_docs
        for d in range(n_docs):
            dl = 24 + (nxt() % 32)
            doc_len[d] = dl
            counts: dict[int, int] = {}
            for _ in range(dl):
                term = (nxt() % 64) if (nxt() % 3) == 0 else (64 + (nxt() % (vocab - 64)))
                counts[term] = counts.get(term, 0) + 1
            for term, tf in counts.items():
                postings[term].append((d, tf))

        idf = [
            ilog2_x1000((((n_docs - len(plist)) * 2 + 1) * 1024) // (len(plist) * 2 + 1) + 1024) - 10000
            if plist else 0
            for plist in postings
        ]
        avgdl_x100 = (sum(doc_len) * 100) // n_docs
        dl_norm = [250 + (750 * dl * 100) // avgdl_x100 for dl in doc_len]

        total_hits, ck = 0, 0
        for _ in range(2000):
            qn = 3 + (nxt() % 3)
            qterms = [nxt() % 64] + [64 + (nxt() % (vocab - 64)) for _ in range(1, qn)]
            acc: dict[int, int] = {}
            for term in qterms:
                it = idf[term]
                if it <= 0:
                    continue
                for d, tf in postings[term]:
                    sc = (it * tf * 2200) // (tf * 1000 + (12 * dl_norm[d]) // 10)
                    acc[d] = acc.get(d, 0) + sc
            top = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
            total_hits += len(top)
            for d, s in top:
                ck = (ck * 31 + d * 10007 + s) % MOD

        expected = f"{total_hits}\n{ck}\n"
        self.assertEqual(expected, "20000\n285545384\n")
        self.assertEqual(suite.BY_NAME["bm25_search"].expect, expected)

    def test_sql_query_exec_oracle(self) -> None:
        rng = 42424242
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        n_cust, n_ord = 8192, 200000
        cust_ids = []
        cust_map: dict[int, tuple[int, int]] = {}
        for i in range(n_cust):
            cid = 100000 + i * 7 + (nxt() % 5)
            reg = nxt() % 16
            tier = nxt() % 4
            cust_ids.append(cid)
            cust_map[cid] = (reg, tier)

        orders = []
        for _ in range(n_ord):
            cid = cust_ids[nxt() % n_cust] if (nxt() % 20) < 17 else (9000000 + (nxt() % 50000))
            cat = nxt() % 32
            amt = 100 + (nxt() % 2000)
            st = 1 if (nxt() % 5) != 0 else 0
            if st == 1 and cid in cust_map and cust_map[cid][1] != 0:
                reg, tier = cust_map[cid]
                orders.append((amt, reg * 32 + cat, tier))

        total_rows, ck = 0, 0
        for rnd in range(16):
            min_amt = 350 + rnd * 50
            grp_cnt: dict[int, int] = {}
            grp_rev: dict[int, int] = {}
            for amt, gb, tier in orders:
                if amt >= min_amt:
                    grp_cnt[gb] = grp_cnt.get(gb, 0) + 1
                    grp_rev[gb] = grp_rev.get(gb, 0) + amt * tier
                    total_rows += 1
            for gb in sorted(grp_cnt, key=lambda b: (-grp_rev[b], b)):
                row = (gb * 1000003 + grp_cnt[gb] * 97 + (grp_rev[gb] % MOD)) % MOD
                ck = (ck * 31 + row) % MOD

        expected = f"{total_rows}\n{ck}\n"
        self.assertEqual(expected, "1053790\n365717875\n")
        self.assertEqual(suite.BY_NAME["sql_query_exec"].expect, expected)

    def test_consistent_hash_oracle(self) -> None:
        def mix32(x: int) -> int:
            h = x & 0xFFFFFFFF
            h ^= h >> 16
            h = (h * 0x45D9F3B) & 0xFFFFFFFF
            h ^= h >> 16
            h = (h * 0x45D9F3B) & 0xFFFFFFFF
            return h ^ (h >> 16)

        max_nodes, vnodes, n_keys = 48, 128, 150000
        alive = {nid for nid in range(32)}
        node_load = [0] * max_nodes

        def build_sorted_ring():
            pairs = sorted(
                (mix32(((nid << 10) | v) ^ 0x9E3779B9), nid)
                for nid in sorted(alive)
                for v in range(vnodes)
            )
            return [t for t, _ in pairs], [n for _, n in pairs]

        rtok, rnode = build_sorted_ring()
        key_tok = [mix32((i * 2654435761 + 12345) & 0xFFFFFFFF) for i in range(n_keys)]

        def route(tok: int) -> int:
            pos = bisect.bisect_left(rtok, tok)
            return rnode[0 if pos == len(rtok) else pos]

        ck = 0
        for p in range(4):
            salt = p * 7919
            for kt in key_tok:
                owner = route(mix32((kt + salt) & 0xFFFFFFFF))
                node_load[owner] += 1
                ck = (ck * 31 + owner + 1) % MOD

        prev_owner = [route(kt) for kt in key_tok]
        total_moved = 0
        ops = [
            (alive.update, (32, 33, 34, 35)),
            (alive.difference_update, (5, 19)),
            (alive.update, (36, 37, 38, 39, 40, 41)),
            (alive.difference_update, (2, 11, 24, 33)),
        ]
        for fn, ids in ops:
            fn(ids)
            rtok, rnode = build_sorted_ring()
            moved = 0
            for i, kt in enumerate(key_tok):
                o = route(kt)
                if o != prev_owner[i]:
                    moved += 1
                    prev_owner[i] = o
                ck = (ck * 31 + o + 1) % MOD
            total_moved += moved
            ck = (ck * 37 + moved) % MOD

        for nl in node_load:
            ck = (ck * 31 + nl) % MOD

        expected = f"{total_moved}\n{ck}\n"
        self.assertEqual(expected, "61873\n601893444\n")
        self.assertEqual(suite.BY_NAME["consistent_hash"].expect, expected)

    def test_wal_log_recovery_oracle(self) -> None:
        rng = 999888777
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        kv: dict[int, int] = {}
        lsn, replayed, ck = 1, 0, 0
        for seg in range(40):
            buf = bytearray()
            for _ in range(3000):
                op = 2 if (nxt() % 6) == 0 else 1
                key = nxt() % 4096
                vlen = 0 if op == 2 else (8 + (nxt() % 32))
                seed = (nxt() >> 4) & 255
                hdr = bytes((0x57, 0x4C, op, (lsn ^ key) & 255))
                body = (
                    lsn.to_bytes(4, "little")
                    + key.to_bytes(4, "little")
                    + vlen.to_bytes(2, "little")
                    + bytes((seed + j * 13 + lsn) & 255 for j in range(vlen))
                )
                frame_wo_crc = hdr + body
                crc = zlib.crc32(frame_wo_crc) & 0xFFFFFFFF
                buf.extend(frame_wo_crc)
                buf.extend(crc.to_bytes(4, "little"))
                lsn += 1

            raw = bytes(buf[:-7] if (seg % 4) == 3 else (buf[:-2] + bytes((buf[-2] ^ 1,)) + buf[-1:] if (seg % 5) == 4 else buf))
            pos, seg_rep, early = 0, 0, 0
            while pos < len(raw):
                if pos + 18 > len(raw) or raw[pos:pos + 2] != b"WL" or raw[pos + 2] not in (1, 2):
                    early = 1
                    break
                vlen = int.from_bytes(raw[pos + 12:pos + 14], "little")
                if pos + 18 + vlen > len(raw):
                    early = 1
                    break
                stored = int.from_bytes(raw[pos + 14 + vlen:pos + 18 + vlen], "little")
                if (zlib.crc32(raw[pos:pos + 14 + vlen]) & 0xFFFFFFFF) != stored:
                    early = 1
                    break
                key = int.from_bytes(raw[pos + 8:pos + 12], "little")
                if raw[pos + 2] == 1:
                    vh = 0
                    for b in raw[pos + 14:pos + 14 + vlen]:
                        vh = (vh * 131 + b) % MOD
                    kv[key] = vh
                else:
                    kv.pop(key, None)
                seg_rep += 1
                pos += 18 + vlen
            replayed += seg_rep
            ck = (ck * 37 + seg * 1009 + seg_rep * 17 + early) % MOD

        for k in range(4096):
            if k in kv:
                ck = (ck * 31 + k * 97 + kv[k]) % MOD

        expected = f"{replayed}\n{ck}\n"
        self.assertEqual(expected, "119984\n241048890\n")
        self.assertEqual(suite.BY_NAME["wal_log_recovery"].expect, expected)


if __name__ == "__main__":
    unittest.main()
