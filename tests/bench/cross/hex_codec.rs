const HEX_DIGITS: &[u8; 16] = b"0123456789abcdef";

fn hex_val(c: u8) -> i32 {
    if c >= b'0' && c <= b'9' {
        (c - b'0') as i32
    } else if c >= b'a' && c <= b'f' {
        (c - b'a' + 10) as i32
    } else if c >= b'A' && c <= b'F' {
        (c - b'A' + 10) as i32
    } else {
        -1
    }
}

fn main() {
    let base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP";
    let payload = base.repeat(8);
    let payload_bytes = payload.as_bytes();
    let n = payload_bytes.len();
    let mut total: i64 = 0;

    let mut enc = vec![0u8; n * 2];
    let mut dec = vec![0u8; n];

    for i in 0..25000 {
        for j in 0..n {
            let c = payload_bytes[j];
            enc[2 * j] = HEX_DIGITS[(c >> 4) as usize];
            enc[2 * j + 1] = HEX_DIGITS[(c & 0x0f) as usize];
        }
        let enc_len = enc.len() as i64;

        for j in 0..n {
            let hi = hex_val(enc[2 * j]);
            let lo = hex_val(enc[2 * j + 1]);
            dec[j] = ((hi << 4) | lo) as u8;
        }
        let dec_len = dec.len() as i64;

        total += enc_len + dec_len;
        if i == 0 {
            total += dec[0] as i64 + dec[dec.len() - 1] as i64;
        }
    }

    println!("{}", total);
}
