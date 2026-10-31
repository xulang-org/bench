// Osprey (MIT): benchmarks/cases/powmod; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty multiplies, no squaring.

fn power(base: i64, e: i64, acc: i64) -> i64 {
    if e == 0 { return acc; }
    return power(base, e - 1, (acc * base) % 1000000007);
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 1;
    while i < 1000000 {
        result = (result + power(i, 20, 1)) % 1000000007;
        i += 1;
    }
    println!("{}", result);
}
