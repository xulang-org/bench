var s: [UInt8] = []
var i: Int64 = 0
let chunk: [UInt8] = Array("0123456789".utf8)
while i < 100_000 {
    s.append(contentsOf: chunk)
    i += 1
}
var c: Int64 = 0
var j: Int64 = 0
let n = Int64(s.count)
while j < n {
    c += Int64(s[Int(j)])
    j += 1
}
print(c)
print(n)
