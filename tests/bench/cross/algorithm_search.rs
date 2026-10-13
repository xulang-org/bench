fn lower_bound(a: &[i64], v: i64) -> usize {
    let mut lo = 0;
    let mut hi = a.len();
    while lo < hi {
        let mid = lo + ((hi - lo) >> 1);
        if a[mid] < v {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    lo
}

fn main() {
    let n = 131072;
    let mut a = Vec::with_capacity(n);
    let mut i: i64 = 0;
    while i < n as i64 {
        a.push(i * 3);
        i += 1;
    }
    let mut total: i64 = 0;
    let mut q: i64 = 0;
    while q < 4000000 {
        let v = ((q.wrapping_mul(1103515245) + 12345) & 0x3FFFF) * 3;
        total += lower_bound(&a, v) as i64;
        q += 1;
    }
    println!("{}", total);
}
