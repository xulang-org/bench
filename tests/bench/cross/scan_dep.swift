let n = 4096
var a = Array(repeating: Int64(0), count: n)
var i = 0
while i < n {
    a[i] = Int64(i & 1023)
    i += 1
}
var t: Int64 = 0
while t < 20000 {
    i = 1
    while i < n {
        a[i] = a[i] + (a[i - 1] & 1023)
        i += 1
    }
    t += 1
}
print(a[n - 1])
