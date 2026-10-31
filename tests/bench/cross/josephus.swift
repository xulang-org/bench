// Osprey (MIT): benchmarks/cases/josephus; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Josephus survivor, zero-based, n=10000000 and k=7; variable divisor chain.

func main() {
    var result: Int64 = 0
    var i: Int64 = 2
    while i <= 10000000 {
        result = (result + 7) % i
        i += 1
    }
    print(result)
}

main()
