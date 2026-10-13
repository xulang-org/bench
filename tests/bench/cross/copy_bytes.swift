let n: Int = 1048576
var src = Array(repeating: Int64(0), count: n)
var dst = Array(repeating: Int64(0), count: n)
var i = 0
while i < n {
    let v = Int64(i & 1023)
    src[i] = v
    dst[i] = v
    i += 1
}
var t: Int64 = 0
while t < 80 {
    i = 0
    while i < n {
        dst[i] = src[i]
        i += 1
    }
    t += 1
}
var s: Int64 = 0
i = 0
while i < n {
    s += dst[i]
    i += 1
}
print(s)
