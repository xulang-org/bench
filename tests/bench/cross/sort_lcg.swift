var a: [Int64] = []
var i: Int64 = 0
var x: Int64 = 12345
while i < 100_000 {
    x = (x &* 1_103_515_245 &+ 12345) & 0x7FFF_FFFF
    a.append(x)
    i += 1
}
a.sort()
print(a[0] + a[50_000] * 2 + a[99_999] * 3)
