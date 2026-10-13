import Foundation

var s = ""
s.reserveCapacity(100000)
var i: Int64 = 0
while i < 10000 {
    s += "0123456789"
    i += 1
}
var hits: Int64 = 0
var k: Int64 = 0
let needle = "89012"
while k < 20 {
    if s.utf8.contains(57) {
        hits += 1
    }
    if s.contains(needle) {
        hits += 1
    }
    k += 1
}
print(hits)
print(s.utf8.count)
