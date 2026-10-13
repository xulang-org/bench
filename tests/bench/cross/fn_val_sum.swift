func bump(_ x: Int64) -> Int64 {
    x + 1
}

let f: (Int64) -> Int64 = bump
var s: Int64 = 0
var i: Int64 = 0
while i < 8_000_000 {
    s += f(i & 7)
    i += 1
}
print(s)
