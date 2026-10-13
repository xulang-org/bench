#[inline(always)]
fn rotl32(v: u32, c: u32) -> u32 {
    v.rotate_left(c)
}

#[inline(always)]
fn qr(s: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize) {
    s[a] = s[a].wrapping_add(s[b]);
    s[d] = rotl32(s[d] ^ s[a], 16);
    s[c] = s[c].wrapping_add(s[d]);
    s[b] = rotl32(s[b] ^ s[c], 12);
    s[a] = s[a].wrapping_add(s[b]);
    s[d] = rotl32(s[d] ^ s[a], 8);
    s[c] = s[c].wrapping_add(s[d]);
    s[b] = rotl32(s[b] ^ s[c], 7);
}

fn main() {
    let mut key = [0u32; 8];
    for i in 0..8 {
        key[i] = (i as u32).wrapping_mul(16843009);
    }
    let nonce0 = 305419896u32;
    let nonce1 = 2596069104u32;
    let nonce2 = 267246505u32;

    let rounds = 30000;
    let mut total_sum = 0u32;
    let mut s = [0u32; 16];

    for block in 0..rounds {
        s[0] = 1634760805;
        s[1] = 857760878;
        s[2] = 2036477234;
        s[3] = 1797285236;
        for k in 0..8 {
            s[4 + k] = key[k].wrapping_add(block as u32);
        }
        s[12] = block as u32;
        s[13] = nonce0;
        s[14] = nonce1;
        s[15] = nonce2;

        for _ in 0..10 {
            qr(&mut s, 0, 4, 8, 12);
            qr(&mut s, 1, 5, 9, 13);
            qr(&mut s, 2, 6, 10, 14);
            qr(&mut s, 3, 7, 11, 15);
            qr(&mut s, 0, 5, 10, 15);
            qr(&mut s, 1, 6, 11, 12);
            qr(&mut s, 2, 7, 8, 13);
            qr(&mut s, 3, 4, 9, 14);
        }
        total_sum = total_sum.wrapping_add(s[0]).wrapping_add(s[5]).wrapping_add(s[10]).wrapping_add(s[15]);
    }
    println!("{}", total_sum);
}
