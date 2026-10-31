// Osprey (MIT): benchmarks/cases/fib; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey fib: naive fib(35), including the original two base cases.

fn add(a: i64, b: i64) -> i64 { return a + b; }
fn sub(a: i64, b: i64) -> i64 { return a - b; }
fn fib(n: i64) -> i64 {
    if n == 0 { return 0; }
    if n == 1 { return 1; }
    return add(fib(sub(n, 1)), fib(sub(n, 2)));
}

fn main() {
    let result: i64 = fib(35);
    println!("{}", result);
}
