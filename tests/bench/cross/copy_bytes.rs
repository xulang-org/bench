fn main() {
    let n: usize = 1_048_576;
    let mut src = vec![0i64; n];
    let mut dst = vec![0i64; n];
    let mut i: usize = 0;
    while i < n {
        let v = (i as i64) & 1023;
        src[i] = v;
        dst[i] = v;
        i += 1;
    }
    let mut t: i64 = 0;
    while t < 80 {
        i = 0;
        while i < n {
            dst[i] = src[i];
            i += 1;
        }
        t += 1;
    }
    let mut s: i64 = 0;
    i = 0;
    while i < n {
        s += dst[i];
        i += 1;
    }
    println!("{}", s);
}
