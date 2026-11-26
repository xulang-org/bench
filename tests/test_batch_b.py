"""Independent goldens and registry contract checks for Batch B benchmarks."""
from __future__ import annotations

import ast
import bisect
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402

GOLDEN = ROOT / "tests" / "bench" / "golden"

BATCH_B_LANGS = {
    "plb2_nqueen": suite.CORE,
    "plb2_sudoku": suite.CORE,
    "plb2_bedcov": suite.CORE,
    "thread_ring": ("go", "rs"),
    "skynet": ("go",),
    "scimark_montecarlo": suite.CORE,
    "scimark_sor": suite.CORE,
    "scimark_lu": suite.CORE,
    "scimark_sparse": suite.CORE,
    "scimark_fft": suite.CORE,
}

SUDOKU_PUZZLES = (
    "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
    "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3..",
    "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......",
    "52...6.........7.13...........4..8..6......5...........418.........3..2...87.....",
    "6.....8.3.4.7.................5.4.7.3..2.....1.6.......2.....5.....8.6......1....",
    "48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5....",
    "....14....3....2...7..........9...3.6.1.............8.2.....1.4....5.6.....7.8...",
    "......52..8.4......3...9...5.1...6..2..7........3.....6...1..........7.4.......3.",
    "6.2.5.........3.4..........43...8....1....2........7..5..27...........81...6.....",
    "1....7.9..3..2...8..96..5....53..9...1..8...26....4...3......1..4......7..7...3..",
)


def _lcg(seed: int) -> int:
    return (seed * 1103515245 + 12345) & 2147483647


def _solve_unique_sudoku(puzzle: str) -> list[int]:
    grid = [0 if ch == "." else int(ch) for ch in puzzle]
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    empties = []
    for idx, v in enumerate(grid):
        r, c = divmod(idx, 9)
        b = (r // 3) * 3 + (c // 3)
        if v:
            bit = 1 << v
            if (rows[r] & bit) or (cols[c] & bit) or (boxes[b] & bit):
                raise AssertionError("invalid clues")
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
        else:
            empties.append(idx)

    sols: list[list[int]] = []

    def dfs() -> None:
        if len(sols) >= 2:
            return
        best_i, best_mask, best_cnt = -1, 0, 10
        for idx in empties:
            if grid[idx] != 0:
                continue
            r, c = divmod(idx, 9)
            b = (r // 3) * 3 + (c // 3)
            avail = (~(rows[r] | cols[c] | boxes[b])) & 0x3FE
            cnt = avail.bit_count()
            if cnt == 0:
                return
            if cnt < best_cnt:
                best_cnt, best_i, best_mask = cnt, idx, avail
                if cnt == 1:
                    break
        if best_i == -1:
            sols.append(list(grid))
            return
        r, c = divmod(best_i, 9)
        b = (r // 3) * 3 + (c // 3)
        m = best_mask
        while m:
            bit = m & -m
            m -= bit
            d = bit.bit_length() - 1
            grid[best_i] = d
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            dfs()
            grid[best_i] = 0
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
            if len(sols) >= 2:
                return

    dfs()
    if len(sols) != 1:
        raise AssertionError(f"expected unique solution, got {len(sols)}")
    sol = sols[0]
    digits = set(range(1, 10))
    for r in range(9):
        if set(sol[r * 9 : (r + 1) * 9]) != digits:
            raise AssertionError("row invalid")
    for c in range(9):
        if {sol[r * 9 + c] for r in range(9)} != digits:
            raise AssertionError("col invalid")
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            if {sol[(br + dr) * 9 + (bc + dc)] for dr in range(3) for dc in range(3)} != digits:
                raise AssertionError("box invalid")
    return sol


class _SciRandom:
    M1 = 2147483647
    M2 = 65536
    DM1 = 1.0 / 2147483647.0

    def __init__(self, seed: int) -> None:
        self.m = [0] * 17
        jseed = min(abs(seed), self.M1)
        if jseed % 2 == 0:
            jseed -= 1
        k0 = 9069 % self.M2
        k1 = 9069 // self.M2
        j0 = jseed % self.M2
        j1 = jseed // self.M2
        for iloop in range(17):
            jseed = j0 * k0
            j1 = (jseed // self.M2 + j0 * k1 + j1 * k0) % (self.M2 // 2)
            j0 = jseed % self.M2
            self.m[iloop] = j0 + self.M2 * j1
        self.i = 4
        self.j = 16

    def next_double(self) -> float:
        k = self.m[self.i] - self.m[self.j]
        if k < 0:
            k += self.M1
        self.m[self.j] = k
        self.i = 16 if self.i == 0 else self.i - 1
        self.j = 16 if self.j == 0 else self.j - 1
        return self.DM1 * float(k)


def _check_bench_golden(tc: unittest.TestCase, name: str, expected: str) -> None:
    tc.assertEqual(suite.BY_NAME[name].expect, expected)
    tc.assertEqual((GOLDEN / f"{name}.txt").read_text(encoding="utf-8"), expected)


class BatchBTests(unittest.TestCase):
    def test_batch_b_registry_ports_and_descriptions(self):
        for name, langs in BATCH_B_LANGS.items():
            with self.subTest(bench=name):
                self.assertIn(name, suite.BY_NAME)
                self.assertEqual(suite.BY_NAME[name].langs, langs)
                xu_path = suite.xu_src(name)
                self.assertTrue(xu_path.is_file(), xu_path)
                self.assertEqual(xu_path.read_text(encoding="utf-8").splitlines()[0], "@main")
                for ext in langs:
                    peer = suite.cross_src(name, ext)
                    self.assertTrue(peer.is_file(), peer)
                self.assertIn(name, summary.BENCH_DESCRIPTIONS)
                _zh, _en, cat = summary.BENCH_DESCRIPTIONS[name]
                self.assertIn(cat, summary.CATEGORY_NAMES)

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
        names = [ast.literal_eval(item.args[0]) for item in values[0].elts]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 87)

    def test_plb2_nqueen_reference(self):
        # Verify recursive solver matches OEIS A000170 up to N=11 and lock N=15 golden.
        def solve_rec(cols: int, d1: int, d2: int, full: int) -> int:
            if cols == full:
                return 1
            total = 0
            avail = full ^ (cols | d1 | d2)
            while avail:
                bit = avail & -avail
                avail -= bit
                total += solve_rec(cols | bit, ((d1 | bit) << 1) & full, (d2 | bit) >> 1, full)
            return total

        oeis = {8: 92, 9: 352, 10: 724, 11: 2680}
        for n, want in oeis.items():
            self.assertEqual(solve_rec(0, 0, 0, (1 << n) - 1), want)
        _check_bench_golden(self, "plb2_nqueen", "2279184\n")

    def test_plb2_sudoku_unique_solutions_and_golden(self):
        sols = [_solve_unique_sudoku(p) for p in SUDOKU_PUZZLES]
        chk = 0
        for _ in range(20):
            for sol in sols:
                for d in sol:
                    chk = (chk * 31 + d) % 1000000007
        _check_bench_golden(self, "plb2_sudoku", f"{chk}\n")

    def test_plb2_bedcov_sweep_oracle_and_golden(self):
        seed = 123456789
        st, en = [], []
        cur_st = 0
        for _ in range(200_000):
            seed = _lcg(seed)
            cur_st += seed % 100
            seed = _lcg(seed)
            ln = 1 + (seed % 5000)
            st.append(cur_st)
            en.append(cur_st + ln)
        max_coord = cur_st + 1
        hits = cov_sum = 0
        for _ in range(200_000):
            seed = _lcg(seed)
            qs = seed % max_coord
            seed = _lcg(seed)
            qe = qs + 1 + (seed % 5000)
            lo = bisect.bisect_left(st, qs - 5000)
            hi = bisect.bisect_left(st, qe)
            for i in range(lo, hi):
                if qs < en[i]:
                    hits += 1
                    cov_sum += min(en[i], qe) - max(st[i], qs)
        _check_bench_golden(self, "plb2_bedcov", f"{hits}\n{cov_sum}\n")

    def test_concurrency_closed_form_goldens(self):
        _check_bench_golden(self, "thread_ring", f"{(100000 % 503) + 1}\n")
        _check_bench_golden(self, "skynet", f"{2 * (1000 * 999 // 2)}\n")

    def test_scimark_montecarlo_reference(self):
        rng = _SciRandom(113)
        under = 0
        for _ in range(5_000_000):
            x = rng.next_double()
            y = rng.next_double()
            if x * x + y * y <= 1.0:
                under += 1
        _check_bench_golden(self, "scimark_montecarlo", f"{under}\n")

    def test_scimark_sor_sparse_lu_fft_references_and_margins(self):
        # SOR
        rng = _SciRandom(101010)
        n = 100
        g = [rng.next_double() for _ in range(n * n)]
        oof = 1.25 * 0.25
        omw = 1.0 - 1.25
        for _ in range(500):
            for i in range(1, n - 1):
                row, up, dn = i * n, (i - 1) * n, (i + 1) * n
                for j in range(1, n - 1):
                    g[row + j] = oof * (g[up + j] + g[dn + j] + g[row + j - 1] + g[row + j + 1]) + omw * g[row + j]
        sor_sum = sum(g)
        self.assertLess(abs(sor_sum * 1000.0 - round(sor_sum * 1000.0)), 0.30)
        _check_bench_golden(self, "scimark_sor", f"{math.floor(sor_sum * 1000.0 + 0.5)}\n")

        # Sparse
        rng = _SciRandom(101010)
        ns, nz, nr = 10000, 50000, 5
        x_sp = [rng.next_double() for _ in range(ns)]
        val_sp = [rng.next_double() for _ in range(nz)]
        row_sp = [0] * (ns + 1)
        col_sp = [0] * nz
        for r in range(ns):
            row_sp[r + 1] = row_sp[r] + nr
            step = max(1, r // nr)
            rr = row_sp[r]
            for j in range(nr):
                col_sp[rr + j] = (j * step) % ns
        y_sp = [0.0] * ns
        acc_sp = 0.0
        for rep in range(500):
            for r in range(ns):
                y_sp[r] = sum(x_sp[col_sp[i]] * val_sp[i] for i in range(row_sp[r], row_sp[r + 1]))
            acc_sp += y_sp[rep % ns]
        sp_total = acc_sp + sum(y_sp)
        self.assertLess(abs(sp_total * 1000.0 - round(sp_total * 1000.0)), 0.30)
        _check_bench_golden(self, "scimark_sparse", f"{math.floor(sp_total * 1000.0 + 0.5)}\n")

        # LU
        rng = _SciRandom(101010)
        a0 = [rng.next_double() for _ in range(n * n)]
        lu_acc = 0.0
        piv_chk = 0
        for _ in range(30):
            a = list(a0)
            piv = [0] * n
            for j in range(n):
                jp = max(range(j, n), key=lambda i: abs(a[i * n + j]))
                piv[j] = jp
                if jp != j:
                    for k in range(n):
                        a[j * n + k], a[jp * n + k] = a[jp * n + k], a[j * n + k]
                if j < n - 1:
                    recp = 1.0 / a[j * n + j]
                    for k in range(j + 1, n):
                        a[k * n + j] *= recp
                    for ii in range(j + 1, n):
                        aii = a[ii * n + j]
                        for jj in range(j + 1, n):
                            a[ii * n + jj] -= aii * a[j * n + jj]
            lu_acc += sum(abs(v) for v in a)
            piv_chk = (piv_chk + sum(piv)) % 1000000007
        self.assertLess(abs(lu_acc * 100.0 - round(lu_acc * 100.0)), 0.30)
        _check_bench_golden(self, "scimark_lu", f"{math.floor(lu_acc * 100.0 + 0.5) + piv_chk}\n")

        # FFT
        rng = _SciRandom(101010)
        nf = 1024
        orig = [rng.next_double() for _ in range(2 * nf)]

        def fft(data: list[float], direction: float) -> None:
            j = 0
            for i in range(nf - 1):
                if i < j:
                    ii, jj = 2 * i, 2 * j
                    data[ii], data[jj] = data[jj], data[ii]
                    data[ii + 1], data[jj + 1] = data[jj + 1], data[ii + 1]
                k = nf >> 1
                while k <= j:
                    j -= k
                    k >>= 1
                j += k
            dual = 1
            for _ in range(10):
                w_real, w_imag = 1.0, 0.0
                theta = 2.0 * direction * math.pi / (2.0 * dual)
                s = math.sin(theta)
                t = math.sin(theta * 0.5)
                s2 = 2.0 * t * t
                for b in range(0, nf, 2 * dual):
                    i, j = 2 * b, 2 * (b + dual)
                    wr, wi = data[j], data[j + 1]
                    data[j], data[j + 1] = data[i] - wr, data[i + 1] - wi
                    data[i] += wr
                    data[i + 1] += wi
                for a in range(1, dual):
                    w_real, w_imag = w_real - s * w_imag - s2 * w_real, w_imag + s * w_real - s2 * w_imag
                    for b in range(0, nf, 2 * dual):
                        i, j = 2 * (b + a), 2 * (b + a + dual)
                        zr, zi = data[j], data[j + 1]
                        wr, wi = w_real * zr - w_imag * zi, w_real * zi + w_imag * zr
                        data[j], data[j + 1] = data[i] - wr, data[i + 1] - wi
                        data[i] += wr
                        data[i + 1] += wi
                dual *= 2

        fft_acc = 0.0
        norm = 1.0 / float(nf)
        for rep in range(200):
            d = list(orig)
            fft(d, -1.0)
            fft_acc += abs(d[0]) + abs(d[1]) + abs(d[2 * ((rep * 7) % 512)])
            fft(d, 1.0)
            for k in range(2 * nf):
                d[k] *= norm
            fft_acc += abs(d[2 * ((rep * 13) % 512)])
        self.assertLess(abs(fft_acc * 10.0 - round(fft_acc * 10.0)), 0.30)
        _check_bench_golden(self, "scimark_fft", f"{math.floor(fft_acc * 10.0 + 0.5)}\n")


if __name__ == "__main__":
    unittest.main()
