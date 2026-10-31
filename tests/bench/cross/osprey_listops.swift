// Osprey (MIT): benchmarks/cases/listops; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.

func hashAt(_ seed: Int64, _ i: Int64) -> Int64 {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func sumList(_ xs: [Int64], _ i: Int64) -> Int64 {
    if i == Int64(xs.count) { return 0 }
    return xs[Int(i)] + sumList(xs, i + 1)
}

func belowList(_ xs: [Int64], _ i: Int64) -> Int64 {
    if i == Int64(xs.count) { return 0 }
    var add: Int64 = 0
    if xs[Int(i)] < 500 { add = 1 }
    return add + belowList(xs, i + 1)
}

func main() {
    var total: Int64 = 0
    var t: Int64 = 0
    while t < 8 {
        var xs: [Int64] = []
        var i: Int64 = 0
        while i < 4000 {
            xs.append(hashAt(1 + t * 131, i) % 1000)
            i += 1
        }
        total = (total + sumList(xs, 0) + belowList(xs, 0)) % 1000000007
        t += 1
    }
    print(total)
}

main()
