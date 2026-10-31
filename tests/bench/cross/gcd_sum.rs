// Osprey (MIT): benchmarks/cases/gcdsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive Euclidean GCD: sum gcd(i,1234567), 1 <= i < 2000000.

fn gcd(a: i64, b: i64) -> i64 {
    if b == 0 { return a; }
    return gcd(b, a % b);
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 1;
    while i < 2000000 {
        result += gcd(i, 1234567);
        i += 1;
    }
    println!("{}", result);
}
