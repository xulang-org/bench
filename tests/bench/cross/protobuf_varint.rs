const MOD_V: i64 = 1000000007;

fn put_uvarint(buf: &mut Vec<i64>, val: i64) {
    let mut v = val;
    while v >= 128 {
        buf.push((v & 127) | 128);
        v >>= 7;
    }
    buf.push(v & 127);
}

fn zigzag_enc(v: i64) -> i64 {
    if v >= 0 { v << 1 } else { ((-v) << 1) - 1 }
}

fn zigzag_dec(u: i64) -> i64 {
    if (u & 1) == 0 { u >> 1 } else { -((u >> 1) + 1) }
}

fn push_str_bytes(buf: &mut Vec<i64>, s: &str) {
    for b in s.bytes() {
        buf.push(b as i64);
    }
}

fn main() {
    let symbols = ["BTC-USD", "ETH-EUR", "SOL-JPY", "XU-USD", "NVDA", "AAPL", "GOOG", "MSFT"];
    let tags = ["fast", "batch", "edge", "core", "prod", "canary", "blue", "green"];

    let mut buf: Vec<i64> = Vec::with_capacity(32768);
    let mut meta: Vec<i64> = Vec::with_capacity(64);
    let mut packed: Vec<i64> = Vec::with_capacity(32);
    let mut msg: Vec<i64> = Vec::with_capacity(128);
    let mut qs = [0i64; 8];

    let mut rng: i64 = 314159265;
    let mut total_wire: i64 = 0;
    let mut ck: i64 = 0;
    for batch in 0i64..400 {
        buf.clear();
        for i in 0i64..500 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let order_id = (batch * 500 + i + 1) * 131 + (rng & 1023);
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let price_delta = (rng % 200001) - 100000;
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let sym = symbols[(rng & 7) as usize];
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let qcnt = (4 + (rng & 3)) as usize;
            for qi in 0..qcnt {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                qs[qi] = 1 + (rng % 5000);
            }
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let reg_id = 1 + (rng & 31);
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let lat_us = (rng % 10001) - 5000;
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let tag = tags[(rng & 7) as usize];

            meta.clear();
            put_uvarint(&mut meta, (1 << 3) | 0);
            put_uvarint(&mut meta, reg_id);
            put_uvarint(&mut meta, (2 << 3) | 0);
            put_uvarint(&mut meta, zigzag_enc(lat_us));
            put_uvarint(&mut meta, (3 << 3) | 2);
            put_uvarint(&mut meta, tag.len() as i64);
            push_str_bytes(&mut meta, tag);

            packed.clear();
            for qi in 0..qcnt {
                put_uvarint(&mut packed, qs[qi]);
            }

            msg.clear();
            put_uvarint(&mut msg, (1 << 3) | 0);
            put_uvarint(&mut msg, order_id);
            put_uvarint(&mut msg, (2 << 3) | 0);
            put_uvarint(&mut msg, zigzag_enc(price_delta));
            put_uvarint(&mut msg, (3 << 3) | 2);
            put_uvarint(&mut msg, sym.len() as i64);
            push_str_bytes(&mut msg, sym);
            put_uvarint(&mut msg, (4 << 3) | 2);
            put_uvarint(&mut msg, packed.len() as i64);
            msg.extend_from_slice(&packed);
            put_uvarint(&mut msg, (5 << 3) | 2);
            put_uvarint(&mut msg, meta.len() as i64);
            msg.extend_from_slice(&meta);

            put_uvarint(&mut buf, msg.len() as i64);
            buf.extend_from_slice(&msg);
        }

        total_wire += buf.len() as i64;
        let mut pos = 0usize;
        let blen = buf.len();
        while pos < blen {
            let mut mlen: i64 = 0;
            let mut sh = 0u32;
            loop {
                let b = buf[pos];
                pos += 1;
                mlen |= (b & 127) << sh;
                if (b & 128) == 0 {
                    break;
                }
                sh += 7;
            }
            let end = pos + mlen as usize;
            let (mut oid, mut pdelta, mut sym_sum, mut q_sum, mut reg, mut lat, mut tlen) = (0i64, 0i64, 0i64, 0i64, 0i64, 0i64, 0i64);
            while pos < end {
                let mut tag_w: i64 = 0;
                sh = 0;
                loop {
                    let b = buf[pos];
                    pos += 1;
                    tag_w |= (b & 127) << sh;
                    if (b & 128) == 0 {
                        break;
                    }
                    sh += 7;
                }
                let fnum = tag_w >> 3;
                let wtype = tag_w & 7;
                if wtype == 0 {
                    let mut val: i64 = 0;
                    sh = 0;
                    loop {
                        let b = buf[pos];
                        pos += 1;
                        val |= (b & 127) << sh;
                        if (b & 128) == 0 {
                            break;
                        }
                        sh += 7;
                    }
                    if fnum == 1 {
                        oid = val;
                    } else if fnum == 2 {
                        pdelta = zigzag_dec(val);
                    }
                } else if wtype == 2 {
                    let mut ln: i64 = 0;
                    sh = 0;
                    loop {
                        let b = buf[pos];
                        pos += 1;
                        ln |= (b & 127) << sh;
                        if (b & 128) == 0 {
                            break;
                        }
                        sh += 7;
                    }
                    let sub_end = pos + ln as usize;
                    if fnum == 3 {
                        while pos < sub_end {
                            sym_sum += buf[pos];
                            pos += 1;
                        }
                    } else if fnum == 4 {
                        while pos < sub_end {
                            let mut qv: i64 = 0;
                            sh = 0;
                            loop {
                                let b = buf[pos];
                                pos += 1;
                                qv |= (b & 127) << sh;
                                if (b & 128) == 0 {
                                    break;
                                }
                                sh += 7;
                            }
                            q_sum += qv;
                        }
                    } else if fnum == 5 {
                        while pos < sub_end {
                            let mut mtag: i64 = 0;
                            sh = 0;
                            loop {
                                let b = buf[pos];
                                pos += 1;
                                mtag |= (b & 127) << sh;
                                if (b & 128) == 0 {
                                    break;
                                }
                                sh += 7;
                            }
                            let mf = mtag >> 3;
                            let mw = mtag & 7;
                            if mw == 0 {
                                let mut mv: i64 = 0;
                                sh = 0;
                                loop {
                                    let b = buf[pos];
                                    pos += 1;
                                    mv |= (b & 127) << sh;
                                    if (b & 128) == 0 {
                                        break;
                                    }
                                    sh += 7;
                                }
                                if mf == 1 {
                                    reg = mv;
                                } else if mf == 2 {
                                    lat = zigzag_dec(mv);
                                }
                            } else if mw == 2 {
                                let mut sln: i64 = 0;
                                sh = 0;
                                loop {
                                    let b = buf[pos];
                                    pos += 1;
                                    sln |= (b & 127) << sh;
                                    if (b & 128) == 0 {
                                        break;
                                    }
                                    sh += 7;
                                }
                                if mf == 3 {
                                    tlen = sln;
                                }
                                pos += sln as usize;
                            }
                        }
                    } else {
                        pos = sub_end;
                    }
                }
            }
            let mut row = (oid + pdelta + sym_sum + q_sum + reg * 13 + lat + tlen * 7) % MOD_V;
            if row < 0 {
                row += MOD_V;
            }
            ck = (ck * 31 + row) % MOD_V;
        }
    }
    println!("{total_wire}");
    println!("{ck}");
}
