fn nq_solve(n: usize) -> i64 {
    let mut l = [0i64; 32];
    let mut c = [0i64; 32];
    let mut r = [0i64; 32];
    let mut m = [0i64; 32];
    let y0 = (1i64 << n) - 1;
    let mut k: isize = 0;
    m[0] = y0;
    let mut cnt: i64 = 0;
    while k >= 0 {
        let ku = k as usize;
        let y = m[ku];
        if y == 0 {
            k -= 1;
        } else {
            let z = y & y.wrapping_neg();
            m[ku] = y - z;
            if ku == n - 1 {
                cnt += 1;
            } else {
                let nk = ku + 1;
                l[nk] = ((l[ku] | z) << 1) & y0;
                c[nk] = c[ku] | z;
                r[nk] = (r[ku] | z) >> 1;
                m[nk] = y0 ^ (l[nk] | c[nk] | r[nk]);
                k += 1;
            }
        }
    }
    cnt
}

fn main() {
    println!("{}", nq_solve(15));
}
