const MASK32: i64 = 4294967295;

#[inline]
fn rotr32(x: i64, n: i64) -> i64 {
    ((x >> n) | ((x << (32 - n)) & MASK32)) & MASK32
}

fn sha256_block(state: &mut [i64], blk: &[i64], off: usize, w: &mut [i64], kv: &[i64]) {
    for t in 0..16 {
        let j = off + t * 4;
        w[t] = (blk[j] << 24) | (blk[j + 1] << 16) | (blk[j + 2] << 8) | blk[j + 3];
    }
    for t in 16..64 {
        let w15 = w[t - 15];
        let w2 = w[t - 2];
        let s0 = rotr32(w15, 7) ^ rotr32(w15, 18) ^ (w15 >> 3);
        let s1 = rotr32(w2, 17) ^ rotr32(w2, 19) ^ (w2 >> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) & MASK32;
    }
    let (mut a, mut b, mut c, mut d) = (state[0], state[1], state[2], state[3]);
    let (mut e, mut f, mut g, mut h) = (state[4], state[5], state[6], state[7]);
    for t in 0..64 {
        let bs1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25);
        let ch = (e & f) ^ ((e ^ MASK32) & g);
        let temp1 = (h + bs1 + ch + kv[t] + w[t]) & MASK32;
        let bs0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22);
        let maj = (a & b) ^ (a & c) ^ (b & c);
        let temp2 = (bs0 + maj) & MASK32;
        h = g;
        g = f;
        f = e;
        e = (d + temp1) & MASK32;
        d = c;
        c = b;
        b = a;
        a = (temp1 + temp2) & MASK32;
    }
    state[0] = (state[0] + a) & MASK32;
    state[1] = (state[1] + b) & MASK32;
    state[2] = (state[2] + c) & MASK32;
    state[3] = (state[3] + d) & MASK32;
    state[4] = (state[4] + e) & MASK32;
    state[5] = (state[5] + f) & MASK32;
    state[6] = (state[6] + g) & MASK32;
    state[7] = (state[7] + h) & MASK32;
}

fn sha256_compute(msg: &[i64], mlen: usize, state: &mut [i64], pad: &mut [i64], w: &mut [i64], kv: &[i64], iv: &[i64], out: &mut [i64]) {
    state[..8].copy_from_slice(&iv[..8]);
    let mut pos = 0usize;
    while pos + 64 <= mlen {
        sha256_block(state, msg, pos, w, kv);
        pos += 64;
    }
    let rem = mlen - pos;
    for pi in 0..rem {
        pad[pi] = msg[pos + pi];
    }
    pad[rem] = 128;
    let total_len = if rem >= 56 { 128 } else { 64 };
    for pi in (rem + 1)..(total_len - 8) {
        pad[pi] = 0;
    }
    let bitlen = (mlen as i64) * 8;
    for bi in 0..8 {
        pad[total_len - 8 + bi] = (bitlen >> ((7 - bi) * 8)) & 255;
    }
    sha256_block(state, pad, 0, w, kv);
    if total_len == 128 {
        sha256_block(state, pad, 64, w, kv);
    }
    for i in 0..8 {
        let sv = state[i];
        out[i * 4] = (sv >> 24) & 255;
        out[i * 4 + 1] = (sv >> 16) & 255;
        out[i * 4 + 2] = (sv >> 8) & 255;
        out[i * 4 + 3] = sv & 255;
    }
}

#[allow(clippy::too_many_arguments)]
fn hmac_sha256(
    key: &[i64], klen: usize, msg: &[i64], mlen: usize,
    ipad: &mut [i64], opad: &mut [i64], inner_buf: &mut [i64], outer_buf: &mut [i64],
    inner_hash: &mut [i64], state: &mut [i64], pad: &mut [i64], w: &mut [i64],
    kv: &[i64], iv: &[i64], out: &mut [i64],
) {
    for i in 0..64 {
        let kb = if i < klen { key[i] } else { 0 };
        ipad[i] = kb ^ 54;
        opad[i] = kb ^ 92;
        inner_buf[i] = ipad[i];
        outer_buf[i] = opad[i];
    }
    for i in 0..mlen {
        inner_buf[64 + i] = msg[i];
    }
    sha256_compute(inner_buf, 64 + mlen, state, pad, w, kv, iv, inner_hash);
    for i in 0..32 {
        outer_buf[64 + i] = inner_hash[i];
    }
    sha256_compute(outer_buf, 96, state, pad, w, kv, iv, out);
}

fn push_lit(buf: &mut Vec<i64>, s: &str) {
    for b in s.bytes() {
        buf.push(b as i64);
    }
}

fn push_nd(buf: &mut Vec<i64>, v: i64, digits: usize) {
    let mut tmp = [0i64; 8];
    let mut x = v;
    let mut i = digits;
    while i > 0 {
        i -= 1;
        tmp[i] = 48 + (x % 10);
        x /= 10;
    }
    for j in 0..digits {
        buf.push(tmp[j]);
    }
}

fn main() {
    let iv = [
        1779033703i64, 3144134277, 1013904242, 2773480762,
        1359893119, 2600822924, 528734635, 1541459225,
    ];
    let kv = [
        1116352408i64, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221,
        3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
        3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986,
        2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895,
        666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
        2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344,
        430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779,
        1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298,
    ];

    let mut state = [0i64; 8];
    let mut w = [0i64; 64];
    let mut pad = [0i64; 128];
    let mut ipad = [0i64; 64];
    let mut opad = [0i64; 64];
    let mut inner_buf = [0i64; 256];
    let mut outer_buf = [0i64; 256];
    let mut inner_hash = [0i64; 32];
    let mut dk = [0i64; 32];
    let mut u_buf = [0i64; 32];
    let mut acc = [0i64; 32];

    let mut pw: Vec<i64> = Vec::with_capacity(64);
    let mut salt: Vec<i64> = Vec::with_capacity(64);
    let mut key: Vec<i64> = Vec::with_capacity(64);
    let mut msg: Vec<i64> = Vec::with_capacity(128);
    let mut ops: i64 = 0;

    for i in 0i64..80 {
        pw.clear();
        push_lit(&mut pw, "xu-pass-");
        push_nd(&mut pw, i, 3);
        push_lit(&mut pw, "-secret");

        salt.clear();
        push_lit(&mut salt, "salt-");
        push_nd(&mut salt, i * 7, 4);
        push_lit(&mut salt, "-v1");
        salt.push(0); salt.push(0); salt.push(0); salt.push(1);

        hmac_sha256(&pw, pw.len(), &salt, salt.len(), &mut ipad, &mut opad, &mut inner_buf, &mut outer_buf, &mut inner_hash, &mut state, &mut pad, &mut w, &kv, &iv, &mut u_buf);
        dk.copy_from_slice(&u_buf);
        for _ in 1..1000 {
            let u_copy = u_buf;
            hmac_sha256(&pw, pw.len(), &u_copy, 32, &mut ipad, &mut opad, &mut inner_buf, &mut outer_buf, &mut inner_hash, &mut state, &mut pad, &mut w, &kv, &iv, &mut u_buf);
            for bi in 0..32 {
                dk[bi] ^= u_buf[bi];
            }
        }
        for bi in 0..32 {
            acc[bi] ^= dk[bi];
        }
        ops += 1;
    }

    for i in 0i64..200 {
        key.clear();
        push_lit(&mut key, "jwt-hmac-key-");
        push_nd(&mut key, i % 16, 2);

        msg.clear();
        push_lit(&mut msg, "eyJhbGciOiJIUzI1NiJ9.sub=user_");
        push_nd(&mut msg, i, 4);
        push_lit(&mut msg, "&seq=");
        push_nd(&mut msg, i * 37, 5);

        hmac_sha256(&key, key.len(), &msg, msg.len(), &mut ipad, &mut opad, &mut inner_buf, &mut outer_buf, &mut inner_hash, &mut state, &mut pad, &mut w, &kv, &iv, &mut u_buf);
        for bi in 0..32 {
            acc[bi] ^= u_buf[bi];
        }
        ops += 1;
    }

    println!("{ops}");
    let hex_chars = b"0123456789abcdef";
    let mut s = String::with_capacity(64);
    for &v in &acc {
        s.push(hex_chars[((v >> 4) & 15) as usize] as char);
        s.push(hex_chars[(v & 15) as usize] as char);
    }
    println!("{s}");
}
