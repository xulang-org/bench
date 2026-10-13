let n = 65536
var nxt = Array(repeating: Int64(0), count: n)
var i = 0
while i < n {
    nxt[i] = Int64(((i * 7) + 1) & (n - 1))
    i += 1
}
var k: Int64 = 0
var s: Int64 = 0
while s < 20000000 {
    k = nxt[Int(k)]
    s += 1
}
print(k)
