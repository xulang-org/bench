// Osprey (MIT): benchmarks/cases/nestedloop; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey nestedloop: descending 250^3 modular multiply/adds.

func loop_k(_ i: Int64, _ j: Int64, _ n: Int64, _ initial: Int64) -> Int64 {
    var k: Int64 = n
    var acc: Int64 = initial
    while k != 0 {
        acc = (acc + i * j * k) % 1000000007
        k -= 1
    }
    return acc
}
func loop_j(_ i: Int64, _ n: Int64, _ initial: Int64) -> Int64 {
    var j: Int64 = n
    var acc: Int64 = initial
    while j != 0 {
        acc = loop_k(i, j, n, acc)
        j -= 1
    }
    return acc
}
func loop_i(_ n: Int64) -> Int64 {
    var i: Int64 = n
    var acc: Int64 = 0
    while i != 0 {
        acc = loop_j(i, n, acc)
        i -= 1
    }
    return acc
}

func main() {
    var result: Int64 = loop_i(250)
    print(result)
}

main()
