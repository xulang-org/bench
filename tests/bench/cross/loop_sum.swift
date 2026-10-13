var s: Int64 = 0
var i: Int64 = 0
while i < 50_000_000 {
    s += i & 1023
    i += 1
}
print(s)
