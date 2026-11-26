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
    let rng = SciRandom(113)
    var under: Int64 = 0
    for _ in 0..<5000000 {
        let x = rng.nextDouble()
        let y = rng.nextDouble()
        if x * x + y * y <= 1.0 {
            under += 1
        }
    }
    print(under)
}

main()
