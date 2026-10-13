fn main() {
    let n: usize = 4096;
    let mut a = vec![0i64; n];
    let mut i: usize = 0;
    while i < n {
        a[i] = (i as i64) & 1023;
        i += 1;
    }
    let mut t: i64 = 0;
    while t < 20_000 {
        i = 1;
        while i < n {
            a[i] = a[i] + (a[i - 1] & 1023);
            i += 1;
        }
        t += 1;
    }
    println!("{}", a[n - 1]);
}
