const MOD_V: i64 = 1000000007;

fn to_bytes(s: &str) -> Vec<i64> {
    s.bytes().map(|b| b as i64).collect()
}

fn emit_raw(out: &mut Vec<i64>, s: &[i64], start: usize, ln: usize) {
    out.extend_from_slice(&s[start..(start + ln)]);
}

fn emit_esc(out: &mut Vec<i64>, s: &[i64]) {
    for &ch in s {
        match ch {
            38 => out.extend_from_slice(&[38, 97, 109, 112, 59]),
            60 => out.extend_from_slice(&[38, 108, 116, 59]),
            62 => out.extend_from_slice(&[38, 103, 116, 59]),
            34 => out.extend_from_slice(&[38, 113, 117, 111, 116, 59]),
            39 => out.extend_from_slice(&[38, 35, 51, 57, 59]),
            _ => out.push(ch),
        }
    }
}

fn match_bytes(src: &[i64], s: usize, e: usize, pat: &str) -> bool {
    let mut a = s;
    let mut b = e;
    while a < b && (src[a] == 32 || src[a] == 9) {
        a += 1;
    }
    while b > a && (src[b - 1] == 32 || src[b - 1] == 9) {
        b -= 1;
    }
    let pb = pat.as_bytes();
    if b - a != pb.len() {
        return false;
    }
    (0..pb.len()).all(|i| src[a + i] == pb[i] as i64)
}

fn var_id(src: &[i64], s: usize, e: usize) -> usize {
    if match_bytes(src, s, e, "title") { return 0; }
    if match_bytes(src, s, e, "badge") { return 1; }
    if match_bytes(src, s, e, "name") { return 2; }
    if match_bytes(src, s, e, "desc") { return 3; }
    99
}

fn main() {
    let tmpl = to_bytes("<div class=\"card\"><h1>{{title}}</h1>{{{badge}}}<ul>{%for item%}<li class=\"{%if featured%}hot{%else%}std{%endif%}\"><span>{{name}}</span><em>{{desc}}</em></li>{%endfor%}</ul></div>");
    let tlen = tmpl.len();

    let titles = [
        to_bytes("Xu <Fast> & Safe"),
        to_bytes("Bench \"Suite\" 'v1'"),
        to_bytes("Release & Notes <2026>"),
        to_bytes("Core / Engine"),
    ];
    let badges = [
        to_bytes("<b>PRO</b>"),
        to_bytes("<i>LTS</i>"),
        to_bytes("<span>NEW</span>"),
        to_bytes("<b>OK</b>"),
    ];
    let names = [
        to_bytes("Item <alpha> & 1"),
        to_bytes("Widget \"beta\""),
        to_bytes("Node 'gamma' > 0"),
        to_bytes("Cache & Pool"),
        to_bytes("Router <v2>"),
        to_bytes("Codec \"lz4\""),
        to_bytes("Parser 'ast'"),
        to_bytes("Engine <core>"),
    ];
    let descs = [
        to_bytes("a < b && c > d"),
        to_bytes("quote \"here\" & 'there'"),
        to_bytes("plain fast path"),
        to_bytes("x & y < z"),
    ];

    let mut op_kind: Vec<usize> = Vec::with_capacity(64);
    let mut op_a: Vec<usize> = Vec::with_capacity(64);
    let mut op_b: Vec<usize> = Vec::with_capacity(64);
    let mut for_stack = [0usize; 8];
    let mut if_stack = [0usize; 8];
    let mut else_stack = [0isize; 8];
    let mut out: Vec<i64> = Vec::with_capacity(2048);

    let mut total_bytes: i64 = 0;
    let mut ck: i64 = 0;
    for rnd in 0usize..400 {
        op_kind.clear();
        op_a.clear();
        op_b.clear();
        let (mut for_sp, mut if_sp, mut pos) = (0usize, 0usize, 0usize);
        while pos < tlen {
            let mut np = pos;
            while np + 1 < tlen && !(tmpl[np] == 123 && (tmpl[np + 1] == 123 || tmpl[np + 1] == 37)) {
                np += 1;
            }
            if np + 1 >= tlen {
                np = tlen;
            }
            if np > pos {
                op_kind.push(0);
                op_a.push(pos);
                op_b.push(np - pos);
                pos = np;
            }
            if pos >= tlen {
                break;
            }
            if tmpl[pos + 1] == 123 {
                if pos + 2 < tlen && tmpl[pos + 2] == 123 {
                    let mut end = pos + 3;
                    while !(tmpl[end] == 125 && tmpl[end + 1] == 125 && tmpl[end + 2] == 125) {
                        end += 1;
                    }
                    op_kind.push(2);
                    op_a.push(var_id(&tmpl, pos + 3, end));
                    op_b.push(0);
                    pos = end + 3;
                } else {
                    let mut end = pos + 2;
                    while !(tmpl[end] == 125 && tmpl[end + 1] == 125) {
                        end += 1;
                    }
                    op_kind.push(1);
                    op_a.push(var_id(&tmpl, pos + 2, end));
                    op_b.push(0);
                    pos = end + 2;
                }
            } else {
                let mut end = pos + 2;
                while !(tmpl[end] == 37 && tmpl[end + 1] == 125) {
                    end += 1;
                }
                let ts = pos + 2;
                if match_bytes(&tmpl, ts, end, "for item") {
                    for_stack[for_sp] = op_kind.len();
                    for_sp += 1;
                    op_kind.push(3);
                    op_a.push(0);
                    op_b.push(0);
                } else if match_bytes(&tmpl, ts, end, "endfor") {
                    for_sp -= 1;
                    let fidx = for_stack[for_sp];
                    op_kind.push(4);
                    op_a.push(fidx + 1);
                    op_b.push(0);
                    op_a[fidx] = op_kind.len();
                } else if match_bytes(&tmpl, ts, end, "if featured") {
                    if_stack[if_sp] = op_kind.len();
                    else_stack[if_sp] = -1;
                    if_sp += 1;
                    op_kind.push(5);
                    op_a.push(0);
                    op_b.push(0);
                } else if match_bytes(&tmpl, ts, end, "else") {
                    let eidx = op_kind.len();
                    op_kind.push(6);
                    op_a.push(0);
                    op_b.push(0);
                    let iidx = if_stack[if_sp - 1];
                    op_a[iidx] = eidx + 1;
                    else_stack[if_sp - 1] = eidx as isize;
                } else if match_bytes(&tmpl, ts, end, "endif") {
                    if_sp -= 1;
                    let iidx = if_stack[if_sp];
                    let eidx = else_stack[if_sp];
                    if eidx >= 0 {
                        op_a[eidx as usize] = op_kind.len();
                    } else {
                        op_a[iidx] = op_kind.len();
                    }
                    op_kind.push(7);
                    op_a.push(0);
                    op_b.push(0);
                }
                pos = end + 2;
            }
        }

        let n_ops = op_kind.len();
        for page in 0usize..25 {
            let title_v = &titles[(rnd + page) & 3];
            let badge_v = &badges[(rnd * 3 + page) & 3];
            out.clear();
            let mut pc = 0usize;
            let mut item_idx = 0usize;
            let item_cnt = 12usize;
            while pc < n_ops {
                let op = op_kind[pc];
                let a = op_a[pc];
                match op {
                    0 => { emit_raw(&mut out, &tmpl, a, op_b[pc]); pc += 1; }
                    1 => {
                        if a == 0 { emit_esc(&mut out, title_v); }
                        else if a == 2 { emit_esc(&mut out, &names[(page + item_idx + rnd) & 7]); }
                        else if a == 3 { emit_esc(&mut out, &descs[(page * 3 + item_idx + rnd) & 3]); }
                        pc += 1;
                    }
                    2 => { if a == 1 { emit_raw(&mut out, badge_v, 0, badge_v.len()); } pc += 1; }
                    3 => { if item_cnt == 0 { pc = a; } else { item_idx = 0; pc += 1; } }
                    4 => { item_idx += 1; if item_idx < item_cnt { pc = a; } else { pc += 1; } }
                    5 => { if ((rnd + page + item_idx) % 3) == 0 { pc += 1; } else { pc = a; } }
                    6 => { pc = a; }
                    _ => { pc += 1; }
                }
            }
            total_bytes += out.len() as i64;
            let mut h: i64 = 0;
            for &b in &out {
                h = (h * 131 + b) % MOD_V;
            }
            ck = (ck * 31 + h) % MOD_V;
        }
    }
    println!("{total_bytes}");
    println!("{ck}");
}
