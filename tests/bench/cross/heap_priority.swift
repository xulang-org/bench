import Foundation

struct MinHeap {
    var data = [Int64]()

    var count: Int {
        return data.count
    }

    mutating func push(_ val: Int64) {
        data.append(val)
        var j = data.count - 1
        while j > 0 {
            let i = (j - 1) >> 1
            if data[j] >= data[i] { break }
            let tmp = data[j]
            data[j] = data[i]
            data[i] = tmp
            j = i
        }
    }

    mutating func pop() -> Int64 {
        let out = data[0]
        let last = data.removeLast()
        if !data.isEmpty {
            data[0] = last
            var root = 0
            let n = data.count
            while true {
                var child = root * 2 + 1
                if child >= n { break }
                if child + 1 < n && data[child + 1] < data[child] {
                    child += 1
                }
                if data[child] < data[root] {
                    let tmp = data[root]
                    data[root] = data[child]
                    data[child] = tmp
                    root = child
                } else {
                    break
                }
            }
        }
        return out
    }
}

var h = MinHeap()
var seed: Int64 = 123456789
var checksum: Int64 = 0

for _ in 0..<200000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    h.push(seed)
}

for _ in 0..<100000 {
    let v = h.pop()
    checksum = (checksum * 31 + v) % 1000000007
}

for _ in 0..<100000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    h.push(seed)
}

while h.count > 0 {
    let v = h.pop()
    checksum = (checksum * 31 + v) % 1000000007
}

print(checksum)
