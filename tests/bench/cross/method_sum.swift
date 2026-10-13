struct Acc {
    var n: Int64 = 0
    mutating func add(_ x: Int64) {
        n += x
    }
}

var a = Acc()
var i: Int64 = 0
while i < 8_000_000 {
    a.add(i & 7)
    i += 1
}
print(a.n)
