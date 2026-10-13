var a: [Int64] = []
var i: Int64 = 0
while i < 2_000_000 {
    a.append(i)
    i += 1
}
var s: Int64 = 0
var j: Int64 = 0
let n = Int64(a.count)
while j < n {
    s += a[Int(j)] & 7
    j += 1
}
print(s)
