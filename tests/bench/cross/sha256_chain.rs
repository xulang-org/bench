const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

fn rotr(x: u32, n: u32) -> u32 {
    x.rotate_right(n)
}

fn sha256_transform(st: &mut [u32; 8], blk: &[u8]) {
    let mut w = [0u32; 64];
    for i in 0..16 {
        let o = i * 4;
        w[i] = u32::from_be_bytes([blk[o], blk[o + 1], blk[o + 2], blk[o + 3]]);
    }
    for i in 16..64 {
        let s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
        let s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16]
            .wrapping_add(s0)
            .wrapping_add(w[i - 7])
            .wrapping_add(s1);
    }
    let mut a = st[0];
    let mut b = st[1];
    let mut c = st[2];
    let mut d = st[3];
    let mut e = st[4];
    let mut f = st[5];
    let mut g = st[6];
    let mut h = st[7];
    for i in 0..64 {
        let s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        let ch = (e & f) ^ ((!e) & g);
        let t1 = h
            .wrapping_add(s1)
            .wrapping_add(ch)
            .wrapping_add(K[i])
            .wrapping_add(w[i]);
        let s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        let maj = (a & b) ^ (a & c) ^ (b & c);
        let t2 = s0.wrapping_add(maj);
        h = g;
        g = f;
        f = e;
        e = d.wrapping_add(t1);
        d = c;
        c = b;
        b = a;
        a = t1.wrapping_add(t2);
    }
    st[0] = st[0].wrapping_add(a);
    st[1] = st[1].wrapping_add(b);
    st[2] = st[2].wrapping_add(c);
    st[3] = st[3].wrapping_add(d);
    st[4] = st[4].wrapping_add(e);
    st[5] = st[5].wrapping_add(f);
    st[6] = st[6].wrapping_add(g);
    st[7] = st[7].wrapping_add(h);
}

fn sha256(msg: &[u8]) -> [u8; 32] {
    let mut st: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let mut i = 0usize;
    while i + 64 <= msg.len() {
        sha256_transform(&mut st, &msg[i..i + 64]);
        i += 64;
    }
    let rem = msg.len() - i;
    let mut blk = [0u8; 64];
    blk[..rem].copy_from_slice(&msg[i..]);
    blk[rem] = 0x80;
    let bits = (msg.len() as u64) * 8;
    if rem >= 56 {
        sha256_transform(&mut st, &blk);
        blk = [0u8; 64];
    }
    blk[56..64].copy_from_slice(&bits.to_be_bytes());
    sha256_transform(&mut st, &blk);
    let mut out = [0u8; 32];
    for j in 0..8 {
        out[j * 4..j * 4 + 4].copy_from_slice(&st[j].to_be_bytes());
    }
    out
}

fn hex32(d: &[u8; 32]) -> String {
    const H: &[u8] = b"0123456789abcdef";
    let mut s = String::with_capacity(64);
    for b in d {
        s.push(H[(b >> 4) as usize] as char);
        s.push(H[(b & 15) as usize] as char);
    }
    s
}

fn main() {
    let chunk = b"The quick brown fox jumps over the lazy dog. 0123456789.";
    let mut body = Vec::new();
    let mut i: i64 = 0;
    while i < 1024 {
        body.extend_from_slice(chunk);
        i += 1;
    }
    let mut h = hex32(&sha256(&body));
    let mut r: i64 = 0;
    while r < 4 {
        let mut cat = Vec::with_capacity(64 + body.len());
        cat.extend_from_slice(h.as_bytes());
        cat.extend_from_slice(&body);
        h = hex32(&sha256(&cat));
        r += 1;
    }
    println!("{}", h);
}
