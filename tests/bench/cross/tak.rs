// Osprey (MIT): benchmarks/cases/tak; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Takeuchi tak(32,16,8): ternary recursion with recursive arguments.

fn sub(a: i64, b: i64) -> i64 { return a - b; }
fn tak(x: i64, y: i64, z: i64) -> i64 {
    if x > y {
        return tak(tak(sub(x, 1), y, z), tak(sub(y, 1), z, x), tak(sub(z, 1), x, y));
    }
    return z;
}

fn main() {
    let result: i64 = tak(32, 16, 8);
    println!("{}", result);
}
