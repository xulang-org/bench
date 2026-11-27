class SciRandom {
    var m: [Int64]
    var idxI: Int
    var idxJ: Int

    init(_ seed: Int64) {
        let m1: Int64 = 2147483647
        let m2: Int64 = 65536
        var arr = [Int64](repeating: 0, count: 17)
        var jseed = seed < 0 ? -seed : seed
        if jseed > m1 { jseed = m1 }
        if jseed % 2 == 0 { jseed -= 1 }
        let k0: Int64 = 9069 % m2
        let k1: Int64 = 9069 / m2
        var j0 = jseed % m2
        var j1 = jseed / m2
        for iloop in 0..<17 {
            jseed = j0 * k0
            j1 = (jseed / m2 + j0 * k1 + j1 * k0) % (m2 / 2)
            j0 = jseed % m2
            arr[iloop] = j0 + m2 * j1
        }
        self.m = arr
        self.idxI = 4
        self.idxJ = 16
    }

    @inline(__always)
    func nextDouble() -> Double {
        let m1: Int64 = 2147483647
        let dm1: Double = 1.0 / 2147483647.0
        var k = m[idxI] - m[idxJ]
        if k < 0 { k += m1 }
        m[idxJ] = k
        idxI = idxI == 0 ? 16 : idxI - 1
        idxJ = idxJ == 0 ? 16 : idxJ - 1
        return dm1 * Double(k)
    }
}

func main() {
    let n = 10000
    let nz = 50000
    let nr = 5
    let rng = SciRandom(101010)

    var x = [Double](repeating: 0.0, count: n)
    var y = [Double](repeating: 0.0, count: n)
    var val = [Double](repeating: 0.0, count: nz)
    var col = [Int](repeating: 0, count: nz)
    var row = [Int](repeating: 0, count: n + 1)

    for i in 0..<n {
        x[i] = rng.nextDouble()
    }
    for i in 0..<nz {
        val[i] = rng.nextDouble()
    }
    for r in 0..<n {
        let rowR = row[r]
        row[r + 1] = rowR + nr
        var step = r / nr
        if step < 1 { step = 1 }
        for j in 0..<nr {
            col[rowR + j] = (j * step) % n
        }
    }

    var acc = 0.0
    for rep in 0..<500 {
        for r in 0..<n {
            var s = 0.0
            var ii = row[r]
            let end = row[r + 1]
            while ii < end {
                s += x[col[ii]] * val[ii]
                ii += 1
            }
            y[r] = s
        }
        acc += y[rep % n]
    }

    var total = acc
    for i in 0..<n {
        total += y[i]
    }
    print(Int64((total * 1000.0 + 0.5).rounded(.down)))
}

main()
