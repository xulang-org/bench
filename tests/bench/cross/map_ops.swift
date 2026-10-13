var m: [Int64: Int64] = [:]
var i: Int64 = 0
while i < 200_000 {
    m[i] = 1
    i += 1
}
var s: Int64 = 0
i = 0
while i < 200_000 {
    s += m[i]! + i
    i += 1
}
print(s)
