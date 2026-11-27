const MOD_V: i64 = 1000000007;

fn main() {
    const N_CUST: usize = 8192;
    const HT_CAP: usize = 16384;
    const HT_MASK: i64 = 16383;
    const N_ORD: usize = 200000;
    let mut rng: i64 = 42424242;

    let mut cust_id = vec![0i64; N_CUST];
    let mut cust_reg = vec![0i64; N_CUST];
    let mut cust_tier = vec![0i64; N_CUST];
    let mut ht_key = vec![-1i64; HT_CAP];
    let mut ht_val = vec![-1i64; HT_CAP];

    for i in 0..N_CUST {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let cid = 100000 + (i as i64) * 7 + (rng % 5);
        cust_id[i] = cid;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cust_reg[i] = rng % 16;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cust_tier[i] = rng % 4;
        let mut slot = (((cid * 2654435761) >> 16) & HT_MASK) as usize;
        while ht_key[slot] != -1 {
            slot = (slot + 1) & (HT_MASK as usize);
        }
        ht_key[slot] = cid;
        ht_val[slot] = i as i64;
    }

    let mut ord_cid = vec![0i64; N_ORD];
    let mut ord_cat = vec![0i64; N_ORD];
    let mut ord_amt = vec![0i64; N_ORD];
    let mut ord_status = vec![0i64; N_ORD];

    for i in 0..N_ORD {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        if (rng % 20) < 17 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            ord_cid[i] = cust_id[(rng % N_CUST as i64) as usize];
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            ord_cid[i] = 9000000 + (rng % 50000);
        }
        rng = (rng * 1103515245 + 12345) & 2147483647;
        ord_cat[i] = rng % 32;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        ord_amt[i] = 100 + (rng % 2000);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        ord_status[i] = if (rng % 5) != 0 { 1 } else { 0 };
    }

    let mut grp_cnt = [0i64; 512];
    let mut grp_rev = [0i64; 512];
    let mut active = [0usize; 512];
    let mut total_rows: i64 = 0;
    let mut ck: i64 = 0;

    for rnd in 0i64..16 {
        let min_amt = 350 + rnd * 50;
        for b in 0..512 {
            grp_cnt[b] = 0;
            grp_rev[b] = 0;
        }
        for i in 0..N_ORD {
            if ord_status[i] != 1 {
                continue;
            }
            let amt = ord_amt[i];
            if amt < min_amt {
                continue;
            }
            let cid = ord_cid[i];
            let mut slot = (((cid * 2654435761) >> 16) & HT_MASK) as usize;
            let mut found: i64 = -1;
            while ht_key[slot] != -1 {
                if ht_key[slot] == cid {
                    found = ht_val[slot];
                    break;
                }
                slot = (slot + 1) & (HT_MASK as usize);
            }
            if found == -1 {
                continue;
            }
            let fi = found as usize;
            let tier = cust_tier[fi];
            if tier == 0 {
                continue;
            }
            let gb = (cust_reg[fi] * 32 + ord_cat[i]) as usize;
            grp_cnt[gb] += 1;
            grp_rev[gb] += amt * tier;
            total_rows += 1;
        }

        let mut acnt = 0usize;
        for b in 0..512 {
            if grp_cnt[b] > 0 {
                active[acnt] = b;
                acnt += 1;
            }
        }
        for i in 1..acnt {
            let kb = active[i];
            let kr = grp_rev[kb];
            let mut j = i;
            while j > 0 {
                let jb = active[j - 1];
                let jr = grp_rev[jb];
                if jr < kr || (jr == kr && jb > kb) {
                    active[j] = jb;
                    j -= 1;
                } else {
                    break;
                }
            }
            active[j] = kb;
        }
        for i in 0..acnt {
            let gb = active[i];
            let row = ((gb as i64) * 1000003 + grp_cnt[gb] * 97 + (grp_rev[gb] % MOD_V)) % MOD_V;
            ck = (ck * 31 + row) % MOD_V;
        }
    }

    println!("{}\n{}", total_rows, ck);
}
