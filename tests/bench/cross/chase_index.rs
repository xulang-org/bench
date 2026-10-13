fn main() {
    let n: usize = 65536;
    let mut nxt = vec![0i64; n];
    let mut i: usize = 0;
    while i < n {
        nxt[i] = (((i as i64) * 7) + 1) & ((n as i64) - 1);
        i += 1;
    }
    let mut k: i64 = 0;
    let mut s: i64 = 0;
    while s < 20_000_000 {
        k = nxt[k as usize];
        s += 1;
    }
    println!("{}", k);
}
