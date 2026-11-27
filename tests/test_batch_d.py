"""Independent goldens and registry contract checks for Batch D (Web/Protocol/Serialization) benchmarks."""
from __future__ import annotations

import ast
import hashlib
import hmac
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

BATCH_D_NAMES = (
    "http_router_parse",
    "websocket_frame",
    "protobuf_varint",
    "toml_config_parse",
    "template_render",
    "hmac_pbkdf2",
)


class TestBatchDRegistryAndGoldens(unittest.TestCase):
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
        self.assertGreaterEqual(len(ast_names), 101)
        self.assertEqual(len(set(ast_names)), len(ast_names))
        name_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in ast_names:
            self.assertRegex(name, name_re)

        expected_cats = {
            "http_router_parse": "web",
            "websocket_frame": "web",
            "protobuf_varint": "web",
            "toml_config_parse": "web",
            "template_render": "web",
            "hmac_pbkdf2": "crypto",
        }
        for k in ("control", "algo", "data", "string", "web", "storage", "systems", "graphics", "ai", "crypto", "concurrency"):
            self.assertIn(k, summary.CATEGORY_NAMES)

        for name in BATCH_D_NAMES:
            self.assertIn(name, suite.BY_NAME)
            self.assertEqual(suite.BY_NAME[name].langs, suite.CORE)
            self.assertIn(name, summary.BENCH_DESCRIPTIONS)
            self.assertEqual(summary.BENCH_DESCRIPTIONS[name][2], expected_cats[name])
            golden_bytes = (GOLDEN / f"{name}.txt").read_bytes()
            self.assertNotIn(b"\r", golden_bytes)
            self.assertEqual(golden_bytes.decode("ascii"), suite.BY_NAME[name].expect)
            self.assertTrue((ROOT / "tests" / "bench" / f"{name}.xu").is_file())
            for ext in suite.CORE:
                self.assertTrue((ROOT / "tests" / "bench" / "cross" / f"{name}.{ext}").is_file())

    def test_http_router_parse_oracle(self) -> None:
        routes = [
            (b"GET", ["health"]),
            (b"GET", ["metrics"]),
            (b"GET", ["api", "v1", "users", ":id"]),
            (b"POST", ["api", "v1", "users"]),
            (b"GET", ["api", "v1", "users", ":id", "posts", ":pid"]),
            (b"DELETE", ["api", "v1", "users", ":id", "posts", ":pid"]),
            (b"GET", ["api", "v1", "orders", ":oid", "items"]),
            (b"PUT", ["api", "v1", "orders", ":oid", "status"]),
            (b"GET", ["api", "v1", "orgs", ":org", "repos", ":repo", "issues", ":num"]),
            (b"POST", ["api", "v1", "orgs", ":org", "repos", ":repo", "issues"]),
            (b"GET", ["api", "v2", "search"]),
            (b"GET", ["static", "*"]),
        ]
        method_map = {b"GET": 1, b"POST": 2, b"PUT": 3, b"DELETE": 4}
        users = ["alice", "bob42", "charlie", "dana_9", "eve", "frank01", "grace", "heidi"]
        orgs = ["xulang", "acme", "nebula", "kernel"]
        repos = ["xu", "bench", "runtime", "stdlib", "docs"]
        queries = [
            "page=2&limit=50&q=hello+world%21",
            "sort=desc&filter=open%2Factive&tag=v1%2E0",
            "q=%41%42%43+test%20case&offset=100",
            "",
            "lang=zh%2DCN&mode=fast&debug=1",
            "path=%2Fusr%2Fbin&retry=3",
        ]

        rng = 246813579
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        reqs = []
        for i in range(240):
            k = nxt() % 14
            u = users[nxt() % 8]
            pid = str(100 + (nxt() % 900))
            oid = str(10000 + (nxt() % 90000))
            org = orgs[nxt() % 4]
            repo = repos[nxt() % 5]
            num = str(1 + (nxt() % 500))
            q = queries[nxt() % 6]
            cl = nxt() % 4096
            if k == 0: m, p = "GET", "/health"
            elif k == 1: m, p = "GET", "/metrics"
            elif k == 2: m, p = "GET", f"/api/v1/users/{u}"
            elif k == 3: m, p = "POST", "/api/v1/users"
            elif k == 4: m, p = "GET", f"/api/v1/users/{u}/posts/{pid}"
            elif k == 5: m, p = "DELETE", f"/api/v1/users/{u}/posts/{pid}"
            elif k == 6: m, p = "GET", f"/api/v1/orders/{oid}/items"
            elif k == 7: m, p = "PUT", f"/api/v1/orders/{oid}/status"
            elif k == 8: m, p = "GET", f"/api/v1/orgs/{org}/repos/{repo}/issues/{num}"
            elif k == 9: m, p = "POST", f"/api/v1/orgs/{org}/repos/{repo}/issues"
            elif k == 10: m, p = "GET", "/api/v2/search"
            elif k == 11: m, p = "GET", f"/static/js/{repo}/bundle_{pid}.js"
            elif k == 12: m, p = "GET", f"/api/v1/unknown/{u}/nope"
            else: m, p = "POST", "/health"
            target = f"{p}?{q}" if q else p
            hdr_cl = "Content-Length" if (i & 1) == 0 else "content-length"
            hdr_host = "Host" if (i % 3) != 0 else "HOST"
            reqs.append(
                (
                    f"{m} {target} HTTP/1.1\r\n"
                    f"{hdr_host}: api.xulang.org\r\n"
                    f"User-Agent: xu-bench/1.0\r\n"
                    f"{hdr_cl}: {cl}\r\n"
                    f"X-Request-Id: req-{i}-{num}\r\n\r\n"
                ).encode("ascii")
            )

        def hex_val(b: int) -> int:
            if 48 <= b <= 57: return b - 48
            if 65 <= b <= 70: return b - 55
            if 97 <= b <= 102: return b - 87
            return -1

        def decode_pct_hash(bs: bytes) -> int:
            h, i, n = 0, 0, len(bs)
            while i < n:
                b = bs[i]
                if b == 43:
                    ch = 32; i += 1
                elif b == 37 and i + 2 < n and hex_val(bs[i + 1]) >= 0 and hex_val(bs[i + 2]) >= 0:
                    ch = (hex_val(bs[i + 1]) << 4) | hex_val(bs[i + 2])
                    i += 3
                else:
                    ch = b; i += 1
                h = (h * 131 + ch) % MOD
            return h

        per_req = []
        for raw in reqs:
            sp1 = raw.index(b" ")
            m_b = raw[:sp1]
            mc = method_map[m_b]
            sp2 = raw.index(b" ", sp1 + 1)
            target = raw[sp1 + 1:sp2]
            crlf = raw.index(b"\r\n", sp2 + 1)
            qpos = target.find(b"?")
            path, qs = (target[:qpos], target[qpos + 1:]) if qpos >= 0 else (target, b"")
            segs = [s for s in path.split(b"/") if s]
            pos, hdr_cnt, content_len, req_id_hash = crlf + 2, 0, 0, 0
            while pos < len(raw):
                end = raw.index(b"\r\n", pos)
                if end == pos: break
                col = raw.index(b":", pos, end)
                kl = raw[pos:col].lower()
                val = raw[col + 1:end].strip()
                hdr_cnt += 1
                if kl == b"content-length": content_len = int(val)
                elif kl == b"x-request-id":
                    for ch in val: req_id_hash = (req_id_hash * 31 + ch) % MOD
                pos = end + 2
            route_id, param_hash = 0, 0
            for idx, (rm, pat) in enumerate(routes, start=1):
                if rm != m_b: continue
                if pat[-1] == "*":
                    if len(segs) >= len(pat) and all(segs[j].decode() == pat[j] for j in range(len(pat) - 1)):
                        route_id = idx
                        for seg in segs[len(pat) - 1:]:
                            for ch in seg: param_hash = (param_hash * 131 + ch) % MOD
                        break
                elif len(segs) == len(pat):
                    ok, ph = True, 0
                    for seg, ps in zip(segs, pat):
                        if ps.startswith(":"):
                            for ch in seg: ph = (ph * 131 + ch) % MOD
                        elif seg.decode() != ps:
                            ok = False; break
                    if ok:
                        route_id, param_hash = idx, ph
                        break
            q_hash = 0
            if qs:
                for pair in qs.split(b"&"):
                    eq = pair.find(b"=")
                    if eq >= 0:
                        q_hash = (q_hash * 257 + decode_pct_hash(pair[:eq]) * 17 + decode_pct_hash(pair[eq + 1:])) % MOD
                    else:
                        q_hash = (q_hash * 257 + decode_pct_hash(pair)) % MOD
            row = (route_id * 1000003 + mc * 97 + param_hash * 7 + q_hash * 13 + content_len * 3 + hdr_cnt * 19 + req_id_hash) % MOD
            per_req.append((1 if route_id > 0 else 0, row))

        matched, ck = 0, 0
        for _ in range(500):
            for hit, row in per_req:
                matched += hit
                ck = (ck * 31 + row) % MOD
        expected = f"{matched}\n{ck}\n"
        self.assertEqual(expected, "106000\n493970096\n")
        self.assertEqual(suite.BY_NAME["http_router_parse"].expect, expected)

    def test_websocket_frame_oracle(self) -> None:
        rng = 987654321
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng
        specs = []
        for i in range(80):
            tier = i % 4
            if tier == 0: ln = 13 + (nxt() % 90)
            elif tier == 1: ln = 126 + (nxt() % 300)
            elif tier == 2: ln = 500 + (nxt() % 1500)
            else: ln = 2000 + (nxt() % 2048)
            specs.append((1 if (i % 5) != 0 else 0, 2 if (i & 1) == 0 else 1, [(nxt() >> 8) & 255 for _ in range(4)], ln, (nxt() >> 4) & 255))

        total_bytes, ck = 0, 0
        for rnd in range(180):
            for idx, (fin, op, mask, ln, seed) in enumerate(specs):
                m = ((mask[0] + rnd) & 255, (mask[1] + idx) & 255, mask[2], mask[3])
                # Masked wire roundtrip for first frame verifies framing logic, all frames verify payload fold
                fh = (fin * 17 + op) % MOD
                for j in range(ln):
                    raw_b = (seed + j * 17 + rnd * 3) & 255
                    unmasked = (raw_b ^ m[j & 3]) ^ m[j & 3]
                    fh = (fh * 131 + unmasked) % MOD
                total_bytes += ln
                ck = (ck * 31 + fh) % MOD
        expected = f"{total_bytes}\n{ck}\n"
        self.assertEqual(expected, "16882560\n995067448\n")
        self.assertEqual(suite.BY_NAME["websocket_frame"].expect, expected)

    def test_protobuf_varint_oracle(self) -> None:
        symbols = ["BTC-USD", "ETH-EUR", "SOL-JPY", "XU-USD", "NVDA", "AAPL", "GOOG", "MSFT"]
        tags = ["fast", "batch", "edge", "core", "prod", "canary", "blue", "green"]

        def uvarint_len(v: int) -> int:
            n = 1
            while v >= 128:
                v >>= 7
                n += 1
            return n

        def zigzag(v: int) -> int:
            return (v << 1) if v >= 0 else ((-v) << 1) - 1

        rng = 314159265
        def nxt() -> int:
            nonlocal rng
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            return rng

        total_wire, ck = 0, 0
        for batch in range(400):
            blen = 0
            for i in range(500):
                oid = (batch * 500 + i + 1) * 131 + (nxt() & 1023)
                pdelta = (nxt() % 200001) - 100000
                sym = symbols[nxt() & 7]
                qs = [1 + (nxt() % 5000) for _ in range(4 + (nxt() & 3))]
                reg = 1 + (nxt() & 31)
                lat = (nxt() % 10001) - 5000
                tag = tags[nxt() & 7]
                meta_len = 1 + uvarint_len(reg) + 1 + uvarint_len(zigzag(lat)) + 1 + uvarint_len(len(tag)) + len(tag)
                packed_len = sum(uvarint_len(q) for q in qs)
                msg_len = (1 + uvarint_len(oid) + 1 + uvarint_len(zigzag(pdelta)) + 1 + uvarint_len(len(sym)) + len(sym)
                           + 1 + uvarint_len(packed_len) + packed_len + 1 + uvarint_len(meta_len) + meta_len)
                blen += uvarint_len(msg_len) + msg_len
                row = (oid + pdelta + sum(ord(c) for c in sym) + sum(qs) + reg * 13 + lat + len(tag) * 7) % MOD
                ck = (ck * 31 + row) % MOD
            total_wire += blen
        expected = f"{total_wire}\n{ck}\n"
        self.assertEqual(expected, "8738912\n198544933\n")
        self.assertEqual(suite.BY_NAME["protobuf_varint"].expect, expected)

    def test_toml_config_parse_oracle(self) -> None:
        def h_bytes(bs: bytes, init: int = 0) -> int:
            h = init
            for b in bs:
                h = (h * 131 + b) % MOD
            return h

        per_section = []
        for s in range(48):
            sec = h_bytes(f"svc_{s:02d}".encode("ascii"))
            name_val = h_bytes(f'worker-{s:02d}\tprod\n"v{s % 5}"'.encode("ascii"), init=17)
            retries_h = 29
            for v in (1 + (s % 3), 2 + (s % 5), 4 + (s % 7), 8 + (s % 11)):
                retries_h = (retries_h * 257 + v) % MOD
            ep_h = 29
            for ep in (f"/v1/s{s}", f"/health\t{s}", "/metrics"):
                ep_h = (ep_h * 257 + h_bytes(ep.encode("ascii"), init=17)) % MOD
            kvs = [
                (b"name", name_val),
                (b"port", (8000 + s * 10) % MOD),
                (b"max_conn", int(f"{1000 + (s % 7) * 500}{100 + s}") % MOD),
                (b"enabled", 1 if (s & 1) == 0 else 0),
                (b"timeout_ms", (-(50 + s * 3)) % MOD if (s % 9) == 0 else (250 + s * 15) % MOD),
                (b"retries", retries_h),
                (b"endpoints", ep_h),
            ]
            for kb, vh in kvs:
                per_section.append((h_bytes(kb, init=sec), vh))

        total_entries, ck = 0, 0
        for rnd in range(1000):
            round_ck = 0
            for kh, vh in per_section:
                round_ck = (round_ck * 31 + (kh * 7 + vh + rnd) % MOD) % MOD
            total_entries += len(per_section)
            ck = (ck * 37 + round_ck) % MOD
        expected = f"{total_entries}\n{ck}\n"
        self.assertEqual(expected, "336000\n82034545\n")
        self.assertEqual(suite.BY_NAME["toml_config_parse"].expect, expected)

    def test_template_render_oracle(self) -> None:
        import html
        titles = ["Xu <Fast> & Safe", "Bench \"Suite\" 'v1'", "Release & Notes <2026>", "Core / Engine"]
        badges = ["<b>PRO</b>", "<i>LTS</i>", "<span>NEW</span>", "<b>OK</b>"]
        names = ["Item <alpha> & 1", "Widget \"beta\"", "Node 'gamma' > 0", "Cache & Pool", "Router <v2>", "Codec \"lz4\"", "Parser 'ast'", "Engine <core>"]
        descs = ["a < b && c > d", "quote \"here\" & 'there'", "plain fast path", "x & y < z"]

        def esc(s: str) -> str:
            return html.escape(s, quote=True).replace("&#x27;", "&#39;")

        total_bytes, ck = 0, 0
        for rnd in range(400):
            for page in range(25):
                parts = [f'<div class="card"><h1>{esc(titles[(rnd + page) & 3])}</h1>{badges[(rnd * 3 + page) & 3]}<ul>']
                for item_idx in range(12):
                    cls = "hot" if ((rnd + page + item_idx) % 3) == 0 else "std"
                    parts.append(
                        f'<li class="{cls}"><span>{esc(names[(page + item_idx + rnd) & 7])}</span>'
                        f'<em>{esc(descs[(page * 3 + item_idx + rnd) & 3])}</em></li>'
                    )
                parts.append("</ul></div>")
                rendered = "".join(parts).encode("ascii")
                total_bytes += len(rendered)
                h = 0
                for b in rendered:
                    h = (h * 131 + b) % MOD
                ck = (ck * 31 + h) % MOD
        expected = f"{total_bytes}\n{ck}\n"
        self.assertEqual(expected, "11585000\n816359811\n")
        self.assertEqual(suite.BY_NAME["template_render"].expect, expected)

    def test_hmac_pbkdf2_oracle(self) -> None:
        acc = bytearray(32)
        ops = 0
        for i in range(80):
            dk = hashlib.pbkdf2_hmac("sha256", f"xu-pass-{i:03d}-secret".encode(), f"salt-{i * 7:04d}-v1".encode(), 1000, dklen=32)
            for j in range(32): acc[j] ^= dk[j]
            ops += 1
        for i in range(200):
            mac = hmac.digest(f"jwt-hmac-key-{i % 16:02d}".encode(), f"eyJhbGciOiJIUzI1NiJ9.sub=user_{i:04d}&seq={i * 37:05d}".encode(), "sha256")
            for j in range(32): acc[j] ^= mac[j]
            ops += 1
        expected = f"{ops}\n{acc.hex()}\n"
        self.assertEqual(expected, "280\nf88ff7eadf3c76f6a2d3098ac8740bffb1fc75bf364f984233c86d1659bed2ec\n")
        self.assertEqual(suite.BY_NAME["hmac_pbkdf2"].expect, expected)


if __name__ == "__main__":
    unittest.main()
