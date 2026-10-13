let n: Int64 = 250
let nn = Int(n * n)
var a = [Int64](repeating: 0, count: nn)
var b = [Int64](repeating: 0, count: nn)
var c = [Int64](repeating: 0, count: nn)
var i: Int64 = 0
while i < n {
    var j: Int64 = 0
    while j < n {
        a[Int(i * n + j)] = (i * 31 + j * 7) & 1023
        b[Int(i * n + j)] = (i * 17 + j * 13) & 1023
        j += 1
    }
    i += 1
}
i = 0
while i < n {
    var k: Int64 = 0
    while k < n {
        let aik = a[Int(i * n + k)]
        var j: Int64 = 0
        while j < n {
            let idx = Int(i * n + j)
            c[idx] = c[idx] + aik * b[Int(k * n + j)]
            j += 1
        }
        k += 1
    }
    i += 1
}
var s: Int64 = 0
var t = 0
while t < nn {
    s += c[t]
    t += 1
}
print(s)
