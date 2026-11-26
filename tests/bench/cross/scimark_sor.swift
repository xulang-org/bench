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
    let n = 100
    let rng = SciRandom(101010)
    var g = [Double](repeating: 0.0, count: n * n)
    for idx in 0..<(n * n) {
        g[idx] = rng.nextDouble()
    }

    let omega = 1.25
    let omegaOverFour = omega * 0.25
    let oneMinusOmega = 1.0 - omega
    for _ in 0..<500 {
        for i in 1..<(n - 1) {
            let row = i * n
            let up = (i - 1) * n
            let dn = (i + 1) * n
            for j in 1..<(n - 1) {
                g[row + j] = omegaOverFour * (g[up + j] + g[dn + j] + g[row + j - 1] + g[row + j + 1]) + oneMinusOmega * g[row + j]
            }
        }
    }

    var total = 0.0
    for idx in 0..<(n * n) {
        total += g[idx]
    }
    print(Int64((total * 1000.0 + 0.5).rounded(.down)))
}

main()
