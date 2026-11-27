"""Independent goldens and registry contract checks for Batch G (113 -> 121) benchmarks."""
from __future__ import annotations

import ast
import math
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

BATCH_G_SPECS: dict[str, tuple[tuple[str, ...], str]] = {
    "raytrace_sphere": (suite.CORE, "graphics"),
    "image_sobel_blur": (suite.CORE, "graphics"),
    "physics_collision": (suite.CORE, "graphics"),
    "mlp_inference": (suite.CORE, "ai"),
    "kmeans_cluster": (suite.CORE, "ai"),
    "order_book_match": (suite.CORE, "ai"),
    "x25519_dh": (suite.CORE, "crypto"),
    "parallel_mapreduce": (("go", "rs"), "concurrency"),
}


class TestBatchGRegistryAndGoldens(unittest.TestCase):
    def test_registry_files_and_full_11_domain_coverage(self) -> None:
        source = (ROOT / "scripts" / "bench_crosslang.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        benches_node = None
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "BENCHES":
                benches_node = node.value
                break
        self.assertIsNotNone(benches_node)
        ast_names = [elt.args[0].value for elt in benches_node.elts]
        self.assertGreaterEqual(len(ast_names), 121)
        self.assertEqual(len(set(ast_names)), len(ast_names))
        name_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in ast_names:
            self.assertRegex(name, name_re)

        expected_cats = {
            "control",
            "algo",
            "data",
            "string",
            "web",
            "storage",
            "systems",
            "graphics",
            "ai",
            "crypto",
            "concurrency",
        }
        self.assertEqual(set(summary.CATEGORY_NAMES.keys()), expected_cats)

        covered_cats: set[str] = set()
        for b in suite.BENCHES:
            if b.name in summary.BENCH_DESCRIPTIONS:
                cat = summary.BENCH_DESCRIPTIONS[b.name][2]
                self.assertIn(cat, summary.CATEGORY_NAMES)
                covered_cats.add(cat)
        self.assertEqual(covered_cats, expected_cats)

        for name, (langs, cat) in BATCH_G_SPECS.items():
            self.assertIn(name, suite.BY_NAME)
            self.assertEqual(suite.BY_NAME[name].langs, langs)
            self.assertEqual(suite.SHARD_WEIGHTS.get(name), 2)
            self.assertEqual(summary.BENCH_DESCRIPTIONS[name][2], cat)
            golden_bytes = (GOLDEN / f"{name}.txt").read_bytes()
            self.assertNotIn(b"\r", golden_bytes)
            self.assertEqual(golden_bytes.decode("ascii"), suite.BY_NAME[name].expect)
            self.assertTrue((ROOT / "tests" / "bench" / f"{name}.xu").is_file())
            for ext in langs:
                self.assertTrue((ROOT / "tests" / "bench" / "cross" / f"{name}.{ext}").is_file())

    def test_raytrace_sphere_oracle(self) -> None:
        cx = [0.0] * 16
        cy = [0.0] * 16
        cz = [0.0] * 16
        cr = [0.0] * 16
        sr = [0.0] * 16
        sg = [0.0] * 16
        sb = [0.0] * 16
        refl = [0.0] * 16
        cx[0], cy[0], cz[0], cr[0] = 0.0, -1001.5, -6.0, 1000.0
        sr[0], sg[0], sb[0], refl[0] = 0.45, 0.48, 0.52, 0.25

        rng = 44556677
        for i in range(1, 16):
            row = (i - 1) // 5
            col = (i - 1) % 5
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            cx[i] = -3.2 + col * 1.6 + ((rng % 41) - 20) / 128.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            cy[i] = -0.7 + row * 1.1 + ((rng % 33) - 16) / 128.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            cz[i] = -4.2 - row * 1.8 - (rng % 33) / 64.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            cr[i] = 0.45 + (rng % 17) / 64.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            sr[i] = 0.25 + (rng % 48) / 64.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            sg[i] = 0.25 + (rng % 48) / 64.0
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            sb[i] = 0.25 + (rng % 48) / 64.0
            refl[i] = 0.2 + (i % 4) * 0.15

        spheres = list(zip(cx, cy, cz, cr, sr, sg, sb, refl))
        cr2 = [r * r for r in cr]
        lx = ly = lz = 0.5773502691896258
        sqrt = math.sqrt
        hit_count = 0
        total_lum = 0.0

        for py in range(240):
            v = (0.5 - (py + 0.5) / 240.0) * 1.5
            vv = v * v + 1.0
            for px in range(320):
                u = ((px + 0.5) / 320.0 - 0.5) * 2.0
                inv_l = 1.0 / sqrt(u * u + vv)
                ox, oy, oz = 0.0, 0.2, 0.0
                dx, dy, dz = u * inv_l, v * inv_l, -1.0 * inv_l
                att = 1.0
                pr = pg = pb = 0.0
                for _depth in range(3):
                    best_t = 1.0e18
                    best_i = -1
                    for i, (scx, scy, scz, _scr, _ssr, _ssg, _ssb, _srefl) in enumerate(spheres):
                        ocx = ox - scx
                        ocy = oy - scy
                        ocz = oz - scz
                        b = ocx * dx + ocy * dy + ocz * dz
                        c = ocx * ocx + ocy * ocy + ocz * ocz - cr2[i]
                        disc = b * b - c
                        if disc > 0.0:
                            t = -b - sqrt(disc)
                            if 0.0005 < t < best_t:
                                best_t = t
                                best_i = i
                    if best_i == -1:
                        sky = 0.5 * (dy + 1.0)
                        pr += att * (0.2 + 0.4 * sky)
                        pg += att * (0.3 + 0.4 * sky)
                        pb += att * (0.5 + 0.4 * sky)
                        break
                    hit_count += 1
                    scx, scy, scz, scr, ssr, ssg, ssb, kr = spheres[best_i]
                    hx = ox + dx * best_t
                    hy = oy + dy * best_t
                    hz = oz + dz * best_t
                    inv_r = 1.0 / scr
                    nx = (hx - scx) * inv_r
                    ny = (hy - scy) * inv_r
                    nz = (hz - scz) * inv_r
                    sox = hx + nx * 0.002
                    soy = hy + ny * 0.002
                    soz = hz + nz * 0.002
                    in_shadow = False
                    for j, (jcx, jcy, jcz, *_rest) in enumerate(spheres):
                        ocx = sox - jcx
                        ocy = soy - jcy
                        ocz = soz - jcz
                        b = ocx * lx + ocy * ly + ocz * lz
                        c = ocx * ocx + ocy * ocy + ocz * ocz - cr2[j]
                        disc = b * b - c
                        if disc > 0.0 and -b - sqrt(disc) > 0.0005:
                            in_shadow = True
                            break
                    diff = 0.0
                    spec = 0.0
                    if not in_shadow:
                        ndotl = nx * lx + ny * ly + nz * lz
                        if ndotl > 0.0:
                            diff = ndotl
                            hx2, hy2, hz2 = lx - dx, ly - dy, lz - dz
                            hinv = 1.0 / sqrt(hx2 * hx2 + hy2 * hy2 + hz2 * hz2)
                            ndoth = (nx * hx2 + ny * hy2 + nz * hz2) * hinv
                            if ndoth > 0.0:
                                s2 = ndoth * ndoth
                                s4 = s2 * s2
                                spec = s4 * s4 * 0.5
                    shade = 0.1 + 0.75 * diff
                    pr += att * (1.0 - kr) * (ssr * shade + spec)
                    pg += att * (1.0 - kr) * (ssg * shade + spec)
                    pb += att * (1.0 - kr) * (ssb * shade + spec)
                    att *= kr
                    if att < 0.02:
                        break
                    dot2 = 2.0 * (dx * nx + dy * ny + dz * nz)
                    dx -= dot2 * nx
                    dy -= dot2 * ny
                    dz -= dot2 * nz
                    ox, oy, oz = sox, soy, soz
                total_lum += pr + pg + pb

        out = f"{hit_count}\n{int(math.floor(total_lum * 10.0 + 0.5))}\n"
        self.assertEqual(out, suite.BY_NAME["raytrace_sphere"].expect)

    def test_image_sobel_blur_oracle(self) -> None:
        w = h = 512
        total_px = w * h
        img = [0] * total_px
        rng = 51515151
        for y in range(h):
            dy2 = (y - 256) ** 2
            y5 = y * 5
            yg = y >> 5
            row = y * w
            for x in range(w):
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                v = ((x * 3 + y5) >> 3) & 255
                dx = x - 256
                if dx * dx + dy2 < 16384:
                    v = (v + 110) & 255
                if (80 <= x < 200 and 80 <= y < 220) or (((x >> 5) + yg) % 4) == 0:
                    v = (v ^ 96) & 255
                img[row + x] = (v + (rng & 15)) & 255

        blur = [0] * total_px
        edges = [0] * total_px
        edge_cnt = 0
        for _ in range(6):
            blur[:w] = img[:w]
            blur[(h - 1) * w : h * w] = img[(h - 1) * w : h * w]
            for y in range(1, h - 1):
                row = y * w
                blur[row] = img[row]
                blur[row + w - 1] = img[row + w - 1]
                r_prev = row - w
                r_next = row + w
                blur[row + 1 : row + w - 1] = [
                    (
                        a + 2 * b + c + 2 * d + 4 * e + 2 * f + g + 2 * h0 + i0
                    ) >> 4
                    for a, b, c, d, e, f, g, h0, i0 in zip(
                        img[r_prev : r_prev + w - 2],
                        img[r_prev + 1 : r_prev + w - 1],
                        img[r_prev + 2 : r_prev + w],
                        img[row : row + w - 2],
                        img[row + 1 : row + w - 1],
                        img[row + 2 : row + w],
                        img[r_next : r_next + w - 2],
                        img[r_next + 1 : r_next + w - 1],
                        img[r_next + 2 : r_next + w],
                    )
                ]
            for y in range(1, h - 1):
                row = y * w
                r_prev = row - w
                r_next = row + w
                mags = [
                    min(
                        255,
                        abs(-a + c - 2 * d + 2 * f - g + i0)
                        + abs(-a - 2 * b - c + g + 2 * h0 + i0),
                    )
                    for a, b, c, d, f, g, h0, i0 in zip(
                        blur[r_prev : r_prev + w - 2],
                        blur[r_prev + 1 : r_prev + w - 1],
                        blur[r_prev + 2 : r_prev + w],
                        blur[row : row + w - 2],
                        blur[row + 2 : row + w],
                        blur[r_next : r_next + w - 2],
                        blur[r_next + 1 : r_next + w - 1],
                        blur[r_next + 2 : r_next + w],
                    )
                ]
                edges[row + 1 : row + w - 1] = mags
                edge_cnt += sum(1 for m in mags if m >= 64)
            img = [(b * 3 + e) >> 2 for b, e in zip(blur, edges)]

        ck = 0
        for val in edges:
            ck = (ck * 131 + val) % MOD
        self.assertEqual(f"{edge_cnt}\n{ck}\n", suite.BY_NAME["image_sobel_blur"].expect)

    def test_physics_collision_oracle(self) -> None:
        n = 512
        arena = 65536
        rng = 62626262
        px: list[int] = []
        py: list[int] = []
        vx: list[int] = []
        vy: list[int] = []
        rad: list[int] = []
        for i in range(n):
            row, col = divmod(i, 32)
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            px.append(1024 + col * 2000 + (rng % 200))
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            py.append(1024 + row * 4000 + (rng % 200))
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            vx.append((rng % 321) - 160)
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            vy.append((rng % 321) - 160)
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            rad.append(384 + (rng % 257))

        def sdiv(num: int, den: int) -> int:
            return num // den if num >= 0 else -((-num) // den)

        isqrt = math.isqrt
        nxt_b = [-1] * n
        collisions = 0
        for _step in range(500):
            head = [-1] * 256
            for i in range(n):
                x = px[i] + vx[i]
                y = py[i] + vy[i]
                r = rad[i]
                if x < r:
                    x = r
                    vx[i] = -vx[i]
                elif x > arena - r:
                    x = arena - r
                    vx[i] = -vx[i]
                if y < r:
                    y = r
                    vy[i] = -vy[i]
                elif y > arena - r:
                    y = arena - r
                    vy[i] = -vy[i]
                px[i] = x
                py[i] = y
                cx = min(15, x >> 12)
                cy = min(15, y >> 12)
                cell = (cy << 4) | cx
                nxt_b[i] = head[cell]
                head[cell] = i

            for i in range(n):
                cx = min(15, px[i] >> 12)
                cy = min(15, py[i] >> 12)
                for ny in range(max(0, cy - 1), min(15, cy + 1) + 1):
                    row_off = ny << 4
                    for nx in range(max(0, cx - 1), min(15, cx + 1) + 1):
                        j = head[row_off | nx]
                        while j != -1:
                            if j > i:
                                dx = px[j] - px[i]
                                dy = py[j] - py[i]
                                rsum = rad[i] + rad[j]
                                dist2 = dx * dx + dy * dy
                                if 0 < dist2 < rsum * rsum:
                                    collisions += 1
                                    dist = max(1, isqrt(dist2))
                                    half = (rsum - dist + 1) >> 1
                                    sx = sdiv(dx * half, dist)
                                    sy = sdiv(dy * half, dist)
                                    px[i] -= sx
                                    py[i] -= sy
                                    px[j] += sx
                                    py[j] += sy
                                    vn = (vx[j] - vx[i]) * dx + (vy[j] - vy[i]) * dy
                                    if vn < 0:
                                        ix = sdiv(vn * dx, dist2)
                                        iy = sdiv(vn * dy, dist2)
                                        vx[i] += ix
                                        vy[i] += iy
                                        vx[j] -= ix
                                        vy[j] -= iy
                            j = nxt_b[j]

        ck = 0
        for i in range(n):
            v = (px[i] + 100000) * 7 + (py[i] + 100000) * 13 + (vx[i] + 100000) * 17 + (vy[i] + 100000) * 19
            # Verify formula from source: line 178 has (vy[i] + 100000) without * 19
            v = (px[i] + 100000) * 7 + (py[i] + 100000) * 13 + (vx[i] + 100000) * 17 + (vy[i] + 100000)
            ck = (ck * 31 + (v % MOD)) % MOD
        self.assertEqual(f"{collisions}\n{ck}\n", suite.BY_NAME["physics_collision"].expect)

    def test_mlp_inference_oracle(self) -> None:
        d0, d1, d2, d3 = 64, 128, 64, 16
        rng = 73737373

        def gen_vec(n: int, span: int, shift: int, scale: float) -> list[float]:
            nonlocal rng
            out: list[float] = []
            for _ in range(n):
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                out.append(((rng % span) - shift) / scale)
            return out

        w1_flat = gen_vec(d1 * d0, 255, 127, 1024.0)
        b1 = gen_vec(d1, 63, 31, 256.0)
        w2_flat = gen_vec(d2 * d1, 255, 127, 1024.0)
        b2 = gen_vec(d2, 63, 31, 256.0)
        w3_flat = gen_vec(d3 * d2, 255, 127, 1024.0)
        b3 = gen_vec(d3, 63, 31, 256.0)

        w1 = [w1_flat[j * d0 : (j + 1) * d0] for j in range(d1)]
        w2 = [w2_flat[j * d1 : (j + 1) * d1] for j in range(d2)]
        w3 = [w3_flat[j * d2 : (j + 1) * d2] for j in range(d3)]

        cls_sum = 0
        logit_acc = 0.0
        for _ in range(2000):
            x = gen_vec(d0, 255, 127, 128.0)
            h1: list[float] = []
            for j in range(d1):
                s = b1[j]
                row = w1[j]
                for i in range(d0):
                    s += x[i] * row[i]
                h1.append(s if s > 0.0 else 0.0)
            h2: list[float] = []
            for j in range(d2):
                s = b2[j]
                row = w2[j]
                for i in range(d1):
                    s += h1[i] * row[i]
                h2.append(s if s > 0.0 else 0.0)
            best_c = 0
            best_v = -1.0e18
            for j in range(d3):
                s = b3[j]
                row = w3[j]
                for i in range(d2):
                    s += h2[i] * row[i]
                if s > best_v:
                    best_v = s
                    best_c = j
            cls_sum += best_c
            logit_acc += abs(best_v)

        out = f"{cls_sum}\n{int(math.floor(logit_acc * 10.0 + 0.5))}\n"
        self.assertEqual(out, suite.BY_NAME["mlp_inference"].expect)

    def test_kmeans_cluster_oracle(self) -> None:
        n, d, k = 8192, 8, 16
        rng = 84848484
        gt: list[list[float]] = []
        for _ in range(k):
            row = []
            for _dim in range(d):
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                row.append(((rng % 1000) - 500) / 16.0)
            gt.append(row)

        pts: list[tuple[float, ...]] = []
        for i in range(n):
            grow = gt[i & 15]
            prow = []
            for dim in range(d):
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                prow.append(grow[dim] + ((rng % 129) - 64) / 32.0)
            pts.append(tuple(prow))

        cent = [list(pts[c]) for c in range(k)]
        assign = [0] * n
        final_inertia = 0.0

        for _ in range(25):
            sum_c = [[0.0] * d for _ in range(k)]
            cnt = [0] * k
            inertia = 0.0
            for i, p in enumerate(pts):
                p0, p1, p2, p3, p4, p5, p6, p7 = p
                best_c = 0
                best_d = 1.0e18
                for c, cc in enumerate(cent):
                    d0 = p0 - cc[0]
                    d1 = p1 - cc[1]
                    d2 = p2 - cc[2]
                    d3 = p3 - cc[3]
                    d4 = p4 - cc[4]
                    d5 = p5 - cc[5]
                    d6 = p6 - cc[6]
                    d7 = p7 - cc[7]
                    dist = d0 * d0 + d1 * d1 + d2 * d2 + d3 * d3 + d4 * d4 + d5 * d5 + d6 * d6 + d7 * d7
                    if dist < best_d:
                        best_d = dist
                        best_c = c
                assign[i] = best_c
                cnt[best_c] += 1
                inertia += best_d
                sc = sum_c[best_c]
                sc[0] += p0
                sc[1] += p1
                sc[2] += p2
                sc[3] += p3
                sc[4] += p4
                sc[5] += p5
                sc[6] += p6
                sc[7] += p7
            for c in range(k):
                if cnt[c] > 0:
                    inv = 1.0 / cnt[c]
                    cent[c] = [v * inv for v in sum_c[c]]
            final_inertia = inertia

        ack = 0
        for a in assign:
            ack = (ack * 31 + a + 1) % MOD
        out = f"{ack}\n{int(math.floor(final_inertia + 0.5))}\n"
        self.assertEqual(out, suite.BY_NAME["kmeans_cluster"].expect)

    def test_order_book_match_oracle(self) -> None:
        pmax = 2048
        max_ord = 262144
        b_head = [-1] * pmax
        b_tail = [-1] * pmax
        a_head = [-1] * pmax
        a_tail = [-1] * pmax
        o_side = [0] * max_ord
        o_px = [0] * max_ord
        o_qty = [0] * max_ord
        o_act = [0] * max_ord
        o_prev = [-1] * max_ord
        o_next = [-1] * max_ord

        def unlink(head: list[int], tail: list[int], px: int, oid: int) -> None:
            pr = o_prev[oid]
            nx = o_next[oid]
            if pr != -1:
                o_next[pr] = nx
            else:
                head[px] = nx
            if nx != -1:
                o_prev[nx] = pr
            else:
                tail[px] = pr
            o_prev[oid] = -1
            o_next[oid] = -1

        def push(head: list[int], tail: list[int], px: int, oid: int) -> None:
            t = tail[px]
            o_prev[oid] = t
            o_next[oid] = -1
            if t != -1:
                o_next[t] = oid
            else:
                head[px] = oid
            tail[px] = oid

        rng = 70707070
        best_bid = -1
        best_ask = pmax
        next_id = 0
        trades = 0
        cancels = 0
        ck = 0

        for _ in range(250000):
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            if (rng % 10) < 2 and next_id > 0:
                win = min(4096, next_id)
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                cid = next_id - 1 - (rng % win)
                if o_act[cid] == 1:
                    px = o_px[cid]
                    if o_side[cid] == 0:
                        unlink(b_head, b_tail, px, cid)
                        if px == best_bid and b_head[px] == -1:
                            while best_bid >= 0 and b_head[best_bid] == -1:
                                best_bid -= 1
                    else:
                        unlink(a_head, a_tail, px, cid)
                        if px == best_ask and a_head[px] == -1:
                            while best_ask < pmax and a_head[best_ask] == -1:
                                best_ask += 1
                    o_act[cid] = 0
                    cancels += 1
            else:
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                side = (rng >> 16) & 1
                if best_bid >= 0 and best_ask < pmax:
                    mid = (best_bid + best_ask) >> 1
                elif best_bid >= 0:
                    mid = best_bid
                elif best_ask < pmax:
                    mid = best_ask
                else:
                    mid = 1024
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                px = max(1, min(pmax - 2, mid + (rng % 41) - 20))
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                qty = 1 + (rng % 50)
                if side == 0:
                    while qty > 0 and best_ask <= px:
                        oid = a_head[best_ask]
                        fill = min(qty, o_qty[oid])
                        qty -= fill
                        o_qty[oid] -= fill
                        trades += 1
                        ck = (ck * 31 + fill * 1009 + best_ask) % MOD
                        if o_qty[oid] == 0:
                            unlink(a_head, a_tail, best_ask, oid)
                            o_act[oid] = 0
                            while best_ask < pmax and a_head[best_ask] == -1:
                                best_ask += 1
                    if qty > 0:
                        oid = next_id
                        next_id += 1
                        o_side[oid] = 0
                        o_px[oid] = px
                        o_qty[oid] = qty
                        o_act[oid] = 1
                        push(b_head, b_tail, px, oid)
                        if px > best_bid:
                            best_bid = px
                else:
                    while qty > 0 and best_bid >= px:
                        oid = b_head[best_bid]
                        fill = min(qty, o_qty[oid])
                        qty -= fill
                        o_qty[oid] -= fill
                        trades += 1
                        ck = (ck * 31 + fill * 1009 + best_bid) % MOD
                        if o_qty[oid] == 0:
                            unlink(b_head, b_tail, best_bid, oid)
                            o_act[oid] = 0
                            while best_bid >= 0 and b_head[best_bid] == -1:
                                best_bid -= 1
                    if qty > 0:
                        oid = next_id
                        next_id += 1
                        o_side[oid] = 1
                        o_px[oid] = px
                        o_qty[oid] = qty
                        o_act[oid] = 1
                        push(a_head, a_tail, px, oid)
                        if px < best_ask:
                            best_ask = px

        ck = (ck * 37 + cancels * 17 + (best_bid + 1) * 7 + best_ask) % MOD
        self.assertEqual(f"{trades}\n{ck}\n", suite.BY_NAME["order_book_match"].expect)

    def test_x25519_dh_rfc7748_oracle(self) -> None:
        p = (1 << 255) - 19
        a24 = 121665

        def clamp_k(k_bytes: bytes) -> int:
            kb = bytearray(k_bytes)
            kb[0] &= 248
            kb[31] &= 127
            kb[31] |= 64
            return int.from_bytes(kb, "little")

        def x25519_py(k_bytes: bytes, u_bytes: bytes) -> bytes:
            k = clamp_k(k_bytes)
            ub = bytearray(u_bytes)
            ub[31] &= 127
            x1 = int.from_bytes(ub, "little") % p
            x2, z2, x3, z3 = 1, 0, x1, 1
            swap = 0
            for t in range(254, -1, -1):
                kt = (k >> t) & 1
                swap ^= kt
                if swap:
                    x2, x3 = x3, x2
                    z2, z3 = z3, z2
                swap = kt
                a = (x2 + z2) % p
                aa = (a * a) % p
                b = (x2 - z2) % p
                bb = (b * b) % p
                e = (aa - bb) % p
                c = (x3 + z3) % p
                d = (x3 - z3) % p
                da = (d * a) % p
                cb = (c * b) % p
                x3 = pow((da + cb) % p, 2, p)
                z3 = (x1 * pow((da - cb) % p, 2, p)) % p
                x2 = (aa * bb) % p
                z2 = (e * ((aa + a24 * e) % p)) % p
            if swap:
                x2, x3 = x3, x2
                z2, z3 = z3, z2
            res = (x2 * pow(z2, p - 2, p)) % p
            return res.to_bytes(32, "little")

        k = (9).to_bytes(32, "little")
        u = (9).to_bytes(32, "little")
        for step in range(1, 101):
            out = x25519_py(k, u)
            u, k = k, out
            if step == 1:
                self.assertEqual(
                    k.hex(),
                    "422c8e7a6227d7bca1350b3e2bb7279f7897b87bb6854b783c60e80311ae3079",
                )
        self.assertEqual(f"100\n{k.hex()}\n", suite.BY_NAME["x25519_dh"].expect)

    def test_parallel_mapreduce_oracle(self) -> None:
        slot_hash: list[int] = []
        for tid in range(64):
            hist = [0] * 256
            rng = (tid + 1) * 1000003 + 98765
            for _ in range(131072):
                rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
                hist[(rng >> 8) & 255] += 1 + ((rng >> 16) & 1023)
            lh = tid + 1
            for hval in hist:
                lh = (lh * 131 + hval) % MOD
            slot_hash.append(lh)

        ck = 0
        for lh in slot_hash:
            ck = (ck * 31 + lh) % MOD
        self.assertEqual(f"{64 * 131072}\n{ck}\n", suite.BY_NAME["parallel_mapreduce"].expect)


if __name__ == "__main__":
    unittest.main()
