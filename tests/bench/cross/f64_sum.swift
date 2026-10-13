var s: Float64 = 0.0
var i: Int64 = 0
while i < 20_000_000 {
    s += Float64(i & 1023)
    i += 1
}
print(Int64(s))
