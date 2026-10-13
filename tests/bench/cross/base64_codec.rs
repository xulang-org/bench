const B64_TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

fn b64_val(c: u8) -> i32 {
    if c >= b'A' && c <= b'Z' {
        (c - b'A') as i32
    } else if c >= b'a' && c <= b'z' {
        (c - b'a' + 26) as i32
    } else if c >= b'0' && c <= b'9' {
        (c - b'0' + 52) as i32
    } else if c == b'+' {
        62
    } else if c == b'/' {
        63
    } else {
        -1
    }
}

fn main() {
    let base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP";
    let payload = base.repeat(6);
    let payload_bytes = payload.as_bytes();
    let payload_len = payload_bytes.len(); // 384
    let enc_len = (payload_len + 2) / 3 * 4; // 512

    let mut enc = vec![0u8; enc_len];
    let mut dec = vec![0u8; payload_len];

    let mut total: i64 = 0;

    for i in 0..15000 {
        // Encode
        let mut di = 0;
        let mut si = 0;
        while si < payload_len {
            let b0 = payload_bytes[si] as u32;
            let b1 = payload_bytes[si + 1] as u32;
            let b2 = payload_bytes[si + 2] as u32;
            let triple = (b0 << 16) | (b1 << 8) | b2;
            enc[di] = B64_TABLE[((triple >> 18) & 0x3f) as usize];
            enc[di + 1] = B64_TABLE[((triple >> 12) & 0x3f) as usize];
            enc[di + 2] = B64_TABLE[((triple >> 6) & 0x3f) as usize];
            enc[di + 3] = B64_TABLE[(triple & 0x3f) as usize];
            di += 4;
            si += 3;
        }

        // Decode
        let mut out_i = 0;
        let mut ei = 0;
        while ei < enc_len {
            let v0 = b64_val(enc[ei]) as u32;
            let v1 = b64_val(enc[ei + 1]) as u32;
            let v2 = b64_val(enc[ei + 2]) as u32;
            let v3 = b64_val(enc[ei + 3]) as u32;
            let triple = (v0 << 18) | (v1 << 12) | (v2 << 6) | v3;
            dec[out_i] = ((triple >> 16) & 0xff) as u8;
            dec[out_i + 1] = ((triple >> 8) & 0xff) as u8;
            dec[out_i + 2] = (triple & 0xff) as u8;
            out_i += 3;
            ei += 4;
        }

        total += enc_len as i64 + out_i as i64;
        if i == 0 {
            total += dec[0] as i64 + dec[out_i - 1] as i64;
        }
    }

    println!("{}", total);
}
