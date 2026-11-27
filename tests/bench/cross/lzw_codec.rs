const LZW_CLEAR: u32 = 256;
const LZW_EOF: u32 = 257;
const LZW_MAX_WIDTH: u32 = 12;
const LZW_MAX_CODE: u32 = 4095;
const LZW_INVALID: u32 = 65535;

#[inline(always)]
fn emit_lsb(out: &mut Vec<u8>, code: u32, width: u32, bits: &mut u32, nbits: &mut u32) {
    *bits |= code << *nbits;
    *nbits += width;
    while *nbits >= 8 {
        out.push((*bits & 0xff) as u8);
        *bits >>= 8;
        *nbits -= 8;
    }
}

fn lzw_encode(src: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(src.len() + 64);
    let mut width: u32 = 9;
    let mut hi: u32 = LZW_EOF;
    let mut overflow: u32 = 1u32 << width;
    let mut bits: u32 = 0;
    let mut nbits: u32 = 0;

    let mut head = [0usize; 4096];
    let mut keys: Vec<u32> = Vec::with_capacity(512);
    let mut vals: Vec<u16> = Vec::with_capacity(512);
    let mut next: Vec<usize> = Vec::with_capacity(512);

    let mut saved: u32 = LZW_INVALID;
    let mut i: usize = 0;
    if !src.is_empty() {
        emit_lsb(&mut out, LZW_CLEAR, width, &mut bits, &mut nbits);
        saved = src[0] as u32;
        i = 1;
    }

    while i < src.len() {
        let lit = src[i] as u32;
        let key = (saved << 8) | lit;
        let h = ((key * 31) & 4095) as usize;
        let mut found: Option<usize> = None;
        let mut cur = head[h];
        while cur > 0 {
            let idx = cur - 1;
            if keys[idx] == key {
                found = Some(idx);
                break;
            }
            cur = next[idx];
        }
        if let Some(idx) = found {
            saved = vals[idx] as u32;
            i += 1;
            continue;
        }
        emit_lsb(&mut out, saved, width, &mut bits, &mut nbits);
        saved = lit;
        hi += 1;
        let mut out_of = false;
        if hi == overflow {
            width += 1;
            overflow <<= 1;
        }
        if hi == LZW_MAX_CODE {
            emit_lsb(&mut out, LZW_CLEAR, width, &mut bits, &mut nbits);
            width = 9;
            hi = LZW_EOF;
            overflow = LZW_CLEAR * 2;
            keys.clear();
            vals.clear();
            next.clear();
            head.fill(0);
            out_of = true;
        }
        if !out_of {
            keys.push(key);
            vals.push(hi as u16);
            next.push(head[h]);
            head[h] = keys.len();
        }
        i += 1;
    }

    if saved != LZW_INVALID {
        emit_lsb(&mut out, saved, width, &mut bits, &mut nbits);
        hi += 1;
        if hi == overflow {
            width += 1;
            overflow <<= 1;
        }
        if hi == LZW_MAX_CODE {
            emit_lsb(&mut out, LZW_CLEAR, width, &mut bits, &mut nbits);
            width = 9;
        }
    } else {
        emit_lsb(&mut out, LZW_CLEAR, width, &mut bits, &mut nbits);
    }

    emit_lsb(&mut out, LZW_EOF, width, &mut bits, &mut nbits);
    if nbits > 0 {
        out.push((bits & 0xff) as u8);
    }
    out
}

fn lzw_decode(src: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(src.len() * 4 + 64);
    let mut width: u32 = 9;
    let mut hi: u32 = LZW_EOF;
    let mut overflow: u32 = 1u32 << width;
    let mut last: u32 = LZW_INVALID;
    let mut bits: u32 = 0;
    let mut nbits: u32 = 0;
    let mut pos: usize = 0;

    let mut prefix = [0u16; 4096];
    let mut suffix = [0u8; 4096];
    let mut stack = Vec::with_capacity(64);

    loop {
        while nbits < width {
            bits |= (src[pos] as u32) << nbits;
            pos += 1;
            nbits += 8;
        }
        let code = bits & ((1u32 << width) - 1);
        bits >>= width;
        nbits -= width;

        if code < LZW_CLEAR {
            out.push(code as u8);
            if last != LZW_INVALID {
                let hu = hi as usize;
                suffix[hu] = code as u8;
                prefix[hu] = last as u16;
            }
        } else {
            if code == LZW_CLEAR {
                width = 9;
                hi = LZW_EOF;
                overflow = 1u32 << width;
                last = LZW_INVALID;
                continue;
            }
            if code == LZW_EOF {
                break;
            }
            if code > hi {
                panic!("lzw: invalid code");
            }
            stack.clear();
            let mut c = code;
            if code == hi && last != LZW_INVALID {
                c = last;
                while c >= LZW_CLEAR {
                    c = prefix[c as usize] as u32;
                }
                stack.push(c as u8);
                c = last;
            }
            while c >= LZW_CLEAR {
                let cu = c as usize;
                stack.push(suffix[cu]);
                c = prefix[cu] as u32;
            }
            stack.push(c as u8);

            let first_byte = *stack.last().unwrap();
            for &b in stack.iter().rev() {
                out.push(b);
            }
            if last != LZW_INVALID {
                let hu = hi as usize;
                suffix[hu] = first_byte;
                prefix[hu] = last as u16;
            }
        }

        last = code;
        hi += 1;
        if hi >= overflow {
            if width == LZW_MAX_WIDTH {
                last = LZW_INVALID;
                hi -= 1;
            } else {
                width += 1;
                overflow <<= 1;
            }
        }
    }
    out
}

fn main() {
    let base = b"TOBEORNOTTOBEORTOBEORNOT#";
    let mut payload = Vec::with_capacity(base.len() * 16);
    for _ in 0..16 {
        payload.extend_from_slice(base);
    }

    let mut total: i64 = 0;
    for i in 0..2500 {
        let enc = lzw_encode(&payload);
        let dec = lzw_decode(&enc);
        total += (enc.len() + dec.len()) as i64;
        if i == 0 {
            total += dec[0] as i64 + dec[dec.len() - 1] as i64;
        }
    }
    println!("{}", total);
}
