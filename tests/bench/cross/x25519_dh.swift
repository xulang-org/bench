func copy16(_ dst: inout [Int], _ src: [Int]) {
    for i in 0..<16 {
        dst[i] = src[i]
    }
}

func car25519(_ o: inout [Int]) {
    for i in 0..<16 {
        let c = o[i] >> 16
        o[i] &= 65535
        if i < 15 {
            o[i + 1] += c
        } else {
            o[0] += c * 38
        }
    }
}

func faddNew(_ o: inout [Int], _ a: [Int], _ b: [Int]) {
    for i in 0..<16 {
        o[i] = a[i] + b[i]
    }
}

func fsubNew(_ o: inout [Int], _ a: [Int], _ b: [Int]) {
    o[0] = a[0] + 130996 - b[0]
    for i in 1..<16 {
        o[i] = a[i] + 131070 - b[i]
    }
    car25519(&o)
}

func fsubSelf(_ a: inout [Int], _ b: [Int]) {
    a[0] = a[0] + 130996 - b[0]
    for i in 1..<16 {
        a[i] = a[i] + 131070 - b[i]
    }
    car25519(&a)
}

func fmulCore(_ o: inout [Int], _ a: [Int], _ b: [Int], _ t: inout [Int]) {
    for k in 0..<32 { t[k] = 0 }
    for i in 0..<16 {
        let ai = a[i]
        for j in 0..<16 {
            t[i + j] += ai * b[j]
        }
    }
    for i in 0..<16 {
        o[i] = t[i] + 38 * t[i + 16]
    }
    car25519(&o)
    car25519(&o)
}

func fmulSelf(_ a: inout [Int], _ b: [Int], _ t: inout [Int]) {
    for k in 0..<32 { t[k] = 0 }
    for i in 0..<16 {
        let ai = a[i]
        for j in 0..<16 {
            t[i + j] += ai * b[j]
        }
    }
    for i in 0..<16 {
        a[i] = t[i] + 38 * t[i + 16]
    }
    car25519(&a)
    car25519(&a)
}

func fsqSelf(_ a: inout [Int], _ t: inout [Int]) {
    for k in 0..<32 { t[k] = 0 }
    for i in 0..<16 {
        let ai = a[i]
        for j in 0..<16 {
            t[i + j] += ai * a[j]
        }
    }
    for i in 0..<16 {
        a[i] = t[i] + 38 * t[i + 16]
    }
    car25519(&a)
    car25519(&a)
}

func fsqNew(_ o: inout [Int], _ a: [Int], _ t: inout [Int]) {
    fmulCore(&o, a, a, &t)
}

func cswap(_ p: inout [Int], _ q: inout [Int], _ bit: Int) {
    if bit != 0 {
        for i in 0..<16 {
            let tmp = p[i]
            p[i] = q[i]
            q[i] = tmp
        }
    }
}

func finv(_ o: inout [Int], _ inV: [Int], _ t: inout [Int]) {
    var c = inV
    var a = 253
    while a >= 0 {
        fsqSelf(&c, &t)
        if a != 2 && a != 4 {
            fmulSelf(&c, inV, &t)
        }
        a -= 1
    }
    copy16(&o, c)
}

func pack25519(_ o: inout [Int], _ nIn: [Int]) {
    var t = nIn
    car25519(&t)
    car25519(&t)
    car25519(&t)
    var m = [Int](repeating: 0, count: 16)
    for _ in 0..<2 {
        m[0] = t[0] - 65517
        var borrow = 0
        if m[0] < 0 {
            m[0] += 65536
            borrow = 1
        }
        for i in 1..<15 {
            m[i] = t[i] - 65535 - borrow
            if m[i] < 0 {
                m[i] += 65536
                borrow = 1
            } else {
                borrow = 0
            }
        }
        m[15] = t[15] - 32767 - borrow
        if m[15] >= 0 {
            copy16(&t, m)
        }
    }
    for i in 0..<16 {
        o[2 * i] = t[i] & 255
        o[2 * i + 1] = (t[i] >> 8) & 255
    }
}

func x25519(_ q: inout [Int], _ nBytes: [Int], _ pBytes: [Int], _ a24: [Int], _ t: inout [Int]) {
    var z = nBytes
    z[0] &= 248
    z[31] = (z[31] & 127) | 64

    var x = [Int](repeating: 0, count: 16)
    for i in 0..<16 {
        x[i] = pBytes[2 * i] | (pBytes[2 * i + 1] << 8)
    }
    x[15] &= 32767

    var a = [Int](repeating: 0, count: 16)
    var b = x
    var c = [Int](repeating: 0, count: 16)
    var d = [Int](repeating: 0, count: 16)
    var e = [Int](repeating: 0, count: 16)
    var f = [Int](repeating: 0, count: 16)
    a[0] = 1
    d[0] = 1

    var bitI = 254
    while bitI >= 0 {
        let r = (z[bitI >> 3] >> (bitI & 7)) & 1
        cswap(&a, &b, r)
        cswap(&c, &d, r)
        faddNew(&e, a, c)
        fsubSelf(&a, c)
        faddNew(&c, b, d)
        fsubSelf(&b, d)
        fsqNew(&d, e, &t)
        fsqNew(&f, a, &t)
        fmulSelf(&a, c, &t)
        fmulCore(&c, b, e, &t)
        copy16(&e, a)
        for ii in 0..<16 {
            e[ii] += c[ii]
        }
        fsubSelf(&a, c)
        fsqNew(&b, a, &t)
        fsubNew(&c, d, f)
        fmulCore(&a, c, a24, &t)
        for ii in 0..<16 {
            a[ii] += d[ii]
        }
        fmulSelf(&c, a, &t)
        fmulCore(&a, d, f, &t)
        fmulCore(&d, b, x, &t)
        fsqNew(&b, e, &t)
        cswap(&a, &b, r)
        cswap(&c, &d, r)
        bitI -= 1
    }
    copy16(&e, c)
    finv(&c, e, &t)
    fmulSelf(&a, c, &t)
    pack25519(&q, a)
}

func run() {
    var a24 = [Int](repeating: 0, count: 16)
    a24[0] = 56129
    a24[1] = 1

    var t = [Int](repeating: 0, count: 32)
    var k = [Int](repeating: 0, count: 32)
    var u = [Int](repeating: 0, count: 32)
    var out = [Int](repeating: 0, count: 32)
    k[0] = 9
    u[0] = 9

    for _ in 0..<100 {
        x25519(&out, k, u, a24, &t)
        u = k
        k = out
    }

    let hexChars: [Character] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
    var s = ""
    for v in k {
        s.append(hexChars[(v >> 4) & 15])
        s.append(hexChars[v & 15])
    }
    print("100\n\(s)")
}

run()
