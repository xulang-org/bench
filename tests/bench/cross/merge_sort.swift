// Osprey (MIT): benchmarks/cases/mergesort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Top-down merge sort with alternating split and fresh growable vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical split/merge/push loops in all ports; see tests/bench/osprey/README.md.

func hashAt(_ seed: Int64, _ i: Int64) -> Int64 {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func merge(_ left: [Int64], _ right: [Int64]) -> [Int64] {
    var result: [Int64] = []
    var i: Int64 = 0
    var j: Int64 = 0
    while i < Int64(left.count) && j < Int64(right.count) {
        if right[Int(j)] < left[Int(i)] {
            result.append(right[Int(j)])
            j += 1
        } else {
            result.append(left[Int(i)])
            i += 1
        }
    }
    while i < Int64(left.count) { result.append(left[Int(i)]); i += 1 }
    while j < Int64(right.count) { result.append(right[Int(j)]); j += 1 }
    return result
}

func mergeSort(_ xs: [Int64]) -> [Int64] {
    if xs.count < 2 {
        var result: [Int64] = []
        var i: Int64 = 0
        while i < Int64(xs.count) { result.append(xs[Int(i)]); i += 1 }
        return result
    }
    var evens: [Int64] = []
    var odds: [Int64] = []
    var i: Int64 = 0
    while i < Int64(xs.count) { evens.append(xs[Int(i)]); i += 2 }
    i = 1
    while i < Int64(xs.count) { odds.append(xs[Int(i)]); i += 2 }
    let left = mergeSort(evens)
    let right = mergeSort(odds)
    return merge(left, right)
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
        let sorted = mergeSort(xs)
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
