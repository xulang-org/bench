fn main() {
    let n: i64 = 250;
    let nn = (n * n) as usize;
    let mut a = vec![0i64; nn];
    let mut b = vec![0i64; nn];
    let mut c = vec![0i64; nn];
    let mut i: i64 = 0;
    while i < n {
        let mut j: i64 = 0;
        while j < n {
            a[(i * n + j) as usize] = (i * 31 + j * 7) & 1023;
            b[(i * n + j) as usize] = (i * 17 + j * 13) & 1023;
            j += 1;
        }
        i += 1;
    }
    i = 0;
    while i < n {
        let mut k: i64 = 0;
        while k < n {
            let aik = a[(i * n + k) as usize];
            let mut j: i64 = 0;
            while j < n {
                let idx = (i * n + j) as usize;
                c[idx] = c[idx] + aik * b[(k * n + j) as usize];
                j += 1;
            }
            k += 1;
        }
        i += 1;
    }
    let mut s: i64 = 0;
    let mut t: usize = 0;
    while t < nn {
        s += c[t];
        t += 1;
    }
    println!("{}", s);
}
