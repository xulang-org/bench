// Osprey (MIT): benchmarks/cases/exprtree; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
enum Expr {
    Lit(i64),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
}

fn hash_at(seed: i64, idx: i64) -> i64 {
    (((seed + idx) * 16807) % 2147483647 * 16807) % 2147483647
}

fn build(seed: i64, idx: i64, depth: i64) -> Expr {
    if depth == 0 { return Expr::Lit(hash_at(seed, idx) % 1000); }
    let left = Box::new(build(seed, idx * 2 + 1, depth - 1));
    let right = Box::new(build(seed, idx * 2 + 2, depth - 1));
    if hash_at(seed, idx) % 2 == 0 { Expr::Add(left, right) } else { Expr::Mul(left, right) }
}

fn eval(e: &Expr) -> i64 {
    match e {
        Expr::Lit(value) => *value,
        Expr::Add(left, right) => (eval(left) + eval(right)) % 1000000007,
        Expr::Mul(left, right) => (eval(left) * eval(right)) % 1000000007,
    }
}

fn main() {
    let mut total: i64 = 0;
    let mut t: i64 = 0;
    while t < 10 {
        let expr = build(1 + t * 7, 1, 14);
        total = (total + eval(&expr)) % 1000000007;
        t += 1;
    }
    println!("{}", total);
}
