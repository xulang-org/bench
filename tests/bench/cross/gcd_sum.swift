// Osprey (MIT): benchmarks/cases/gcdsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive Euclidean GCD: sum gcd(i,1234567), 1 <= i < 2000000.

func gcd(_ a: Int64, _ b: Int64) -> Int64 {
    if b == 0 { return a }
    return gcd(b, a % b)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i < 2000000 {
        result += gcd(i, 1234567)
        i += 1
    }
    print(result)
}

main()
