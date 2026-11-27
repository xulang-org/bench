"""Independent goldens and registry contract checks for Batch F (Systems/Tooling/Compression) benchmarks."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402

GOLDEN = ROOT / "tests" / "bench" / "golden"
MOD = 1_000_000_007

BATCH_F_NAMES = (
    "expr_bytecode_vm",
    "myers_diff",
    "slab_allocator",
    "timing_wheel",
    "lz4_block_codec",
    "utf8_text_norm",
)


class TestBatchFRegistryAndGoldens(unittest.TestCase):
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
        self.assertGreaterEqual(len(ast_names), 113)
        self.assertEqual(len(set(ast_names)), len(ast_names))
        name_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in ast_names:
            self.assertRegex(name, name_re)

        self.assertIn("systems", summary.CATEGORY_NAMES)
        for name in BATCH_F_NAMES:
            self.assertIn(name, suite.BY_NAME)
            self.assertEqual(suite.BY_NAME[name].langs, suite.CORE)
            self.assertIn(name, summary.BENCH_DESCRIPTIONS)
            self.assertEqual(summary.BENCH_DESCRIPTIONS[name][2], "systems")
            golden_bytes = (GOLDEN / f"{name}.txt").read_bytes()
            self.assertNotIn(b"\r", golden_bytes)
            self.assertEqual(golden_bytes.decode("ascii"), suite.BY_NAME[name].expect)
            self.assertTrue((ROOT / "tests" / "bench" / f"{name}.xu").is_file())
            for ext in suite.CORE:
                self.assertTrue((ROOT / "tests" / "bench" / "cross" / f"{name}.{ext}").is_file())

    def test_expr_bytecode_vm_oracle(self) -> None:
        mask30 = 1073741823
        base30 = 1073741824
        exprs = [
            "((x + y) * (z + 7) - (x ^ y)) / ((z & 15) + 1) + (x % 97)",
            "(~x & 65535) + ((y * 13 + z) ^ (x + y + z)) - (y / 3)",
            "((x * 3 + y * 5 + z * 7) ^ (x * 11 - y)) + ((z | 255) & (x + 1023))",
            "-(x - y) + (z * (x & 255) + (y % 31)) ^ (~z & 4095)",
            "(((x + 17) * (y + 29)) % 65521) + ((z ^ (x + y)) / ((x & 7) + 1))",
            "((x | y) & (y | z) & (z | x)) + ((x ^ y ^ z) * 19) - (z % 17)",
            "(x + (y + (z + (x * 3 + (y * 5 - z))))) & 1048575",
            "((x / 5 + y / 7 + z / 11) * (x % 13 + y % 17 + 1)) ^ (x + z)",
            "((~x & 1023) * (~y & 1023) + (~z & 1023)) % 1000003",
            "(((x ^ 12345) + (y ^ 6789)) * 7) / ((z % 23) + 2) + (y & 511)",
            "(x * (y & 63) - y * (z & 63) + z * (x & 63)) ^ ((x + y) | z)",
            "((x + y + z) * (x + y + z)) / (x % 29 + y % 31 + 3) + (~(x & y) & 8191)",
            "(((x & 4095) + 1) * ((y & 4095) + 3) + ((z & 4095) + 5)) ^ (x * 17)",
            "((x - (y - (z - x))) + (y * 9 - z * 5)) % 99991 + (x & z)",
            "((x | 85) ^ (y | 170) ^ (z | 51)) + ((x + y) * 23) / ((y & 31) + 1)",
            "((((x + 3) * 5 - y) ^ (z + 11)) + ((y + 7) * (z & 127))) % 524287",
        ]

        def count_ops(node: ast.AST) -> int:
            if isinstance(node, (ast.Constant, ast.Name)):
                return 1
            if isinstance(node, ast.UnaryOp):
                return 1 + count_ops(node.operand)
            if isinstance(node, ast.BinOp):
                return 1 + count_ops(node.left) + count_ops(node.right)
            raise ValueError(node)

        def eval_ast(node: ast.AST, x: int, y: int, z: int) -> int:
            if isinstance(node, ast.Constant):
                return node.value & mask30
            if isinstance(node, ast.Name):
                return {"x": x, "y": y, "z": z}[node.id]
            if isinstance(node, ast.UnaryOp):
                v = eval_ast(node.operand, x, y, z)
                return (base30 - v) & mask30 if isinstance(node.op, ast.USub) else (v ^ mask30)
            if isinstance(node, ast.BinOp):
                a = eval_ast(node.left, x, y, z)
                b = eval_ast(node.right, x, y, z)
                if isinstance(node.op, ast.Add): return (a + b) & mask30
                if isinstance(node.op, ast.Sub): return (a - b + base30) & mask30
                if isinstance(node.op, ast.Mult): return ((a & 32767) * (b & 32767)) & mask30
                if isinstance(node.op, ast.Div): return a // (b + 1)
                if isinstance(node.op, ast.Mod): return a % (b + 1)
                if isinstance(node.op, ast.BitAnd): return a & b
                if isinstance(node.op, ast.BitOr): return a | b
                if isinstance(node.op, ast.BitXor): return a ^ b
            raise ValueError(node)

        parsed = [ast.parse(e, mode="eval").body for e in exprs]
        ops_per_expr = [count_ops(p) for p in parsed]
        self.assertEqual(sum(ops_per_expr) * 160 * 100, 5488000)

        rng = 112233445
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        total_insts, ck = 0, 0
        for _ in range(160):
            for p, n_ops in zip(parsed, ops_per_expr):
                for _ in range(100):
                    x, y, z = nxt() & 65535, nxt() & 65535, nxt() & 65535
                    res = eval_ast(p, x, y, z)
                    total_insts += n_ops
                    ck = (ck * 31 + res) % MOD

        expected = f"{total_insts}\n{ck}\n"
        self.assertEqual(expected, "5488000\n628681581\n")
        self.assertEqual(suite.BY_NAME["expr_bytecode_vm"].expect, expected)

    def test_myers_diff_oracle(self) -> None:
        rng = 20260501
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        max_d, stride, off = 120, 241, 120
        v = [0] * stride
        trace = [0] * ((max_d + 1) * stride)
        total_edits, ck = 0, 0
        for pair in range(1200):
            n = 200
            a = [nxt() & 63 for _ in range(n)]
            b = list(a)
            for _ in range(18 + (nxt() % 11)):
                kind = nxt() % 3
                if kind == 0 and len(b) > 120:
                    del b[nxt() % len(b)]
                elif kind == 1 and len(b) < 260:
                    pos = nxt() % (len(b) + 1)
                    b.insert(pos, nxt() & 63)
                else:
                    pos = nxt() % len(b)
                    b[pos] = nxt() & 63
            m = len(b)
            v[off + 1] = 0
            found_d = -1
            for d in range(max_d + 1):
                tbase = d * stride
                for k in range(-d, d + 1, 2):
                    x = v[off + k + 1] if (k == -d or (k != d and v[off + k - 1] < v[off + k + 1])) else (v[off + k - 1] + 1)
                    y = x - k
                    while x < n and y < m and a[x] == b[y]:
                        x += 1
                        y += 1
                    v[off + k] = x
                    trace[tbase + off + k] = x
                    if x >= n and y >= m:
                        found_d = d
                        break
                if found_d >= 0:
                    break
            x, y, ops = n, m, []
            for bd in range(found_d, 0, -1):
                pbase = (bd - 1) * stride
                k = x - y
                pk = k + 1 if (k == -bd or (k != bd and trace[pbase + off + k - 1] < trace[pbase + off + k + 1])) else (k - 1)
                px = trace[pbase + off + pk]
                py = px - pk
                while x > px and y > py:
                    ops.append((0, a[x - 1])); x -= 1; y -= 1
                if x == px:
                    ops.append((1, b[y - 1])); y -= 1
                else:
                    ops.append((2, a[x - 1])); x -= 1
            while x > 0 and y > 0:
                ops.append((0, a[x - 1])); x -= 1; y -= 1
            if pair < 10:
                self.assertEqual([val for t, val in reversed(ops) if t != 2], b)
            total_edits += found_d
            sh = found_d
            for t, val in ops:
                sh = (sh * 131 + t * 67 + val) % MOD
            ck = (ck * 31 + sh) % MOD

        expected = f"{total_edits}\n{ck}\n"
        self.assertEqual(expected, "35144\n450000758\n")
        self.assertEqual(suite.BY_NAME["myers_diff"].expect, expected)

    def test_slab_allocator_oracle(self) -> None:
        rng = 31415926
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        n_pages, page_words = 256, 256
        class_sz = (2, 4, 8, 16, 32, 64)
        mem = [0] * (n_pages * page_words)
        page_cls = [-1] * n_pages
        page_used = [0] * n_pages
        page_head = [-1] * n_pages
        page_prev = [-1] * n_pages
        page_next = [-1] * n_pages
        page_in_list = [0] * n_pages
        cls_head = [-1] * 6
        free_stack = [n_pages - 1 - i for i in range(n_pages)]
        page_allocs = page_reclaims = 0

        def list_push(cls: int, pg: int) -> None:
            h = cls_head[cls]
            page_prev[pg] = -1; page_next[pg] = h
            if h != -1: page_prev[h] = pg
            cls_head[cls] = pg; page_in_list[pg] = 1

        def list_remove(cls: int, pg: int) -> None:
            pr, nx = page_prev[pg], page_next[pg]
            if pr != -1: page_next[pr] = nx
            else: cls_head[cls] = nx
            if nx != -1: page_prev[nx] = pr
            page_prev[pg] = page_next[pg] = -1; page_in_list[pg] = 0

        def slab_alloc(cls: int) -> int:
            nonlocal page_allocs
            pg = cls_head[cls]
            if pg == -1:
                if not free_stack: return -1
                pg = free_stack.pop()
                page_allocs += 1; page_cls[pg] = cls; page_used[pg] = 0
                sz = class_sz[cls]; base = pg << 8; cnt = page_words // sz
                for s in range(cnt - 1): mem[base + s * sz] = base + (s + 1) * sz
                mem[base + (cnt - 1) * sz] = -1; page_head[pg] = base
                list_push(cls, pg)
            ptr = page_head[pg]; page_head[pg] = mem[ptr]; page_used[pg] += 1
            if page_head[pg] == -1: list_remove(cls, pg)
            return ptr

        def slab_free(ptr: int) -> None:
            nonlocal page_reclaims
            pg = ptr >> 8; cls = page_cls[pg]
            was_full = page_head[pg] == -1
            mem[ptr] = page_head[pg]; page_head[pg] = ptr; page_used[pg] -= 1
            if page_used[pg] == 0:
                if page_in_list[pg]: list_remove(cls, pg)
                page_cls[pg] = page_head[pg] = -1
                free_stack.append(pg); page_reclaims += 1
            elif was_full:
                list_push(cls, pg)

        live = 1024
        live_ptr = [-1] * live
        live_cls = [0] * live
        alloc_ok = ck = 0
        for op_i in range(600000):
            slot = nxt() & 1023
            if (op_i & 4095) == 4095:
                for k in range(0, live, 3):
                    p = live_ptr[k]
                    if p != -1:
                        sz = class_sz[live_cls[k]]
                        ck = (ck * 31 + mem[p] + mem[p + sz - 1]) % MOD
                        slab_free(p); live_ptr[k] = -1
            if live_ptr[slot] != -1:
                p = live_ptr[slot]; sz = class_sz[live_cls[slot]]
                ck = (ck * 31 + mem[p] + mem[p + sz - 1]) % MOD
                slab_free(p); live_ptr[slot] = -1
            else:
                r = nxt() % 100
                cls = 0 if r < 35 else (1 if r < 60 else (2 if r < 78 else (3 if r < 90 else (4 if r < 97 else 5))))
                p = slab_alloc(cls)
                if p >= 0:
                    sz = class_sz[cls]
                    tag = (op_i * 13 + cls * 7 + 1) % MOD
                    mem[p] = tag; mem[p + sz - 1] = (tag ^ (p * 3)) % MOD
                    live_ptr[slot] = p; live_cls[slot] = cls; alloc_ok += 1
        for k in range(live):
            p = live_ptr[k]
            if p != -1:
                sz = class_sz[live_cls[k]]
                ck = (ck * 31 + mem[p] + mem[p + sz - 1]) % MOD
                slab_free(p)
        self.assertEqual(len(free_stack), n_pages)
        ck = (ck * 37 + page_allocs * 17 + page_reclaims) % MOD
        expected = f"{alloc_ok}\n{ck}\n"
        self.assertEqual(expected, "300032\n352385751\n")
        self.assertEqual(suite.BY_NAME["slab_allocator"].expect, expected)

    def test_timing_wheel_oracle(self) -> None:
        import collections
        rng = 888777666
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        # Independent 2-level deque-bucket timing wheel with handle generation validation
        max_nodes = 131072
        active: dict[int, tuple[int, int, int, int, int]] = {}  # u -> (gen, exp, per, rep, pay)
        b_deqs: list[collections.deque[tuple[int, int]]] = [collections.deque() for _ in range(512)]
        handles = [-1] * 16384
        h_wr = fired = canceled = ck = gen_seq = 0
        free_top = max_nodes
        free_stack = [max_nodes - 1 - i for i in range(max_nodes)]

        def push_wheel(u: int, gen: int, exp: int, now: int) -> None:
            b = (exp & 255) if (exp - now) < 256 else (256 + ((exp >> 8) & 255))
            b_deqs[b].append((u, gen))

        for now in range(160000):
            for _ in range(3):
                if free_top > 0:
                    free_top -= 1
                    u = free_stack[free_top]
                    delay = (1 + (nxt() % 250)) if (nxt() % 10) < 6 else (256 + (nxt() % 4096))
                    per = (17 + (nxt() % 200)) if (nxt() % 5) == 0 else 0
                    rep = 2 if per > 0 else 0
                    pay = nxt() % 100000
                    gen_seq += 1
                    exp = now + delay
                    active[u] = (gen_seq, exp, per, rep, pay)
                    push_wheel(u, gen_seq, exp, now)
                    handles[h_wr] = u
                    h_wr = (h_wr + 1) & 16383
            ci = nxt() & 16383
            cu = handles[ci]
            if cu in active:
                active.pop(cu)
                free_stack[free_top] = cu
                free_top += 1
                handles[ci] = -1
                canceled += 1
            tick = now + 1
            if (tick & 255) == 0:
                cb = 256 + ((tick >> 8) & 255)
                cq = b_deqs[cb]
                while cq:
                    u, gen = cq.popleft()
                    info = active.get(u)
                    if info is not None and info[0] == gen:
                        b_deqs[info[1] & 255].append((u, gen))
            q = b_deqs[tick & 255]
            while q:
                u, gen = q.popleft()
                info = active.get(u)
                if info is None or info[0] != gen:
                    continue
                _, exp, per, rep, pay = info
                self.assertEqual(exp, tick)
                fired += 1
                ck = (ck * 31 + pay * 7 + tick) % MOD
                if rep > 0:
                    nxt_exp = tick + per
                    active[u] = (gen, nxt_exp, per, rep - 1, pay)
                    push_wheel(u, gen, nxt_exp, tick)
                else:
                    active.pop(u)
                    free_stack[free_top] = u
                    free_top += 1
        ck = (ck * 37 + canceled) % MOD
        expected = f"{fired}\n{ck}\n"
        self.assertEqual(expected, "479931\n463812537\n")
        self.assertEqual(suite.BY_NAME["timing_wheel"].expect, expected)

    def test_lz4_block_codec_oracle(self) -> None:
        rng = 135724680
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        blk_len = 32768
        phrases = (
            b'{"level":"INFO","service":"storage-node","msg":"compaction_ok","ms":',
            b'{"level":"WARN","service":"rpc-gateway","msg":"retry_backoff","ms":',
            b'SELECT region, category, SUM(amount) FROM orders WHERE status = 1; ',
            b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
            b'GET /api/v1/users/profile HTTP/1.1\r\nHost: api.xulang.org\r\n\r\n',
            b'0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
        )
        blocks = []
        for _ in range(24):
            src = bytearray()
            while len(src) < blk_len:
                k = nxt() % 10
                if k < 6:
                    src.extend(phrases[k])
                    v = nxt() % 1000
                    src.extend((48 + (v // 100), 48 + ((v // 10) % 10), 48 + (v % 10), 10))
                elif k < 8:
                    ch = 65 + (nxt() % 26)
                    src.extend([ch] * (12 + (nxt() % 48)))
                else:
                    for _ in range(8 + (nxt() % 24)):
                        src.append(32 + (nxt() % 95))
            blocks.append(bytes(src[:blk_len]))

        def compress(src: bytes) -> bytes:
            ht = [-1] * 4096
            out = bytearray()
            ip = anchor = 0
            limit, mflimit = blk_len - 12, blk_len - 5
            while ip < limit:
                seq = src[ip] | (src[ip + 1] << 8) | (src[ip + 2] << 16) | (src[ip + 3] << 24)
                h = ((seq * 0x45D9F3B) >> 18) & 4095
                ref = ht[h]; ht[h] = ip
                if ref >= 0 and (ip - ref) <= 65535 and src[ref:ref + 4] == src[ip:ip + 4]:
                    mlen = 4
                    while ip + mlen < mflimit and src[ref + mlen] == src[ip + mlen]:
                        mlen += 1
                    lit_len, m_extra = ip - anchor, mlen - 4
                    out.append(((15 if lit_len >= 15 else lit_len) << 4) | (15 if m_extra >= 15 else m_extra))
                    if lit_len >= 15:
                        rem = lit_len - 15
                        while rem >= 255: out.append(255); rem -= 255
                        out.append(rem)
                    out.extend(src[anchor:ip])
                    out.extend((ip - ref).to_bytes(2, "little"))
                    if m_extra >= 15:
                        rem = m_extra - 15
                        while rem >= 255: out.append(255); rem -= 255
                        out.append(rem)
                    ip += mlen; anchor = ip
                else:
                    ip += 1
            lit_len = blk_len - anchor
            out.append((15 if lit_len >= 15 else lit_len) << 4)
            if lit_len >= 15:
                rem = lit_len - 15
                while rem >= 255: out.append(255); rem -= 255
                out.append(rem)
            out.extend(src[anchor:])
            return bytes(out)

        def decompress(comp: bytes) -> bytes:
            dec = bytearray()
            ip, clen = 0, len(comp)
            while ip < clen:
                tok = comp[ip]; ip += 1
                lit_len = tok >> 4
                if lit_len == 15:
                    while True:
                        b = comp[ip]; ip += 1; lit_len += b
                        if b != 255: break
                dec.extend(comp[ip:ip + lit_len]); ip += lit_len
                if ip >= clen: break
                off = int.from_bytes(comp[ip:ip + 2], "little"); ip += 2
                mlen = (tok & 15) + 4
                if (tok & 15) == 15:
                    while True:
                        b = comp[ip]; ip += 1; mlen += b
                        if b != 255: break
                for _ in range(mlen):
                    dec.append(dec[-off])
            return bytes(dec)

        total_comp, ck = 0, 0
        for rnd in range(4):
            for src in blocks:
                c = compress(src)
                if rnd == 0:
                    self.assertEqual(decompress(c), src)
                h = len(c)
                for b in src:
                    h = (h * 131 + b) % MOD
                total_comp += len(c)
                ck = (ck * 31 + h) % MOD

        expected = f"{total_comp}\n{ck}\n"
        self.assertEqual(expected, "609348\n141693848\n")
        self.assertEqual(suite.BY_NAME["lz4_block_codec"].expect, expected)

    def test_utf8_text_norm_oracle(self) -> None:
        rng = 246801357
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        src = bytearray()
        while len(src) < 65520:
            r = nxt() % 100
            if r < 38:
                k = nxt() % 62
                cp = 65 + k if k < 26 else (97 + (k - 26) if k < 52 else 48 + (k - 52))
                src.extend(chr(cp).encode("utf-8"))
            elif r < 52:
                src.extend(chr((0x20, 0x09, 0x0A, 0x0D, 0x00A0, 0x3000)[nxt() % 6]).encode("utf-8"))
            elif r < 64:
                g = nxt() % 3
                cp = 0xC0 + (nxt() % 62) if g == 0 else (0x0391 + (nxt() % 40) if g == 1 else 0x0410 + (nxt() % 64))
                src.extend(chr(cp).encode("utf-8"))
            elif r < 78:
                cp = (0x2018, 0x2019, 0x201C, 0x201D)[nxt() & 3] if (nxt() & 3) == 0 else (0xFF01 + (nxt() % 94))
                src.extend(chr(cp).encode("utf-8"))
            elif r < 90:
                src.extend(chr(0x4E00 + (nxt() % 512)).encode("utf-8"))
            elif r < 97:
                src.extend(chr(0x1F600 + (nxt() % 64)).encode("utf-8"))
            else:
                inv = nxt() % 4
                if inv == 0: src.append(0x80 + (nxt() % 64))
                elif inv == 1: src.extend((0xC0, 0xAF))
                elif inv == 2: src.extend((0xED, 0xA0, 0x80))
                else: src.extend((0xF4, 0x90, 0x80, 0x80))

        # Python's stdlib utf-8 replace decoder + character normalization must produce identical output
        decoded = bytes(src).decode("utf-8", errors="replace")
        # Normalize consecutive overlong/invalid bytes using our single-step U+FFFD rule:
        # Note: in bytes.decode("utf-8", "replace"), multi-byte invalid sequences like C0 AF produce 2 U+FFFDs cleanly just like adv=1!
        out_chars = []
        in_ws = True
        for ch in decoded:
            cp = ord(ch)
            if cp in (0x20, 0x09, 0x0A, 0x0D, 0x00A0, 0x3000):
                if not in_ws:
                    out_chars.append(" ")
                    in_ws = True
                continue
            in_ws = False
            if 0xFF01 <= cp <= 0xFF5E:
                cp -= 0xFEE0
            if 0x41 <= cp <= 0x5A: cp += 32
            elif (0xC0 <= cp <= 0xD6) or (0xD8 <= cp <= 0xDE): cp += 32
            elif (0x0391 <= cp <= 0x03A1) or (0x03A3 <= cp <= 0x03AB): cp += 32
            elif 0x0410 <= cp <= 0x042F: cp += 32
            elif cp in (0x2018, 0x2019): cp = 0x27
            elif cp in (0x201C, 0x201D): cp = 0x22
            out_chars.append(chr(cp))

        out_bytes = "".join(out_chars).encode("utf-8")
        olen = len(out_bytes)
        h = olen
        for b in out_bytes:
            h = (h * 131 + b) % MOD
        total_out = olen * 40
        ck = 0
        for _ in range(40):
            ck = (ck * 31 + h) % MOD

        expected = f"{total_out}\n{ck}\n"
        self.assertEqual(expected, "2339280\n538177438\n")
        self.assertEqual(suite.BY_NAME["utf8_text_norm"].expect, expected)


if __name__ == "__main__":
    unittest.main()
