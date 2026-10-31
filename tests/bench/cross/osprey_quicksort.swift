// Osprey (MIT): benchmarks/cases/quicksort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey first-element-pivot quicksort; two partition passes and fresh vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical partition/concatenate/push loops in all ports; see tests/bench/osprey/README.md.

func hashAt(_ seed: Int64, _ i: Int64) -> Int64 {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func quicksort(_ xs: [Int64]) -> [Int64] {
    if xs.isEmpty { return [] }
    let pivot = xs[0]
    var below: [Int64] = []
    var atLeast: [Int64] = []
    var i: Int64 = 1
    while i < Int64(xs.count) {
        if xs[Int(i)] < pivot { below.append(xs[Int(i)]) }
        i += 1
    }
    i = 1
    while i < Int64(xs.count) {
        if xs[Int(i)] >= pivot { atLeast.append(xs[Int(i)]) }
        i += 1
    }
    var sorted = quicksort(below)
    sorted.append(pivot)
    let right = quicksort(atLeast)
    i = 0
    while i < Int64(right.count) { sorted.append(right[Int(i)]); i += 1 }
    return sorted
}

func main() {
    var total: Int64 = 0
    var t: Int64 = 0
    while t < 8 {
        var xs: [Int64] = []
        var i: Int64 = 0
        while i < 2000 {
            xs.append(hashAt(1 + t * 131, i) % 100000)
            i += 1
        }
        let sorted = quicksort(xs)
        var weight: Int64 = 0
        i = 0
        while i < Int64(sorted.count) {
            weight = (weight + sorted[Int(i)] * (i + 1)) % 1000000007
            i += 1
        }
        total = (total + weight) % 1000000007
        t += 1
    }
    print(total)
}

main()
