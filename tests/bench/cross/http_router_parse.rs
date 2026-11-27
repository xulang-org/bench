const MOD_V: i64 = 1000000007;

fn push_str(buf: &mut Vec<i64>, s: &str) {
    for b in s.bytes() {
        buf.push(b as i64);
    }
}

fn push_int(buf: &mut Vec<i64>, v: i64) {
    let mut x = v;
    if x < 0 {
        buf.push(45);
        x = -x;
    }
    if x == 0 {
        buf.push(48);
        return;
    }
    let mut digs = [0i64; 24];
    let mut dc = 0usize;
    while x > 0 {
        digs[dc] = 48 + (x % 10);
        dc += 1;
        x /= 10;
    }
    let mut i = dc;
    while i > 0 {
        i -= 1;
        buf.push(digs[i]);
    }
}

fn hex_val(b: i64) -> i64 {
    if b >= 48 && b <= 57 { return b - 48; }
    if b >= 65 && b <= 70 { return b - 55; }
    if b >= 97 && b <= 102 { return b - 87; }
    -1
}

fn decode_pct_hash(buf: &[i64], start: usize, end: usize) -> i64 {
    let mut h: i64 = 0;
    let mut i = start;
    while i < end {
        let b = buf[i];
        let mut ch = b;
        if b == 43 {
            ch = 32;
            i += 1;
        } else if b == 37 && i + 2 < end {
            let hi = hex_val(buf[i + 1]);
            let lo = hex_val(buf[i + 2]);
            if hi >= 0 && lo >= 0 {
                ch = (hi << 4) | lo;
                i += 3;
            } else {
                i += 1;
            }
        } else {
            i += 1;
        }
        h = (h * 131 + ch) % MOD_V;
    }
    h
}

struct TrieRouter {
    node_edge_head: Vec<i64>,
    node_param: Vec<i64>,
    node_wild: Vec<i64>,
    node_routes: Vec<i64>,
    edge_off: Vec<usize>,
    edge_len: Vec<usize>,
    edge_child: Vec<usize>,
    edge_next: Vec<i64>,
    seg_pool: Vec<i64>,
}

impl TrieRouter {
    fn new() -> Self {
        let mut rt = Self {
            node_edge_head: Vec::new(),
            node_param: Vec::new(),
            node_wild: Vec::new(),
            node_routes: Vec::new(),
            edge_off: Vec::new(),
            edge_len: Vec::new(),
            edge_child: Vec::new(),
            edge_next: Vec::new(),
            seg_pool: Vec::new(),
        };
        rt.new_node();
        rt
    }

    fn new_node(&mut self) -> usize {
        let idx = self.node_edge_head.len();
        self.node_edge_head.push(-1);
        self.node_param.push(-1);
        self.node_wild.push(-1);
        for _ in 0..5 {
            self.node_routes.push(0);
        }
        idx
    }

    fn add_route(&mut self, method: usize, pat: &[&str], rid: i64) {
        let mut cur = 0usize;
        for &seg in pat {
            if seg == "*" {
                if self.node_wild[cur] < 0 {
                    let nn = self.new_node();
                    self.node_wild[cur] = nn as i64;
                }
                cur = self.node_wild[cur] as usize;
            } else if seg.starts_with(':') {
                if self.node_param[cur] < 0 {
                    let nn = self.new_node();
                    self.node_param[cur] = nn as i64;
                }
                cur = self.node_param[cur] as usize;
            } else {
                let mut e = self.node_edge_head[cur];
                let mut found: i64 = -1;
                let sb = seg.as_bytes();
                while e >= 0 {
                    let eu = e as usize;
                    let off = self.edge_off[eu];
                    let ln = self.edge_len[eu];
                    if ln == sb.len() && (0..ln).all(|j| self.seg_pool[off + j] == sb[j] as i64) {
                        found = e;
                        break;
                    }
                    e = self.edge_next[eu];
                }
                if found >= 0 {
                    cur = self.edge_child[found as usize];
                } else {
                    let nn = self.new_node();
                    let off = self.seg_pool.len();
                    for &b in sb {
                        self.seg_pool.push(b as i64);
                    }
                    let ei = self.edge_off.len();
                    self.edge_off.push(off);
                    self.edge_len.push(sb.len());
                    self.edge_child.push(nn);
                    self.edge_next.push(self.node_edge_head[cur]);
                    self.node_edge_head[cur] = ei as i64;
                    cur = nn;
                }
            }
        }
        self.node_routes[cur * 5 + method] = rid;
    }
}

fn match_lower_key(buf: &[i64], s: usize, e: usize, target: &[u8]) -> bool {
    if e - s != target.len() {
        return false;
    }
    for i in 0..target.len() {
        let mut c = buf[s + i];
        if c >= 65 && c <= 90 {
            c += 32;
        }
        if c != target[i] as i64 {
            return false;
        }
    }
    true
}

fn main() {
    let mut rt = TrieRouter::new();
    rt.add_route(1, &["health"], 1);
    rt.add_route(1, &["metrics"], 2);
    rt.add_route(1, &["api", "v1", "users", ":id"], 3);
    rt.add_route(2, &["api", "v1", "users"], 4);
    rt.add_route(1, &["api", "v1", "users", ":id", "posts", ":pid"], 5);
    rt.add_route(4, &["api", "v1", "users", ":id", "posts", ":pid"], 6);
    rt.add_route(1, &["api", "v1", "orders", ":oid", "items"], 7);
    rt.add_route(3, &["api", "v1", "orders", ":oid", "status"], 8);
    rt.add_route(1, &["api", "v1", "orgs", ":org", "repos", ":repo", "issues", ":num"], 9);
    rt.add_route(2, &["api", "v1", "orgs", ":org", "repos", ":repo", "issues"], 10);
    rt.add_route(1, &["api", "v2", "search"], 11);
    rt.add_route(1, &["static", "*"], 12);

    let users = ["alice", "bob42", "charlie", "dana_9", "eve", "frank01", "grace", "heidi"];
    let orgs = ["xulang", "acme", "nebula", "kernel"];
    let repos = ["xu", "bench", "runtime", "stdlib", "docs"];
    let queries = [
        "page=2&limit=50&q=hello+world%21",
        "sort=desc&filter=open%2Factive&tag=v1%2E0",
        "q=%41%42%43+test%20case&offset=100",
        "",
        "lang=zh%2DCN&mode=fast&debug=1",
        "path=%2Fusr%2Fbin&retry=3",
    ];

    let mut req_buf: Vec<i64> = Vec::with_capacity(65536);
    let mut req_off: Vec<usize> = Vec::with_capacity(240);
    let mut req_len: Vec<usize> = Vec::with_capacity(240);
    let mut rng: i64 = 246813579;
    for i in 0i64..240 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let k = rng % 14;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let u = users[(rng % 8) as usize];
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let pid = 100 + (rng % 900);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let oid = 10000 + (rng % 90000);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let org = orgs[(rng % 4) as usize];
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let repo = repos[(rng % 5) as usize];
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let num = 1 + (rng % 500);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let q = queries[(rng % 6) as usize];
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let cl = rng % 4096;

        let off = req_buf.len();
        req_off.push(off);
        match k {
            0 => push_str(&mut req_buf, "GET /health"),
            1 => push_str(&mut req_buf, "GET /metrics"),
            2 => { push_str(&mut req_buf, "GET /api/v1/users/"); push_str(&mut req_buf, u); }
            3 => push_str(&mut req_buf, "POST /api/v1/users"),
            4 => { push_str(&mut req_buf, "GET /api/v1/users/"); push_str(&mut req_buf, u); push_str(&mut req_buf, "/posts/"); push_int(&mut req_buf, pid); }
            5 => { push_str(&mut req_buf, "DELETE /api/v1/users/"); push_str(&mut req_buf, u); push_str(&mut req_buf, "/posts/"); push_int(&mut req_buf, pid); }
            6 => { push_str(&mut req_buf, "GET /api/v1/orders/"); push_int(&mut req_buf, oid); push_str(&mut req_buf, "/items"); }
            7 => { push_str(&mut req_buf, "PUT /api/v1/orders/"); push_int(&mut req_buf, oid); push_str(&mut req_buf, "/status"); }
            8 => { push_str(&mut req_buf, "GET /api/v1/orgs/"); push_str(&mut req_buf, org); push_str(&mut req_buf, "/repos/"); push_str(&mut req_buf, repo); push_str(&mut req_buf, "/issues/"); push_int(&mut req_buf, num); }
            9 => { push_str(&mut req_buf, "POST /api/v1/orgs/"); push_str(&mut req_buf, org); push_str(&mut req_buf, "/repos/"); push_str(&mut req_buf, repo); push_str(&mut req_buf, "/issues"); }
            10 => push_str(&mut req_buf, "GET /api/v2/search"),
            11 => { push_str(&mut req_buf, "GET /static/js/"); push_str(&mut req_buf, repo); push_str(&mut req_buf, "/bundle_"); push_int(&mut req_buf, pid); push_str(&mut req_buf, ".js"); }
            12 => { push_str(&mut req_buf, "GET /api/v1/unknown/"); push_str(&mut req_buf, u); push_str(&mut req_buf, "/nope"); }
            _ => push_str(&mut req_buf, "POST /health"),
        }
        if !q.is_empty() {
            req_buf.push(63);
            push_str(&mut req_buf, q);
        }
        push_str(&mut req_buf, " HTTP/1.1\r\n");
        if (i % 3) != 0 {
            push_str(&mut req_buf, "Host: api.xulang.org\r\n");
        } else {
            push_str(&mut req_buf, "HOST: api.xulang.org\r\n");
        }
        push_str(&mut req_buf, "User-Agent: xu-bench/1.0\r\n");
        if (i & 1) == 0 {
            push_str(&mut req_buf, "Content-Length: ");
        } else {
            push_str(&mut req_buf, "content-length: ");
        }
        push_int(&mut req_buf, cl);
        push_str(&mut req_buf, "\r\nX-Request-Id: req-");
        push_int(&mut req_buf, i);
        req_buf.push(45);
        push_int(&mut req_buf, num);
        push_str(&mut req_buf, "\r\n\r\n");
        req_len.push(req_buf.len() - off);
    }

    let mut seg_starts = [0usize; 16];
    let mut seg_ends = [0usize; 16];
    let mut matched: i64 = 0;
    let mut ck: i64 = 0;
    for _rnd in 0..500 {
        for ri in 0..240 {
            let r_start = req_off[ri];
            let r_end = r_start + req_len[ri];
            let mut sp1 = r_start;
            while req_buf[sp1] != 32 {
                sp1 += 1;
            }
            let mlen = sp1 - r_start;
            let mut mc: i64 = 0;
            if mlen == 3 && req_buf[r_start] == 71 {
                mc = 1;
            } else if mlen == 4 && req_buf[r_start] == 80 {
                mc = 2;
            } else if mlen == 3 && req_buf[r_start] == 80 {
                mc = 3;
            } else if mlen == 6 && req_buf[r_start] == 68 {
                mc = 4;
            }
            let t_start = sp1 + 1;
            let mut sp2 = t_start;
            while req_buf[sp2] != 32 {
                sp2 += 1;
            }
            let mut crlf = sp2 + 1;
            while !(req_buf[crlf] == 13 && req_buf[crlf + 1] == 10) {
                crlf += 1;
            }
            let mut qpos: Option<usize> = None;
            for p in t_start..sp2 {
                if req_buf[p] == 63 {
                    qpos = Some(p);
                    break;
                }
            }
            let path_end = qpos.unwrap_or(sp2);
            let mut n_segs = 0usize;
            let mut sp = t_start;
            while sp < path_end {
                while sp < path_end && req_buf[sp] == 47 {
                    sp += 1;
                }
                if sp >= path_end {
                    break;
                }
                let mut se = sp;
                while se < path_end && req_buf[se] != 47 {
                    se += 1;
                }
                seg_starts[n_segs] = sp;
                seg_ends[n_segs] = se;
                n_segs += 1;
                sp = se;
            }

            let mut pos = crlf + 2;
            let mut hdr_cnt: i64 = 0;
            let mut content_len: i64 = 0;
            let mut req_id_hash: i64 = 0;
            while pos < r_end {
                let mut lend = pos;
                while lend + 1 < r_end && !(req_buf[lend] == 13 && req_buf[lend + 1] == 10) {
                    lend += 1;
                }
                if lend == pos {
                    break;
                }
                let mut col = pos;
                while col < lend && req_buf[col] != 58 {
                    col += 1;
                }
                let mut vs = col + 1;
                while vs < lend && (req_buf[vs] == 32 || req_buf[vs] == 9) {
                    vs += 1;
                }
                let mut ve = lend;
                while ve > vs && (req_buf[ve - 1] == 32 || req_buf[ve - 1] == 9) {
                    ve -= 1;
                }
                hdr_cnt += 1;
                if match_lower_key(&req_buf, pos, col, b"content-length") {
                    let mut v: i64 = 0;
                    for vp in vs..ve {
                        v = v * 10 + (req_buf[vp] - 48);
                    }
                    content_len = v;
                } else if match_lower_key(&req_buf, pos, col, b"x-request-id") {
                    for vp in vs..ve {
                        req_id_hash = (req_id_hash * 31 + req_buf[vp]) % MOD_V;
                    }
                }
                pos = lend + 2;
            }

            let mut cur = 0usize;
            let mut ph: i64 = 0;
            let mut sj = 0usize;
            let mut dead = false;
            while sj < n_segs {
                let ss = seg_starts[sj];
                let sln = seg_ends[sj] - ss;
                let mut e = rt.node_edge_head[cur];
                let mut nxt: i64 = -1;
                while e >= 0 {
                    let eu = e as usize;
                    let off = rt.edge_off[eu];
                    if sln == rt.edge_len[eu] && (0..sln).all(|j| req_buf[ss + j] == rt.seg_pool[off + j]) {
                        nxt = rt.edge_child[eu] as i64;
                        break;
                    }
                    e = rt.edge_next[eu];
                }
                if nxt >= 0 {
                    cur = nxt as usize;
                    sj += 1;
                } else if rt.node_param[cur] >= 0 {
                    for cp in ss..(ss + sln) {
                        ph = (ph * 131 + req_buf[cp]) % MOD_V;
                    }
                    cur = rt.node_param[cur] as usize;
                    sj += 1;
                } else if rt.node_wild[cur] >= 0 {
                    while sj < n_segs {
                        for cp in seg_starts[sj]..seg_ends[sj] {
                            ph = (ph * 131 + req_buf[cp]) % MOD_V;
                        }
                        sj += 1;
                    }
                    cur = rt.node_wild[cur] as usize;
                    break;
                } else {
                    dead = true;
                    break;
                }
            }
            let mut route_id: i64 = 0;
            let mut param_hash: i64 = 0;
            if !dead {
                let rid = rt.node_routes[cur * 5 + mc as usize];
                if rid > 0 {
                    route_id = rid;
                    param_hash = ph;
                }
            }
            let mut q_hash: i64 = 0;
            if let Some(qp_idx) = qpos {
                if qp_idx + 1 < sp2 {
                    let mut qp = qp_idx + 1;
                    while qp < sp2 {
                        let mut qe = qp;
                        while qe < sp2 && req_buf[qe] != 38 {
                            qe += 1;
                        }
                        let mut eq: Option<usize> = None;
                        for qt in qp..qe {
                            if req_buf[qt] == 61 {
                                eq = Some(qt);
                                break;
                            }
                        }
                        if let Some(eq_idx) = eq {
                            let kh = decode_pct_hash(&req_buf, qp, eq_idx);
                            let vh = decode_pct_hash(&req_buf, eq_idx + 1, qe);
                            q_hash = (q_hash * 257 + kh * 17 + vh) % MOD_V;
                        } else {
                            q_hash = (q_hash * 257 + decode_pct_hash(&req_buf, qp, qe)) % MOD_V;
                        }
                        qp = qe + 1;
                    }
                }
            }
            if route_id > 0 {
                matched += 1;
            }
            let row = (route_id * 1000003 + mc * 97 + param_hash * 7 + q_hash * 13 + content_len * 3 + hdr_cnt * 19 + req_id_hash) % MOD_V;
            ck = (ck * 31 + row) % MOD_V;
        }
    }
    println!("{matched}");
    println!("{ck}");
}
