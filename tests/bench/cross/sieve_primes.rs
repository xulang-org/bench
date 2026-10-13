fn main() {
    let n: i64 = 2_000_000;
    let mut is_prime: Vec<i64> = Vec::with_capacity((n + 1) as usize);
    let mut i: i64 = 0;
    while i <= n {
        is_prime.push(1);
        i += 1;
    }
    is_prime[0] = 0;
    is_prime[1] = 0;
    let mut p: i64 = 2;
    while p * p <= n {
        if is_prime[p as usize] == 1 {
            let mut j = p * p;
            while j <= n {
                is_prime[j as usize] = 0;
                j += p;
            }
        }
        p += 1;
    }
    let mut count: i64 = 0;
    let mut total: i64 = 0;
    let mut k: i64 = 2;
    while k <= n {
        if is_prime[k as usize] == 1 {
            count += 1;
            total += k;
        }
        k += 1;
    }
    println!("{}", count);
    println!("{}", total);
}
