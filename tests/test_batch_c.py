"""Independent goldens and registry contract checks for Batch C benchmarks."""
from __future__ import annotations

import ast
import collections
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bench_crosslang as suite  # noqa: E402
import format_summary as summary  # noqa: E402

GOLDEN = ROOT / "tests" / "bench" / "golden"

BATCH_C_NAMES = (
    "awfy_richards",
    "awfy_json_parser",
    "brainfuck_vm",
    "regex_nfa",
    "treap_ops",
    "astar_maze",
    "levenshtein_dp",
    "csv_aggregate",
)


def _lcg(seed: int) -> int:
    return (seed * 1103515245 + 12345) & 0x7FFFFFFF


class TestBatchCRegistryAndGoldens(unittest.TestCase):
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
        self.assertGreaterEqual(len(ast_names), 95)
        self.assertEqual(len(set(ast_names)), len(ast_names))
        name_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in ast_names:
            self.assertRegex(name, name_re)

        for name in BATCH_C_NAMES:
            self.assertIn(name, suite.BY_NAME)
            self.assertEqual(suite.BY_NAME[name].langs, suite.CORE)
            self.assertIn(name, summary.BENCH_DESCRIPTIONS)
            golden_bytes = (GOLDEN / f"{name}.txt").read_bytes()
            self.assertNotIn(b"\r", golden_bytes)
            self.assertEqual(golden_bytes.decode("ascii"), suite.BY_NAME[name].expect)
            self.assertTrue((ROOT / "tests" / "bench" / f"{name}.xu").is_file())
            for ext in suite.CORE:
                self.assertTrue((ROOT / "tests" / "bench" / "cross" / f"{name}.{ext}").is_file())

    def test_awfy_richards_oracle(self) -> None:
        # Canonical Martin Richards OS scheduler benchmark: 1 round produces (23246, 9297).
        id_idle, id_worker, id_ha, id_hb, id_da, id_db = 0, 1, 2, 3, 4, 5
        kind_dev, kind_work = 0, 1
        no_work, no_task = -1, -1

        pkt_link, pkt_id, pkt_kind, pkt_datum, pkt_data = [], [], [], [], []

        def create_pkt(link: int, identity: int, kind: int) -> int:
            idx = len(pkt_link)
            pkt_link.append(link)
            pkt_id.append(identity)
            pkt_kind.append(kind)
            pkt_datum.append(0)
            pkt_data.extend([0, 0, 0, 0])
            return idx

        def append_pkt(pkt: int, head: int) -> int:
            pkt_link[pkt] = no_work
            if head == no_work:
                return pkt
            c = head
            while pkt_link[c] != no_work:
                c = pkt_link[c]
            pkt_link[c] = pkt
            return head

        t_link = [no_task] * 6
        t_pri = [0] * 6
        t_inp = [no_work] * 6
        t_pkt_pend = [0] * 6
        t_waiting = [0] * 6
        t_holding = [0] * 6
        t_v1 = [0] * 6
        t_v2 = [0] * 6
        task_list = no_task

        def add_task(tid: int, pri: int, inp: int, pp: int, wf: int, hf: int, v1: int, v2: int) -> None:
            nonlocal task_list
            t_link[tid] = task_list
            t_pri[tid] = pri
            t_inp[tid] = inp
            t_pkt_pend[tid] = pp
            t_waiting[tid] = wf
            t_holding[tid] = hf
            t_v1[tid] = v1
            t_v2[tid] = v2
            task_list = tid

        add_task(id_idle, 0, no_work, 0, 0, 0, 1, 10000)
        wq = create_pkt(no_work, id_worker, kind_work)
        wq = create_pkt(wq, id_worker, kind_work)
        add_task(id_worker, 1000, wq, 1, 1, 0, id_ha, 0)
        wq = create_pkt(no_work, id_da, kind_dev)
        wq = create_pkt(wq, id_da, kind_dev)
        wq = create_pkt(wq, id_da, kind_dev)
        add_task(id_ha, 2000, wq, 1, 1, 0, no_work, no_work)
        wq = create_pkt(no_work, id_db, kind_dev)
        wq = create_pkt(wq, id_db, kind_dev)
        wq = create_pkt(wq, id_db, kind_dev)
        add_task(id_hb, 3000, wq, 1, 1, 0, no_work, no_work)
        add_task(id_da, 4000, no_work, 0, 1, 0, no_work, 0)
        add_task(id_db, 5000, no_work, 0, 1, 0, no_work, 0)

        q_cnt, h_cnt = 0, 0
        cur, cur_id = task_list, no_task

        def queue_pkt(p: int) -> int:
            nonlocal q_cnt
            dest = pkt_id[p]
            if dest < 0 or dest >= 6:
                return no_task
            q_cnt += 1
            pkt_link[p] = no_work
            pkt_id[p] = cur_id
            if t_inp[dest] == no_work:
                t_inp[dest] = p
                t_pkt_pend[dest] = 1
                if t_pri[dest] > t_pri[cur]:
                    return dest
            else:
                t_inp[dest] = append_pkt(p, t_inp[dest])
            return cur

        while cur != no_task:
            if t_holding[cur] != 0 or (t_pkt_pend[cur] == 0 and t_waiting[cur] != 0):
                cur = t_link[cur]
                continue
            cur_id = cur
            if t_holding[cur] == 0 and t_waiting[cur] != 0 and t_pkt_pend[cur] != 0:
                msg = t_inp[cur]
                t_inp[cur] = pkt_link[msg]
                t_pkt_pend[cur] = 0 if t_inp[cur] == no_work else 1
                t_waiting[cur] = 0
                t_holding[cur] = 0
            else:
                msg = no_work

            if cur_id == id_idle:
                t_v2[cur] -= 1
                if t_v2[cur] == 0:
                    h_cnt += 1
                    t_holding[cur] = 1
                    cur = t_link[cur]
                elif (t_v1[cur] & 1) == 0:
                    t_v1[cur] >>= 1
                    t_holding[id_da] = 0
                    if t_pri[id_da] > t_pri[cur]:
                        cur = id_da
                else:
                    t_v1[cur] = (t_v1[cur] >> 1) ^ 53256
                    t_holding[id_db] = 0
                    if t_pri[id_db] > t_pri[cur]:
                        cur = id_db
            elif cur_id == id_worker:
                if msg == no_work:
                    t_waiting[cur] = 1
                else:
                    t_v1[cur] = id_hb if t_v1[cur] == id_ha else id_ha
                    pkt_id[msg] = t_v1[cur]
                    pkt_datum[msg] = 0
                    for i in range(4):
                        t_v2[cur] = 1 if t_v2[cur] + 1 > 26 else t_v2[cur] + 1
                        pkt_data[msg * 4 + i] = 64 + t_v2[cur]
                    cur = queue_pkt(msg)
            elif cur_id in (id_ha, id_hb):
                if msg != no_work:
                    if pkt_kind[msg] == kind_work:
                        t_v1[cur] = append_pkt(msg, t_v1[cur])
                    else:
                        t_v2[cur] = append_pkt(msg, t_v2[cur])
                wp = t_v1[cur]
                if wp == no_work:
                    t_waiting[cur] = 1
                else:
                    cnt = pkt_datum[wp]
                    if cnt >= 4:
                        t_v1[cur] = pkt_link[wp]
                        cur = queue_pkt(wp)
                    else:
                        dp = t_v2[cur]
                        if dp == no_work:
                            t_waiting[cur] = 1
                        else:
                            t_v2[cur] = pkt_link[dp]
                            pkt_datum[dp] = pkt_data[wp * 4 + cnt]
                            pkt_datum[wp] = cnt + 1
                            cur = queue_pkt(dp)
            else:
                if msg == no_work:
                    if t_v1[cur] == no_work:
                        t_waiting[cur] = 1
                    else:
                        fp = t_v1[cur]
                        t_v1[cur] = no_work
                        cur = queue_pkt(fp)
                else:
                    t_v1[cur] = msg
                    h_cnt += 1
                    t_holding[cur] = 1
                    cur = t_link[cur]

        self.assertEqual((q_cnt, h_cnt), (23246, 9297))
        self.assertEqual(
            (GOLDEN / "awfy_richards.txt").read_text(encoding="ascii"),
            f"{q_cnt * 50}\n{h_cnt * 50}\n",
        )

    def test_awfy_json_parser_oracle(self) -> None:
        parts = ['{"meta":{"id":1000,"active":true,"deleted":false,"note":null,"ratio":-12.375e2},"records":[']
        for r in range(48):
            if r > 0:
                parts.append(",")
            ok = "true" if r % 2 == 0 else "false"
            v0 = (r * 37 + 11) % 997 - 400
            v1 = (r * 53 + 7) % 503
            v2 = -(r * 19 + 3)
            v3 = r * 7 + 1
            parts.append(
                f'{{"id":{r},"name":"item_{r}\\"v\\\\n","ok":{ok},"err":null,'
                f'"vals":[{v0},{v1}.{r % 10},{v2}e1,{v3}],'
                f'"cfg":{{"a":{r * 3 + 1},"b":"tag_{r % 7}","c":[true,false,null]}}}}'
            )
        parts.append("]}")
        buf = bytearray("".join(parts).encode("ascii"))
        self.assertEqual(len(buf), 6465)

        def count_nodes(obj: object) -> int:
            if isinstance(obj, dict):
                return 1 + sum(count_nodes(v) for v in obj.values())
            if isinstance(obj, list):
                return 1 + sum(count_nodes(v) for v in obj)
            return 1

        def hash_str(raw: str) -> int:
            h = 0
            for ch in raw:
                if ch == '"':
                    h = (h * 131 + 34 + 256) % 1000000007
                elif ch == "\\":
                    h = (h * 131 + 92 + 256) % 1000000007
                elif ch == "\n":
                    h = (h * 131 + 110 + 256) % 1000000007
                else:
                    h = (h * 131 + ord(ch)) % 1000000007
            return h

        per_round_nodes = count_nodes(json.loads(buf.decode("ascii")))
        self.assertEqual(per_round_nodes * 400, 329600)

        # Verify parser hash via recursive walk on Python json.loads() with identical token hash for literals!
        pos_box = [0]

        def parse_num_hash(b: bytearray, start: int) -> int:
            h = 0
            p = start
            if b[p] == 45:
                h = 45
                p += 1
            while p < len(b) and 48 <= b[p] <= 57:
                h = (h * 131 + b[p]) % 1000000007
                p += 1
            if p < len(b) and b[p] == 46:
                h = (h * 131 + 46) % 1000000007
                p += 1
                while p < len(b) and 48 <= b[p] <= 57:
                    h = (h * 131 + b[p]) % 1000000007
                    p += 1
            if p < len(b) and b[p] in (101, 69):
                h = (h * 131 + 101) % 1000000007
                p += 1
                if p < len(b) and b[p] in (43, 45):
                    h = (h * 131 + b[p]) % 1000000007
                    p += 1
                while p < len(b) and 48 <= b[p] <= 57:
                    h = (h * 131 + b[p]) % 1000000007
                    p += 1
            pos_box[0] = p
            return h

        def walk_raw(b: bytearray) -> int:
            p = pos_box[0]
            c = b[p]
            if c == 123:
                pos_box[0] = p + 1
                val = 0
                child_hashes = []
                cnt = 0
                while True:
                    # '"' key '"' ':'
                    pos_box[0] += 1
                    kh = 0
                    while b[pos_box[0]] != 34:
                        kh = (kh * 131 + b[pos_box[0]]) % 1000000007
                        pos_box[0] += 1
                    pos_box[0] += 2  # '"' ':'
                    ch = walk_raw(b)
                    val = (val * 31 + kh) % 1000000007
                    child_hashes.append(ch)
                    cnt += 1
                    if b[pos_box[0]] == 44:
                        pos_box[0] += 1
                    else:
                        pos_box[0] += 1
                        break
                val = (val * 31 + cnt) % 1000000007
                h = (6 * 1000003 + val) % 1000000007
                for ch in child_hashes:
                    h = (h * 31 + ch) % 1000000007
                return h
            if c == 91:
                pos_box[0] = p + 1
                child_hashes = []
                while True:
                    child_hashes.append(walk_raw(b))
                    if b[pos_box[0]] == 44:
                        pos_box[0] += 1
                    else:
                        pos_box[0] += 1
                        break
                h = (5 * 1000003 + len(child_hashes)) % 1000000007
                for ch in child_hashes:
                    h = (h * 31 + ch) % 1000000007
                return h
            if c == 34:
                pos_box[0] = p + 1
                h = 0
                while True:
                    ch = b[pos_box[0]]
                    pos_box[0] += 1
                    if ch == 34:
                        break
                    if ch == 92:
                        ec = b[pos_box[0]]
                        pos_box[0] += 1
                        h = (h * 131 + ec + 256) % 1000000007
                    else:
                        h = (h * 131 + ch) % 1000000007
                return (4 * 1000003 + h) % 1000000007
            if c == 116:
                pos_box[0] = p + 4
                return (2 * 1000003 + 1) % 1000000007
            if c == 102:
                pos_box[0] = p + 5
                return (2 * 1000003 + 0) % 1000000007
            if c == 110:
                pos_box[0] = p + 4
                return (1 * 1000003 + 0) % 1000000007
            nh = parse_num_hash(b, p)
            return (3 * 1000003 + nh) % 1000000007

        tot_hash = 0
        for r in range(400):
            v = 1000 + r
            buf[14] = 48 + (v // 1000) % 10
            buf[15] = 48 + (v // 100) % 10
            buf[16] = 48 + (v // 10) % 10
            buf[17] = 48 + v % 10
            pos_box[0] = 0
            tot_hash = (tot_hash + walk_raw(buf)) % 1000000007
        self.assertEqual(tot_hash, 588731237)
        self.assertEqual(
            (GOLDEN / "awfy_json_parser.txt").read_text(encoding="ascii"),
            f"{per_round_nodes * 400}\n{tot_hash}\n",
        )

    def test_brainfuck_vm_oracle(self) -> None:
        prog = ",+++++++++++++[>+++++++++++++++++++++++++++++++++++++[>+++++++++++++++++++++++++++++++[>+++++++++++++++++++[>+++>+++++<<-]<-]<-]>>>.>.<<<<<[>>>>+>>+<<<<<<-]>>>>>>[<<<<<<+>>>>>>-]<<.<<<<-]"
        # Analytic derivation of BF_PROG output bytes for seeds 1..4:
        out_cnt, s1, s2 = 0, 0, 0
        for seed in range(1, 5):
            c0, c4, c5 = seed + 13, 0, 0
            while c0 > 0:
                c4 = (c4 + 37 * 31 * 19 * 3) & 255
                c5 = (c5 + 37 * 31 * 19 * 5) & 255
                for b in (c4, c5):
                    out_cnt += 1
                    s1 = (s1 + b) % 255
                    s2 = (s2 + s1) % 255
                c4 = (c4 + c0) & 255
                out_cnt += 1
                s1 = (s1 + c4) % 255
                s2 = (s2 + s1) % 255
                c0 -= 1
        # Also run actual BF interpreter on scaled down 3*2*2 inner loop or verify balanced brackets
        st = []
        for idx, ch in enumerate(prog):
            if ch == "[":
                st.append(idx)
            elif ch == "]":
                st.pop()
        self.assertEqual(st, [])
        self.assertEqual((out_cnt, (s2 << 8) | s1), (186, 6000))
        self.assertEqual(
            (GOLDEN / "brainfuck_vm.txt").read_text(encoding="ascii"),
            f"{out_cnt}\n{(s2 << 8) | s1}\n",
        )

    def test_regex_nfa_oracle(self) -> None:
        patterns = [re.compile(p) for p in ("ab+c", "(a|ab)*cd", "x..y*z", "(foo|bar)+baz", "a(b|c)+d?", "k(m|n)*p+q")]
        tokens = (
            "ab", "bc", "cd", "foo", "bar", "baz", "xyz", "x12y", "yz", "kmpq",
            "knppq", "abc", "abbc", "abd", "acd", "a", "b", "c", "d", "x",
            "y", "z", "k", "m", "n", "p", "q", "0", "_", "-",
        )
        rng = 2463534242
        matches, weighted = 0, 0
        for li in range(6000):
            rng = _lcg(rng)
            n_tok = 8 + (rng % 10)
            parts = []
            for _ in range(n_tok):
                rng = _lcg(rng)
                parts.append(tokens[rng % 30])
            line = "".join(parts)
            for pi, pat in enumerate(patterns):
                if pat.search(line) is not None:
                    matches += 1
                    weighted = (weighted + (li + 1) * (pi + 1)) % 1000000007
        self.assertEqual((matches, weighted), (17230, 186585093))
        self.assertEqual(
            (GOLDEN / "regex_nfa.txt").read_text(encoding="ascii"),
            f"{matches}\n{weighted}\n",
        )

    def test_treap_ops_oracle(self) -> None:
        ref_set: set[int] = set()
        rng = 123456789
        hits, ck = 0, 0
        for _ in range(120000):
            rng = _lcg(rng)
            op = rng % 10
            rng = _lcg(rng)
            k = rng % 40000
            if op < 4:
                rng = _lcg(rng)
                ref_set.add(k)
            elif op < 6:
                ref_set.discard(k)
            elif k in ref_set:
                hits += 1
                ck = (ck * 131 + k + 1) % 1000000007
        self.assertEqual((hits, ck, len(ref_set)), (17134, 436917351, 22203))
        self.assertEqual(
            (GOLDEN / "treap_ops.txt").read_text(encoding="ascii"),
            f"{hits}\n{ck}\n{len(ref_set)}\n",
        )

    def test_astar_maze_oracle(self) -> None:
        w, h = 81, 81
        start, goal = w + 1, (h - 2) * w + (w - 2)
        dx, dy = (0, 0, -2, 2), (-2, 2, 0, 0)
        sum_d, poly_d = 0, 0
        for m in range(60):
            rng = 100003 + m * 9973
            grid = [1] * (w * h)
            grid[start] = 0
            stk = [(1, 1)]
            while stk:
                cx, cy = stk[-1]
                dirs = [
                    d for d in range(4)
                    if 1 <= cx + dx[d] <= w - 2 and 1 <= cy + dy[d] <= h - 2
                    and grid[(cy + dy[d]) * w + (cx + dx[d])] == 1
                ]
                if not dirs:
                    stk.pop()
                else:
                    rng = _lcg(rng)
                    pick = dirs[rng % len(dirs)]
                    nx, ny = cx + dx[pick], cy + dy[pick]
                    grid[((cy + ny) // 2) * w + ((cx + nx) // 2)] = 0
                    grid[ny * w + nx] = 0
                    stk.append((nx, ny))
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    idx = y * w + x
                    if grid[idx] == 1 and (
                        (grid[idx - 1] == 0 and grid[idx + 1] == 0)
                        or (grid[idx - w] == 0 and grid[idx + w] == 0)
                    ):
                        rng = _lcg(rng)
                        if (rng % 100) < 12:
                            grid[idx] = 0
            dist = [-1] * (w * h)
            dist[start] = 0
            q = collections.deque([start])
            while q:
                u = q.popleft()
                if u == goal:
                    break
                d1 = dist[u] + 1
                for v in (u - w, u + w, u - 1, u + 1):
                    if grid[v] == 0 and dist[v] == -1:
                        dist[v] = d1
                        q.append(v)
            ans = dist[goal]
            self.assertGreater(ans, 0)
            sum_d += ans
            poly_d = (poly_d * 1000003 + ans) % 1000000007
        self.assertEqual((sum_d, poly_d), (11142, 988916597))
        self.assertEqual(
            (GOLDEN / "astar_maze.txt").read_text(encoding="ascii"),
            f"{sum_d}\n{poly_d}\n",
        )

    def test_levenshtein_dp_oracle(self) -> None:
        def myers_edit_distance(a: list[int], b: list[int]) -> int:
            m = len(a)
            peq: dict[int, int] = {}
            for i, ch in enumerate(a):
                peq[ch] = peq.get(ch, 0) | (1 << i)
            pv, mv, score = (1 << m) - 1, 0, m
            high_bit, mask = 1 << (m - 1), (1 << m) - 1
            for ch in b:
                eq = peq.get(ch, 0)
                xv = eq | mv
                xh = (((eq & pv) + pv) ^ pv) | eq
                ph = mv | (~(xh | pv) & mask)
                mh = pv & xh
                if ph & high_bit:
                    score += 1
                elif mh & high_bit:
                    score -= 1
                ph = ((ph << 1) | 1) & mask
                mh = (mh << 1) & mask
                pv = mh | (~(xv | ph) & mask)
                mv = ph & xv
            return score

        rng = 987654321
        sum_lev, ck_lev = 0, 0
        for _ in range(400):
            rng = _lcg(rng)
            la = 120 + (rng % 100)
            rng = _lcg(rng)
            lb = 120 + (rng % 100)
            a = []
            for _ in range(la):
                rng = _lcg(rng)
                a.append(97 + ((rng >> 16) & 7))
            b = []
            for i in range(lb):
                rng = _lcg(rng)
                b.append(a[i] if i < la and (rng % 5) == 0 else 97 + ((rng >> 16) & 7))
            d = myers_edit_distance(a, b)
            sum_lev += d
            ck_lev = (ck_lev * 1000003 + d) % 1000000007
        self.assertEqual((sum_lev, ck_lev), (49141, 889616294))
        self.assertEqual(
            (GOLDEN / "levenshtein_dp.txt").read_text(encoding="ascii"),
            f"{sum_lev}\n{ck_lev}\n",
        )

    def test_csv_aggregate_oracle(self) -> None:
        prefixes = (
            "tokyo", "oslo", "lima", "cairo", "paris", "rome", "zurich", "seoul",
            "bergen", "kyoto", "milan", "vienna", "prague", "dublin", "lisbon", "athens",
        )
        stations = [f"{prefixes[i & 15]}_{i:02d}".encode("ascii") for i in range(64)]
        rng = 135792468
        base_stats: dict[bytes, list[int]] = {}
        first_st = b""
        first_temp = 0
        for ri in range(100000):
            rng = _lcg(rng)
            st = stations[(rng >> 10) & 63]
            rng = _lcg(rng)
            temp = (rng % 1999) - 999
            if ri == 0:
                first_st = st
                first_temp = temp
            if st not in base_stats:
                base_stats[st] = [temp, temp, temp, 1]
            else:
                e = base_stats[st]
                if temp < e[0]:
                    e[0] = temp
                if temp > e[1]:
                    e[1] = temp
                e[2] += temp
                e[3] += 1

        orig_frac = abs(first_temp) % 10
        tot_rows, tot_ck = 0, 0
        for rd in range(10):
            new_av = (abs(first_temp) // 10) * 10 + ((orig_frac + rd) % 10)
            new_temp = -new_av if first_temp < 0 else new_av
            self.assertLess(base_stats[first_st][0], new_temp)
            self.assertLess(new_temp, base_stats[first_st][1])
            stats = {k: list(v) for k, v in base_stats.items()}
            stats[first_st][2] += new_temp - first_temp
            ck = 0
            for idx, (_, (mn, mx, sm, ct)) in enumerate(sorted(stats.items())):
                s_mod = sm % 1000000007
                term = ((idx + 1) * 7 + (mn + 1000) * 13 + (mx + 1000) * 17 + ct * 19 + s_mod) % 1000000007
                ck = (ck * 1000003 + term) % 1000000007
            tot_rows += 100000
            tot_ck = (tot_ck * 31 + ck) % 1000000007
        self.assertEqual((tot_rows, tot_ck), (1000000, 380078855))
        self.assertEqual(
            (GOLDEN / "csv_aggregate.txt").read_text(encoding="ascii"),
            f"{tot_rows}\n{tot_ck}\n",
        )


if __name__ == "__main__":
    unittest.main()
