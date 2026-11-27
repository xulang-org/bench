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
    let mut digs = [0i64; 16];
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

fn push_2d(buf: &mut Vec<i64>, v: i64) {
    buf.push(48 + (v / 10));
    buf.push(48 + (v % 10));
}

fn parse_val(doc: &[i64], start: usize, n: usize) -> (i64, usize) {
    let mut p = start;
    if doc[p] == 34 {
        p += 1;
        let mut vh: i64 = 17;
        while p < n && doc[p] != 34 {
            let mut ch = doc[p];
            if ch == 92 && p + 1 < n {
                p += 1;
                let e = doc[p];
                ch = if e == 110 { 10 } else if e == 116 { 9 } else if e == 34 { 34 } else if e == 92 { 92 } else { e };
            }
            vh = (vh * 131 + ch) % MOD_V;
            p += 1;
        }
        if p < n {
            p += 1;
        }
        return (vh, p);
    } else if doc[p] == 91 {
        p += 1;
        let mut ah: i64 = 29;
        while p < n {
            while p < n && (doc[p] == 32 || doc[p] == 9 || doc[p] == 44) {
                p += 1;
            }
            if p >= n || doc[p] == 93 {
                if p < n {
                    p += 1;
                }
                break;
            }
            let (ev, np) = parse_val(doc, p, n);
            ah = (ah * 257 + ev) % MOD_V;
            p = np;
        }
        return (ah, p);
    } else if doc[p] == 116 {
        return (1, p + 4);
    } else if doc[p] == 102 {
        return (0, p + 5);
    }
    let mut neg = false;
    if doc[p] == 45 {
        neg = true;
        p += 1;
    }
    let mut v: i64 = 0;
    while p < n && ((doc[p] >= 48 && doc[p] <= 57) || doc[p] == 95) {
        if doc[p] != 95 {
            v = v * 10 + (doc[p] - 48);
        }
        p += 1;
    }
    if neg {
        v = -v;
    }
    v %= MOD_V;
    if v < 0 {
        v += MOD_V;
    }
    (v, p)
}

fn main() {
    let mut doc: Vec<i64> = Vec::with_capacity(16384);
    push_str(&mut doc, "# Auto-generated microservice configuration\n");
    for s in 0i64..48 {
        push_str(&mut doc, "\n[svc_");
        push_2d(&mut doc, s);
        push_str(&mut doc, "]\n");
        push_str(&mut doc, "name = \"worker-");
        push_2d(&mut doc, s);
        push_str(&mut doc, "\\tprod\\n\\\"v");
        push_int(&mut doc, s % 5);
        push_str(&mut doc, "\\\"\" # inline comment\n");
        push_str(&mut doc, "port = ");
        push_int(&mut doc, 8000 + s * 10);
        doc.push(10);
        push_str(&mut doc, "max_conn = ");
        push_int(&mut doc, 1000 + (s % 7) * 500);
        doc.push(95);
        push_int(&mut doc, 100 + s);
        doc.push(10);
        if (s & 1) == 0 {
            push_str(&mut doc, "enabled = true\n");
        } else {
            push_str(&mut doc, "enabled = false\n");
        }
        if (s % 9) == 0 {
            push_str(&mut doc, "timeout_ms = -");
            push_int(&mut doc, 50 + s * 3);
            doc.push(10);
        } else {
            push_str(&mut doc, "timeout_ms = ");
            push_int(&mut doc, 250 + s * 15);
            doc.push(10);
        }
        push_str(&mut doc, "retries = [");
        push_int(&mut doc, 1 + (s % 3));
        push_str(&mut doc, ", ");
        push_int(&mut doc, 2 + (s % 5));
        push_str(&mut doc, ", ");
        push_int(&mut doc, 4 + (s % 7));
        push_str(&mut doc, ", ");
        push_int(&mut doc, 8 + (s % 11));
        push_str(&mut doc, "]\n");
        push_str(&mut doc, "endpoints = [\"/v1/s");
        push_int(&mut doc, s);
        push_str(&mut doc, "\", \"/health\\t");
        push_int(&mut doc, s);
        push_str(&mut doc, "\", \"/metrics\"]\n");
    }

    let n = doc.len();
    let mut total_entries: i64 = 0;
    let mut ck: i64 = 0;
    for rnd in 0i64..1000 {
        let mut pos = 0usize;
        let mut sec_hash: i64 = 0;
        let mut entries: i64 = 0;
        let mut round_ck: i64 = 0;
        while pos < n {
            while pos < n && (doc[pos] == 32 || doc[pos] == 9 || doc[pos] == 10 || doc[pos] == 13) {
                pos += 1;
            }
            if pos >= n {
                break;
            }
            let c = doc[pos];
            if c == 35 {
                while pos < n && doc[pos] != 10 {
                    pos += 1;
                }
                continue;
            }
            if c == 91 {
                pos += 1;
                let mut sh: i64 = 0;
                while pos < n && doc[pos] != 93 {
                    sh = (sh * 131 + doc[pos]) % MOD_V;
                    pos += 1;
                }
                if pos < n {
                    pos += 1;
                }
                sec_hash = sh;
                while pos < n && doc[pos] != 10 {
                    pos += 1;
                }
                continue;
            }
            let mut kh = sec_hash;
            while pos < n && doc[pos] != 61 && doc[pos] != 32 && doc[pos] != 9 && doc[pos] != 10 {
                kh = (kh * 131 + doc[pos]) % MOD_V;
                pos += 1;
            }
            while pos < n && (doc[pos] == 32 || doc[pos] == 9) {
                pos += 1;
            }
            if pos < n && doc[pos] == 61 {
                pos += 1;
            }
            while pos < n && (doc[pos] == 32 || doc[pos] == 9) {
                pos += 1;
            }
            let (vh, np) = parse_val(&doc, pos, n);
            pos = np;
            while pos < n && doc[pos] != 10 {
                pos += 1;
            }
            entries += 1;
            round_ck = (round_ck * 31 + (kh * 7 + vh + rnd) % MOD_V) % MOD_V;
        }
        total_entries += entries;
        ck = (ck * 37 + round_ck) % MOD_V;
    }
    println!("{total_entries}");
    println!("{ck}");
}
