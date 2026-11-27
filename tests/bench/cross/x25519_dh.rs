fn car25519(o: &mut [i64; 16]) {
    for i in 0..16 {
        let c = o[i] >> 16;
        o[i] &= 65535;
        if i < 15 {
            o[i + 1] += c;
        } else {
            o[0] += c * 38;
        }
    }
}

fn fadd_new(o: &mut [i64; 16], a: &[i64; 16], b: &[i64; 16]) {
    for i in 0..16 {
        o[i] = a[i] + b[i];
    }
}

fn fsub_new(o: &mut [i64; 16], a: &[i64; 16], b: &[i64; 16]) {
    o[0] = a[0] + 130996 - b[0];
    for i in 1..16 {
        o[i] = a[i] + 131070 - b[i];
    }
    car25519(o);
}

fn fsub_self(a: &mut [i64; 16], b: &[i64; 16]) {
    a[0] = a[0] + 130996 - b[0];
    for i in 1..16 {
        a[i] = a[i] + 131070 - b[i];
    }
    car25519(a);
}

fn fmul_core(o: &mut [i64; 16], a: &[i64; 16], b: &[i64; 16]) {
    let mut t = [0i64; 32];
    for i in 0..16 {
        let ai = a[i];
        for j in 0..16 {
            t[i + j] += ai * b[j];
        }
    }
    for i in 0..16 {
        o[i] = t[i] + 38 * t[i + 16];
    }
    car25519(o);
    car25519(o);
}

fn fmul_self(a: &mut [i64; 16], b: &[i64; 16]) {
    let mut t = [0i64; 32];
    for i in 0..16 {
        let ai = a[i];
        for j in 0..16 {
            t[i + j] += ai * b[j];
        }
    }
    for i in 0..16 {
        a[i] = t[i] + 38 * t[i + 16];
    }
    car25519(a);
    car25519(a);
}

fn fsq_self(a: &mut [i64; 16]) {
    let mut t = [0i64; 32];
    for i in 0..16 {
        let ai = a[i];
        for j in 0..16 {
            t[i + j] += ai * a[j];
        }
    }
    for i in 0..16 {
        a[i] = t[i] + 38 * t[i + 16];
    }
    car25519(a);
    car25519(a);
}

fn fsq_new(o: &mut [i64; 16], a: &[i64; 16]) {
    fmul_core(o, a, a);
}

fn cswap(p: &mut [i64; 16], q: &mut [i64; 16], bit: i64) {
    if bit != 0 {
        for i in 0..16 {
            let tmp = p[i];
            p[i] = q[i];
            q[i] = tmp;
        }
    }
}

fn finv(o: &mut [i64; 16], in_v: &[i64; 16]) {
    let mut c = *in_v;
    let mut a = 253i64;
    while a >= 0 {
        fsq_self(&mut c);
        if a != 2 && a != 4 {
            fmul_self(&mut c, in_v);
        }
        a -= 1;
    }
    *o = c;
}

fn pack25519(o: &mut [i64; 32], n_in: &[i64; 16]) {
    let mut t = *n_in;
    car25519(&mut t);
    car25519(&mut t);
    car25519(&mut t);
    let mut m = [0i64; 16];
    for _pass in 0..2 {
        m[0] = t[0] - 65517;
        let mut borrow = if m[0] < 0 {
            m[0] += 65536;
            1
        } else {
            0
        };
        for i in 1..15 {
            m[i] = t[i] - 65535 - borrow;
            if m[i] < 0 {
                m[i] += 65536;
                borrow = 1;
            } else {
                borrow = 0;
            }
        }
        m[15] = t[15] - 32767 - borrow;
        if m[15] >= 0 {
            t = m;
        }
    }
    for i in 0..16 {
        o[2 * i] = t[i] & 255;
        o[2 * i + 1] = (t[i] >> 8) & 255;
    }
}

fn x25519(q: &mut [i64; 32], n_bytes: &[i64; 32], p_bytes: &[i64; 32], a24: &[i64; 16]) {
    let mut z = *n_bytes;
    z[0] &= 248;
    z[31] = (z[31] & 127) | 64;

    let mut x = [0i64; 16];
    for i in 0..16 {
        x[i] = p_bytes[2 * i] | (p_bytes[2 * i + 1] << 8);
    }
    x[15] &= 32767;

    let mut a = [0i64; 16];
    let mut b = x;
    let mut c = [0i64; 16];
    let mut d = [0i64; 16];
    let mut e = [0i64; 16];
    let mut f = [0i64; 16];
    a[0] = 1;
    d[0] = 1;

    let mut bit_i = 254isize;
    while bit_i >= 0 {
        let r = (z[(bit_i >> 3) as usize] >> (bit_i & 7)) & 1;
        cswap(&mut a, &mut b, r);
        cswap(&mut c, &mut d, r);
        fadd_new(&mut e, &a, &c);
        fsub_self(&mut a, &c);
        fadd_new(&mut c, &b, &d);
        fsub_self(&mut b, &d);
        fsq_new(&mut d, &e);
        fsq_new(&mut f, &a);
        fmul_self(&mut a, &c);
        fmul_core(&mut c, &b, &e);
        e = a;
        for ii in 0..16 {
            e[ii] += c[ii];
        }
        fsub_self(&mut a, &c);
        fsq_new(&mut b, &a);
        fsub_new(&mut c, &d, &f);
        fmul_core(&mut a, &c, a24);
        for ii in 0..16 {
            a[ii] += d[ii];
        }
        fmul_self(&mut c, &a);
        fmul_core(&mut a, &d, &f);
        fmul_core(&mut d, &b, &x);
        fsq_new(&mut b, &e);
        cswap(&mut a, &mut b, r);
        cswap(&mut c, &mut d, r);
        bit_i -= 1;
    }
    e = c;
    finv(&mut c, &e);
    fmul_self(&mut a, &c);
    pack25519(q, &a);
}

fn main() {
    let mut a24 = [0i64; 16];
    a24[0] = 56129;
    a24[1] = 1;

    let mut k = [0i64; 32];
    let mut u = [0i64; 32];
    let mut out = [0i64; 32];
    k[0] = 9;
    u[0] = 9;

    for _step in 0..100 {
        x25519(&mut out, &k, &u, &a24);
        u = k;
        k = out;
    }

    println!("100");
    for i in 0..32 {
        print!("{:02x}", k[i]);
    }
    println!();
}
