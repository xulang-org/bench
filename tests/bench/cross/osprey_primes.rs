// Osprey (MIT): benchmarks/cases/primes; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey primes: trial division, every candidate divisor from 2 through sqrt(n).

fn has_factor(n: i64, d: i64) -> i64 {
    if d * d > n { return 0; }
    if n % d == 0 { return 1; }
    return has_factor(n, d + 1);
}
fn is_prime(n: i64) -> i64 {
    if n < 2 { return 0; }
    return 1 - has_factor(n, 2);
}

fn main() {
    let mut result: i64 = 0;
    let mut n: i64 = 2;
    while n < 200000 {
        if is_prime(n) != 0 { result += 1; }
        n += 1;
    }
    println!("{}", result);
}
