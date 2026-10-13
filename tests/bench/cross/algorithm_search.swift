func lowerBound(_ a: [Int64], _ v: Int64) -> Int64 {
    var lo = 0
    var hi = a.count
    while lo < hi {
        let mid = lo + ((hi - lo) >> 1)
        if a[mid] < v {
            lo = mid + 1
        } else {
            hi = mid
        }
    }
    return Int64(lo)
}

let n = 131072
var a = [Int64]()
a.reserveCapacity(n)
var i: Int64 = 0
while i < Int64(n) {
    a.append(i * 3)
    i += 1
}
var total: Int64 = 0
var q: Int64 = 0
while q < 4000000 {
    let v = ((q &* 1103515245 &+ 12345) & 0x3FFFF) * 3
    total += lowerBound(a, v)
    q += 1
}
print(total)
