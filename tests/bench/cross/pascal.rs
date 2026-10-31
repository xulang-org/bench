// Osprey (MIT): benchmarks/cases/pascal; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised Pascal recursion: binomial coefficient C(27,13).

fn binom(n: i64, k: i64) -> i64 {
    if k == 0 { return 1; }
    if k == n { return 1; }
    return binom(n - 1, k - 1) + binom(n - 1, k);
}

fn main() {
    let result: i64 = binom(27, 13);
    println!("{}", result);
}
