// Osprey (MIT): benchmarks/cases/listops; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.

fn hash_at(seed: i64, i: i64) -> i64 {
    (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

fn sum_list(xs: &[i64], i: i64) -> i64 {
    if i == xs.len() as i64 { return 0; }
    xs[i as usize] + sum_list(xs, i + 1)
}

fn below_list(xs: &[i64], i: i64) -> i64 {
    if i == xs.len() as i64 { return 0; }
    let mut add: i64 = if xs[i as usize] < 500 { 1 } else { 0 };
    add += below_list(xs, i + 1);
    add
}

fn main() {
    let mut total: i64 = 0;
    let mut t: i64 = 0;
    while t < 8 {
        let mut xs = Vec::new();
        let mut i: i64 = 0;
        while i < 4000 {
            xs.push(hash_at(1 + t * 131, i) % 1000);
            i += 1;
        }
        total = (total + sum_list(&xs, 0) + below_list(&xs, 0)) % 1000000007;
        t += 1;
    }
    println!("{}", total);
}
