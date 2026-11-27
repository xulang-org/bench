struct NfaPool {
    st_kind: Vec<i64>,
    st_out1: Vec<i64>,
    st_out2: Vec<i64>,
    p_st: Vec<i64>,
    p_wh: Vec<i64>,
    p_next: Vec<i64>,
    start_st: Vec<i64>,
    match_st: Vec<i64>,
}

fn prec(op: i64) -> i64 {
    if op == -3 {
        return 1;
    }
    if op == -2 {
        return 2;
    }
    if op == -4 || op == -5 || op == -6 {
        return 3;
    }
    0
}

impl NfaPool {
    fn new() -> Self {
        Self {
            st_kind: Vec::new(),
            st_out1: Vec::new(),
            st_out2: Vec::new(),
            p_st: Vec::new(),
            p_wh: Vec::new(),
            p_next: Vec::new(),
            start_st: Vec::new(),
            match_st: Vec::new(),
        }
    }

    fn add_st(&mut self, k: i64, o1: i64, o2: i64) -> i64 {
        let idx = self.st_kind.len() as i64;
        self.st_kind.push(k);
        self.st_out1.push(o1);
        self.st_out2.push(o2);
        idx
    }

    fn new_patch(&mut self, si: i64, wh: i64) -> i64 {
        let idx = self.p_st.len() as i64;
        self.p_st.push(si);
        self.p_wh.push(wh);
        self.p_next.push(-1);
        idx
    }

    fn append_patch(&mut self, h1: i64, t1: i64, h2: i64) -> i64 {
        if h1 == -1 {
            return h2;
        }
        if h2 == -1 {
            return h1;
        }
        self.p_next[t1 as usize] = h2;
        h1
    }

    fn apply_patch(&mut self, head: i64, target: i64) {
        let mut cur = head;
        while cur != -1 {
            let cu = cur as usize;
            let st_idx = self.p_st[cu] as usize;
            if self.p_wh[cu] == 1 {
                self.st_out1[st_idx] = target;
            } else {
                self.st_out2[st_idx] = target;
            }
            cur = self.p_next[cu];
        }
    }

    fn compile_pattern(&mut self, pat: &str) {
        let mut toks: Vec<i64> = Vec::with_capacity(pat.len() * 2);
        let mut prev_atom = false;
        for b in pat.bytes() {
            let c = b as i64;
            if c == 40 {
                if prev_atom {
                    toks.push(-2);
                }
                toks.push(-10);
                prev_atom = false;
            } else if c == 41 {
                toks.push(-11);
                prev_atom = true;
            } else if c == 124 {
                toks.push(-3);
                prev_atom = false;
            } else if c == 42 {
                toks.push(-4);
                prev_atom = true;
            } else if c == 43 {
                toks.push(-5);
                prev_atom = true;
            } else if c == 63 {
                toks.push(-6);
                prev_atom = true;
            } else {
                if prev_atom {
                    toks.push(-2);
                }
                toks.push(if c == 46 { -1 } else { c });
                prev_atom = true;
            }
        }

        let mut post: Vec<i64> = Vec::with_capacity(toks.len());
        let mut ops: Vec<i64> = Vec::with_capacity(toks.len());
        for &t in &toks {
            if t >= 0 || t == -1 {
                post.push(t);
            } else if t == -10 {
                ops.push(t);
            } else if t == -11 {
                while let Some(&top) = ops.last() {
                    if top == -10 {
                        break;
                    }
                    post.push(top);
                    ops.pop();
                }
                ops.pop();
            } else {
                let pt = prec(t);
                while let Some(&top) = ops.last() {
                    if top == -10 || prec(top) < pt {
                        break;
                    }
                    post.push(top);
                    ops.pop();
                }
                ops.push(t);
            }
        }
        while let Some(top) = ops.pop() {
            post.push(top);
        }

        let mut fs: Vec<i64> = Vec::new();
        let mut fh: Vec<i64> = Vec::new();
        let mut ft: Vec<i64> = Vec::new();
        for &t in &post {
            if t >= 0 || t == -1 {
                let s = self.add_st(t, -1, -1);
                let p = self.new_patch(s, 1);
                fs.push(s);
                fh.push(p);
                ft.push(p);
            } else if t == -2 {
                let s2 = fs.pop().unwrap();
                let h2 = fh.pop().unwrap();
                let t2 = ft.pop().unwrap();
                let s1 = fs.pop().unwrap();
                let h1 = fh.pop().unwrap();
                ft.pop();
                self.apply_patch(h1, s2);
                fs.push(s1);
                fh.push(h2);
                ft.push(t2);
            } else if t == -3 {
                let s2 = fs.pop().unwrap();
                let h2 = fh.pop().unwrap();
                let t2 = ft.pop().unwrap();
                let s1 = fs.pop().unwrap();
                let h1 = fh.pop().unwrap();
                let t1 = ft.pop().unwrap();
                let s = self.add_st(-2, s1, s2);
                let hn = self.append_patch(h1, t1, h2);
                fs.push(s);
                fh.push(hn);
                ft.push(t2);
            } else if t == -6 {
                let s1 = fs.pop().unwrap();
                let h1 = fh.pop().unwrap();
                let t1 = ft.pop().unwrap();
                let s = self.add_st(-2, s1, -1);
                let p = self.new_patch(s, 2);
                let hn = self.append_patch(h1, t1, p);
                fs.push(s);
                fh.push(hn);
                ft.push(p);
            } else if t == -4 {
                let s1 = fs.pop().unwrap();
                let h1 = fh.pop().unwrap();
                ft.pop();
                let s = self.add_st(-2, s1, -1);
                self.apply_patch(h1, s);
                let p = self.new_patch(s, 2);
                fs.push(s);
                fh.push(p);
                ft.push(p);
            } else if t == -5 {
                let s1 = fs.pop().unwrap();
                let h1 = fh.pop().unwrap();
                ft.pop();
                let s = self.add_st(-2, s1, -1);
                self.apply_patch(h1, s);
                let p = self.new_patch(s, 2);
                fs.push(s1);
                fh.push(p);
                ft.push(p);
            }
        }
        let m = self.add_st(-3, -1, -1);
        let h_final = fh.pop().unwrap();
        let s_final = fs.pop().unwrap();
        self.apply_patch(h_final, m);
        self.start_st.push(s_final);
        self.match_st.push(m);
    }
}

fn add_state(
    nfa: &NfaPool,
    vis: &mut [i64],
    lst: &mut [i64],
    lst_len: &mut usize,
    stk: &mut [i64],
    s: i64,
    gen: i64,
) {
    let mut sp = 0usize;
    stk[sp] = s;
    sp += 1;
    while sp > 0 {
        sp -= 1;
        let u = stk[sp];
        if u < 0 {
            continue;
        }
        let uu = u as usize;
        if vis[uu] == gen {
            continue;
        }
        vis[uu] = gen;
        if nfa.st_kind[uu] == -2 {
            stk[sp] = nfa.st_out2[uu];
            sp += 1;
            stk[sp] = nfa.st_out1[uu];
            sp += 1;
        } else {
            lst[*lst_len] = u;
            *lst_len += 1;
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn nfa_search(
    nfa: &NfaPool,
    start: i64,
    match_st: i64,
    text: &[i64],
    tlen: usize,
    vis: &mut [i64],
    gen_box: &mut i64,
    cur: &mut [i64],
    nxt: &mut [i64],
    stk: &mut [i64],
) -> bool {
    let mut gen = *gen_box + 1;
    let mut cur_len = 0usize;
    add_state(nfa, vis, cur, &mut cur_len, stk, start, gen);
    if vis[match_st as usize] == gen {
        *gen_box = gen;
        return true;
    }
    for i in 0..tlen {
        let c = text[i];
        gen += 1;
        let mut nxt_len = 0usize;
        for j in 0..cur_len {
            let u = cur[j] as usize;
            let k = nfa.st_kind[u];
            if k == c || k == -1 {
                add_state(nfa, vis, nxt, &mut nxt_len, stk, nfa.st_out1[u], gen);
            }
        }
        add_state(nfa, vis, nxt, &mut nxt_len, stk, start, gen);
        if vis[match_st as usize] == gen {
            *gen_box = gen;
            return true;
        }
        cur[..nxt_len].copy_from_slice(&nxt[..nxt_len]);
        cur_len = nxt_len;
    }
    *gen_box = gen;
    false
}

fn main() {
    let mut nfa = NfaPool::new();
    let patterns = [
        "ab+c",
        "(a|ab)*cd",
        "x..y*z",
        "(foo|bar)+baz",
        "a(b|c)+d?",
        "k(m|n)*p+q",
    ];
    for p in &patterns {
        nfa.compile_pattern(p);
    }
    let tokens = [
        "ab", "bc", "cd", "foo", "bar", "baz", "xyz", "x12y", "yz", "kmpq",
        "knppq", "abc", "abbc", "abd", "acd", "a", "b", "c", "d", "x",
        "y", "z", "k", "m", "n", "p", "q", "0", "_", "-",
    ];

    let n_st = nfa.st_kind.len();
    let mut vis = vec![0i64; n_st];
    let mut cur = vec![0i64; n_st];
    let mut nxt = vec![0i64; n_st];
    let mut stk = vec![0i64; n_st * 2];
    let mut gen_box: i64 = 0;
    let mut line = [0i64; 256];

    let mut rng: i64 = 2463534242;
    let mut matches: i64 = 0;
    let mut weighted: i64 = 0;
    for li in 0i64..6000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let n_tok = 8 + (rng % 10);
        let mut tlen = 0usize;
        for _ in 0..n_tok {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let tok = tokens[(rng % 30) as usize];
            for b in tok.bytes() {
                line[tlen] = b as i64;
                tlen += 1;
            }
        }
        for pi in 0..6usize {
            let s_st = nfa.start_st[pi];
            let m_st = nfa.match_st[pi];
            if nfa_search(&nfa, s_st, m_st, &line, tlen, &mut vis, &mut gen_box, &mut cur, &mut nxt, &mut stk) {
                matches += 1;
                weighted = (weighted + (li + 1) * ((pi as i64) + 1)) % 1000000007;
            }
        }
    }
    println!("{}\n{}", matches, weighted);
}
