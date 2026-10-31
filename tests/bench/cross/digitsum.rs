// Osprey (MIT): benchmarks/cases/digitsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive decimal digit sums, summed over 1..2000000.

fn digit_sum(n: i64) -> i64 {
    if n < 10 { return n; }
    return n % 10 + digit_sum(n / 10);
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 1;
    while i <= 2000000 {
        result += digit_sum(i);
        i += 1;
    }
    println!("{}", result);
}
