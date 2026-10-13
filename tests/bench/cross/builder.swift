import Foundation

var b = [UInt8]()
b.reserveCapacity(64)
var i: Int64 = 0
while i < 100000 {
    b.append(UInt8(48 + (i % 10)))
    i += 1
}
var c: Int64 = 0
var j = 0
let n = b.count
while j < n {
    c += Int64(b[j])
    j += 1
}
print(c)
print(n)
