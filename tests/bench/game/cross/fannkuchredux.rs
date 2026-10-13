fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(12);
    let mut perm1: Vec<i32> = (0..n as i32).collect();
    let mut count = vec![0i32; n];
    let mut perm = vec![0i32; n];
    let (mut max_flips, mut checksum, mut sign, mut r) = (0i32, 0i32, 1i32, n);
    loop {
        while r != 1 { count[r-1] = r as i32; r -= 1; }
        perm.copy_from_slice(&perm1);
        let mut flips = 0i32;
        let mut k = perm[0];
        while k != 0 {
            let mut i = 0usize; let mut j = k as usize;
            while i < j { perm.swap(i, j); i += 1; j -= 1; }
            flips += 1; k = perm[0];
        }
        if flips > max_flips { max_flips = flips; }
        checksum += sign * flips; sign = -sign;
        loop {
            if r == n { println!("{checksum}\nPfannkuchen({n}) = {max_flips}"); return; }
            let p0 = perm1[0];
            for i in 0..r { perm1[i] = perm1[i+1]; }
            perm1[r] = p0;
            count[r] -= 1;
            if count[r] > 0 { break; }
            r += 1;
        }
    }
}
