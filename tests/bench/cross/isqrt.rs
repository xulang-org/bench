// Osprey (MIT): benchmarks/cases/isqrt; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Integer Newton iteration, sum floor(sqrt(i)) over 1..1000000.

fn root(n: i64) -> i64 {
    if n < 2 { return n; }
    let mut x: i64 = n;
    let mut y: i64 = (x + n / x) / 2;
    while y < x {
        x = y;
        y = (x + n / x) / 2;
    }
    return x;
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 1;
    while i <= 1000000 {
        result += root(i);
        i += 1;
    }
    println!("{}", result);
}
