// Osprey (MIT): benchmarks/cases/coprime; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey coprime: 2000x2000 grid, recursive Euclidean GCD.

fn gcd(a: i64, b: i64) -> i64 {
    if b == 0 { return a; }
    return gcd(b, a % b);
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 2000;
    while i > 0 {
        let mut j: i64 = 2000;
        while j > 0 {
            if gcd(i, j) == 1 { result += 1; }
            j -= 1;
        }
        i -= 1;
    }
    println!("{}", result);
}
