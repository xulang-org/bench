fn md5_step(state: &mut [u32; 4], block: &[u8; 64]) {
    let mut a = state[0];
    let mut b = state[1];
    let mut c = state[2];
    let mut d = state[3];

    let mut x = [0u32; 16];
    for i in 0..16 {
        x[i] = u32::from_le_bytes([
            block[i * 4],
            block[i * 4 + 1],
            block[i * 4 + 2],
            block[i * 4 + 3],
        ]);
    }

    macro_rules! round1 {
        ($a:ident, $b:ident, $c:ident, $d:ident, $k:expr, $s:expr, $t:expr) => {
            $a = $a.wrapping_add((($b & $c) | ((!$b) & $d)).wrapping_add(x[$k]).wrapping_add($t));
            $a = $a.rotate_left($s).wrapping_add($b);
        };
    }
    macro_rules! round2 {
        ($a:ident, $b:ident, $c:ident, $d:ident, $k:expr, $s:expr, $t:expr) => {
            $a = $a.wrapping_add((($b & $d) | ($c & (!$d))).wrapping_add(x[$k]).wrapping_add($t));
            $a = $a.rotate_left($s).wrapping_add($b);
        };
    }
    macro_rules! round3 {
        ($a:ident, $b:ident, $c:ident, $d:ident, $k:expr, $s:expr, $t:expr) => {
            $a = $a.wrapping_add(($b ^ $c ^ $d).wrapping_add(x[$k]).wrapping_add($t));
            $a = $a.rotate_left($s).wrapping_add($b);
        };
    }
    macro_rules! round4 {
        ($a:ident, $b:ident, $c:ident, $d:ident, $k:expr, $s:expr, $t:expr) => {
            $a = $a.wrapping_add(($c ^ ($b | (!$d))).wrapping_add(x[$k]).wrapping_add($t));
            $a = $a.rotate_left($s).wrapping_add($b);
        };
    }

    round1!(a, b, c, d,  0,  7, 0xd76aa478); round1!(d, a, b, c,  1, 12, 0xe8c7b756);
    round1!(c, d, a, b,  2, 17, 0x242070db); round1!(b, c, d, a,  3, 22, 0xc1bdceee);
    round1!(a, b, c, d,  4,  7, 0xf57c0faf); round1!(d, a, b, c,  5, 12, 0x4787c62a);
    round1!(c, d, a, b,  6, 17, 0xa8304613); round1!(b, c, d, a,  7, 22, 0xfd469501);
    round1!(a, b, c, d,  8,  7, 0x698098d8); round1!(d, a, b, c,  9, 12, 0x8b44f7af);
    round1!(c, d, a, b, 10, 17, 0xffff5bb1); round1!(b, c, d, a, 11, 22, 0x895cd7be);
    round1!(a, b, c, d, 12,  7, 0x6b901122); round1!(d, a, b, c, 13, 12, 0xfd987193);
    round1!(c, d, a, b, 14, 17, 0xa679438e); round1!(b, c, d, a, 15, 22, 0x49b40821);

    round2!(a, b, c, d,  1,  5, 0xf61e2562); round2!(d, a, b, c,  6,  9, 0xc040b340);
    round2!(c, d, a, b, 11, 14, 0x265e5a51); round2!(b, c, d, a,  0, 20, 0xe9b6c7aa);
    round2!(a, b, c, d,  5,  5, 0xd62f105d); round2!(d, a, b, c, 10,  9, 0x02441453);
    round2!(c, d, a, b, 15, 14, 0xd8a1e681); round2!(b, c, d, a,  4, 20, 0xe7d3fbc8);
    round2!(a, b, c, d,  9,  5, 0x21e1cde6); round2!(d, a, b, c, 14,  9, 0xc33707d6);
    round2!(c, d, a, b,  3, 14, 0xf4d50d87); round2!(b, c, d, a,  8, 20, 0x455a14ed);
    round2!(a, b, c, d, 13,  5, 0xa9e3e905); round2!(d, a, b, c,  2,  9, 0xfcefa3f8);
    round2!(c, d, a, b,  7, 14, 0x676f02d9); round2!(b, c, d, a, 12, 20, 0x8d2a4c8a);

    round3!(a, b, c, d,  5,  4, 0xfffa3942); round3!(d, a, b, c,  8, 11, 0x8771f681);
    round3!(c, d, a, b, 11, 16, 0x6d9d6122); round3!(b, c, d, a, 14, 23, 0xfde5380c);
    round3!(a, b, c, d,  1,  4, 0xa4beea44); round3!(d, a, b, c,  4, 11, 0x4bdecfa9);
    round3!(c, d, a, b,  7, 16, 0xf6bb4b60); round3!(b, c, d, a, 10, 23, 0xbebfbc70);
    round3!(a, b, c, d, 13,  4, 0x289b7ec6); round3!(d, a, b, c,  0, 11, 0xeaa127fa);
    round3!(c, d, a, b,  3, 16, 0xd4ef3085); round3!(b, c, d, a,  6, 23, 0x04881d05);
    round3!(a, b, c, d,  9,  4, 0xd9d4d039); round3!(d, a, b, c, 12, 11, 0xe6db99e5);
    round3!(c, d, a, b, 15, 16, 0x1fa27cf8); round3!(b, c, d, a,  2, 23, 0xc4ac5665);

    round4!(a, b, c, d,  0,  6, 0xf4292244); round4!(d, a, b, c,  7, 10, 0x432aff97);
    round4!(c, d, a, b, 14, 15, 0xab9423a7); round4!(b, c, d, a,  5, 21, 0xfc93a039);
    round4!(a, b, c, d, 12,  6, 0x655b59c3); round4!(d, a, b, c,  3, 10, 0x8f0ccc92);
    round4!(c, d, a, b, 10, 15, 0xffeff47d); round4!(b, c, d, a,  1, 21, 0x85845dd1);
    round4!(a, b, c, d,  8,  6, 0x6fa87e4f); round4!(d, a, b, c, 15, 10, 0xfe2ce6e0);
    round4!(c, d, a, b,  6, 15, 0xa3014314); round4!(b, c, d, a, 13, 21, 0x4e0811a1);
    round4!(a, b, c, d,  4,  6, 0xf7537e82); round4!(d, a, b, c, 11, 10, 0xbd3af235);
    round4!(c, d, a, b,  2, 15, 0x2ad7d2bb); round4!(b, c, d, a,  9, 21, 0xeb86d391);

    state[0] = state[0].wrapping_add(a);
    state[1] = state[1].wrapping_add(b);
    state[2] = state[2].wrapping_add(c);
    state[3] = state[3].wrapping_add(d);
}

fn md5_sum(msg: &[u8]) -> [u8; 16] {
    let mut state = [0x67452301u32, 0xefcdab89u32, 0x98badcfeu32, 0x10325476u32];
    let bit_len = (msg.len() as u64) * 8;
    let mut padded = Vec::with_capacity(msg.len() + 64);
    padded.extend_from_slice(msg);
    padded.push(0x80);
    while (padded.len() % 64) != 56 {
        padded.push(0x00);
    }
    padded.extend_from_slice(&bit_len.to_le_bytes());

    for chunk in padded.chunks_exact(64) {
        let mut block = [0u8; 64];
        block.copy_from_slice(chunk);
        md5_step(&mut state, &block);
    }

    let mut out = [0u8; 16];
    for i in 0..4 {
        out[i * 4..(i + 1) * 4].copy_from_slice(&state[i].to_le_bytes());
    }
    out
}

const HEX_CHARS: &[u8; 16] = b"0123456789abcdef";

fn hex_str(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        s.push(HEX_CHARS[(b >> 4) as usize] as char);
        s.push(HEX_CHARS[(b & 0x0f) as usize] as char);
    }
    s
}

fn main() {
    let mut h = "The quick brown fox jumps over the lazy dog".to_string();
    for _ in 0..100000 {
        let digest = md5_sum(h.as_bytes());
        h = hex_str(&digest);
    }
    println!("{}", h);
}
