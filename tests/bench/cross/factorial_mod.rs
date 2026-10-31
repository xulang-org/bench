// Osprey (MIT): benchmarks/cases/factorial; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Product 1..10000000 modulo 1000000007; dependent multiply/remainder fold.

fn main() {
    let mut result: i64 = 1;
    let mut i: i64 = 1;
    while i <= 10000000 {
        result = (result * i) % 1000000007;
        i += 1;
    }
    println!("{}", result);
}
