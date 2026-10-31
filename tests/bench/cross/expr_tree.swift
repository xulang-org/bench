// Osprey (MIT): benchmarks/cases/exprtree; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
final class Expr {
    let tag, value: Int64
    let left, right: Expr?
    init(_ tag: Int64, _ value: Int64, _ left: Expr?, _ right: Expr?) {
        self.tag = tag
        self.value = value
        self.left = left
        self.right = right
    }
}

func hashAt(_ seed: Int64, _ idx: Int64) -> Int64 {
    return (((seed + idx) * 16807) % 2147483647 * 16807) % 2147483647
}

func build(_ seed: Int64, _ idx: Int64, _ depth: Int64) -> Expr {
    if depth == 0 { return Expr(0, hashAt(seed, idx) % 1000, nil, nil) }
    let left = build(seed, idx * 2 + 1, depth - 1)
    let right = build(seed, idx * 2 + 2, depth - 1)
    return Expr(1 + hashAt(seed, idx) % 2, 0, left, right)
}

func eval(_ e: Expr) -> Int64 {
    if e.tag == 0 { return e.value }
    let left = eval(e.left!)
    let right = eval(e.right!)
    if e.tag == 1 { return (left + right) % 1000000007 }
    return (left * right) % 1000000007
}

func main() {
    var total: Int64 = 0
    var t: Int64 = 0
    while t < 10 {
        let expr = build(1 + t * 7, 1, 14)
        total = (total + eval(expr)) % 1000000007
        t += 1
    }
    print(total)
}

main()
