// Osprey (MIT): benchmarks/cases/josephus; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Josephus survivor, zero-based, n=10000000 and k=7; variable divisor chain.

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 2;
    while i <= 10000000 {
        result = (result + 7) % i;
        i += 1;
    }
    println!("{}", result);
}
