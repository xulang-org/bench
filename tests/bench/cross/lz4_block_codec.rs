const MOD_V: i64 = 1000000007;

fn lz4_compress(blocks: &[i64], src_off: usize, n: usize, ht: &mut [i64], comp: &mut [i64]) -> usize {
    for h_slot in ht.iter_mut() {
        *h_slot = -1;
    }
    let mut op = 0usize;
    let mut ip = 0usize;
    let mut anchor = 0usize;
    let limit = n - 12;
    let mflimit = n - 5;
    while ip < limit {
        let p = src_off + ip;
        let seq = blocks[p] | (blocks[p + 1] << 8) | (blocks[p + 2] << 16) | (blocks[p + 3] << 24);
        let h = (((seq * 73244475) >> 18) & 4095) as usize;
        let ref_pos = ht[h];
        ht[h] = ip as i64;
        if ref_pos >= 0 && (ip as i64 - ref_pos) <= 65535 {
            let ref_u = ref_pos as usize;
            let rp = src_off + ref_u;
            if blocks[rp] == blocks[p]
                && blocks[rp + 1] == blocks[p + 1]
                && blocks[rp + 2] == blocks[p + 2]
                && blocks[rp + 3] == blocks[p + 3]
            {
                let mut mlen = 4usize;
                while ip + mlen < mflimit && blocks[rp + mlen] == blocks[p + mlen] {
                    mlen += 1;
                }
                let lit_len = ip - anchor;
                let m_extra = mlen - 4;
                let tok_lit = if lit_len >= 15 { 15 } else { lit_len };
                let tok_m = if m_extra >= 15 { 15 } else { m_extra };
                comp[op] = ((tok_lit << 4) | tok_m) as i64;
                op += 1;
                if lit_len >= 15 {
                    let mut rem = lit_len - 15;
                    while rem >= 255 {
                        comp[op] = 255;
                        op += 1;
                        rem -= 255;
                    }
                    comp[op] = rem as i64;
                    op += 1;
                }
                for j in 0..lit_len {
                    comp[op] = blocks[src_off + anchor + j];
                    op += 1;
                }
                let off = ip - ref_u;
                comp[op] = (off & 255) as i64;
                comp[op + 1] = ((off >> 8) & 255) as i64;
                op += 2;
                if m_extra >= 15 {
                    let mut rem = m_extra - 15;
                    while rem >= 255 {
                        comp[op] = 255;
                        op += 1;
                        rem -= 255;
                    }
                    comp[op] = rem as i64;
                    op += 1;
                }
                ip += mlen;
                anchor = ip;
                continue;
            }
        }
        ip += 1;
    }
    let lit_len = n - anchor;
    let tok_lit = if lit_len >= 15 { 15 } else { lit_len };
    comp[op] = (tok_lit << 4) as i64;
    op += 1;
    if lit_len >= 15 {
        let mut rem = lit_len - 15;
        while rem >= 255 {
            comp[op] = 255;
            op += 1;
            rem -= 255;
        }
        comp[op] = rem as i64;
        op += 1;
    }
    for j in 0..lit_len {
        comp[op] = blocks[src_off + anchor + j];
        op += 1;
    }
    op
}

fn lz4_decompress(comp: &[i64], clen: usize, decomp: &mut [i64]) {
    let mut ip = 0usize;
    let mut op = 0usize;
    while ip < clen {
        let tok = comp[ip] as usize;
        ip += 1;
        let mut lit_len = tok >> 4;
        if lit_len == 15 {
            loop {
                let b = comp[ip] as usize;
                ip += 1;
                lit_len += b;
                if b != 255 {
                    break;
                }
            }
        }
        for _ in 0..lit_len {
            decomp[op] = comp[ip];
            op += 1;
            ip += 1;
        }
        if ip >= clen {
            break;
        }
        let off = (comp[ip] | (comp[ip + 1] << 8)) as usize;
        ip += 2;
        let mut mlen = (tok & 15) + 4;
        if (tok & 15) == 15 {
            loop {
                let b = comp[ip] as usize;
                ip += 1;
                mlen += b;
                if b != 255 {
                    break;
                }
            }
        }
        let mp = op - off;
        for j in 0..mlen {
            decomp[op] = decomp[mp + j];
            op += 1;
        }
    }
}

fn main() {
    const BLK_LEN: usize = 32768;
    let mut rng: i64 = 135724680;
    let phrases: [&[u8]; 6] = [
        b"{\"level\":\"INFO\",\"service\":\"storage-node\",\"msg\":\"compaction_ok\",\"ms\":",
        b"{\"level\":\"WARN\",\"service\":\"rpc-gateway\",\"msg\":\"retry_backoff\",\"ms\":",
        b"SELECT region, category, SUM(amount) FROM orders WHERE status = 1; ",
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        b"GET /api/v1/users/profile HTTP/1.1\r\nHost: api.xulang.org\r\n\r\n",
        b"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    ];

    let mut blocks: Vec<i64> = Vec::with_capacity(24 * BLK_LEN);
    for _bi in 0..24 {
        let mut src: Vec<i64> = Vec::with_capacity(BLK_LEN + 128);
        while src.len() < BLK_LEN {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let k = (rng % 10) as usize;
            if k < 6 {
                for &b in phrases[k] {
                    src.push(b as i64);
                }
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let v = rng % 1000;
                src.push(48 + (v / 100));
                src.push(48 + ((v / 10) % 10));
                src.push(48 + (v % 10));
                src.push(10);
            } else if k < 8 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let ch = 65 + (rng % 26);
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let rl = 12 + (rng % 48);
                for _ in 0..rl {
                    src.push(ch);
                }
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let rl = 8 + (rng % 24);
                for _ in 0..rl {
                    rng = (rng * 1103515245 + 12345) & 2147483647;
                    src.push(32 + (rng % 95));
                }
            }
        }
        blocks.extend_from_slice(&src[..BLK_LEN]);
    }

    let mut ht = vec![-1i64; 4096];
    let mut comp = vec![0i64; BLK_LEN + 4096];
    let mut decomp = vec![0i64; BLK_LEN];

    let mut total_comp: i64 = 0;
    let mut ck: i64 = 0;
    for _rnd in 0..4 {
        for bi in 0..24 {
            let clen = lz4_compress(&blocks, bi * BLK_LEN, BLK_LEN, &mut ht, &mut comp);
            lz4_decompress(&comp, clen, &mut decomp);
            let mut h = clen as i64;
            for i in 0..BLK_LEN {
                h = (h * 131 + decomp[i]) % MOD_V;
            }
            total_comp += clen as i64;
            ck = (ck * 31 + h) % MOD_V;
        }
    }

    println!("{}\n{}", total_comp, ck);
}
