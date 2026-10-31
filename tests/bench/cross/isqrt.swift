// Osprey (MIT): benchmarks/cases/isqrt; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Integer Newton iteration, sum floor(sqrt(i)) over 1..1000000.

func root(_ n: Int64) -> Int64 {
    if n < 2 { return n }
    var x: Int64 = n
    var y: Int64 = (x + n / x) / 2
    while y < x {
        x = y
        y = (x + n / x) / 2
    }
    return x
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i <= 1000000 {
        result += root(i)
        i += 1
    }
    print(result)
}

main()
