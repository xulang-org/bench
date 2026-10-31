// Osprey (MIT): benchmarks/cases/mutual; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Mutually recursive parity, i%1000 for 1 <= i < 130000.

func even(_ n: Int64) -> Int64 {
    if n == 0 { return 1 }
    return odd(n - 1)
}
func odd(_ n: Int64) -> Int64 {
    if n == 0 { return 0 }
    return even(n - 1)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i < 130000 {
        result += even(i % 1000)
        i += 1
    }
    print(result)
}

main()
