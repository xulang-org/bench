import Foundation

func qsort(_ a: inout [Int64], _ low: Int, _ high: Int) {
    if low >= high { return }
    let pivot = a[(low + high) / 2]
    var i = low
    var j = high
    while i <= j {
        while a[i] < pivot { i += 1 }
        while a[j] > pivot { j -= 1 }
        if i <= j {
            a.swapAt(i, j)
            i += 1
            j -= 1
        }
    }
    if low < j { qsort(&a, low, j) }
    if i < high { qsort(&a, i, high) }
}

var checksum: Int64 = 0
var arr = [Int64](repeating: 0, count: 100000)

for round in 0..<5 {
    var seed: Int64 = 123456789 + Int64(round) * 1013904223
    for k in 0..<100000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647
        arr[k] = seed
    }
    qsort(&arr, 0, 99999)
    for i in 0..<100000 {
        checksum = (checksum * 31 + arr[i]) % 1000000007
    }
}

print(checksum)
