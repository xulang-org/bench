// Osprey (MIT): benchmarks/cases/coprime; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey coprime: 2000x2000 grid, recursive Euclidean GCD.

func gcd(_ a: Int64, _ b: Int64) -> Int64 {
    if b == 0 { return a }
    return gcd(b, a % b)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 2000
    while i > 0 {
        var j: Int64 = 2000
        while j > 0 {
            if gcd(i, j) == 1 { result += 1 }
            j -= 1
        }
        i -= 1
    }
    print(result)
}

main()
