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
    var a0 = [Double](repeating: 0.0, count: n * n)
    var a = [Double](repeating: 0.0, count: n * n)
    var piv = [Int64](repeating: 0, count: n)
    for idx in 0..<(n * n) {
        a0[idx] = rng.nextDouble()
    }

    var luAcc = 0.0
    var pivChk: Int64 = 0
    for _ in 0..<30 {
        for idx in 0..<(n * n) {
            a[idx] = a0[idx]
        }
        for j in 0..<n {
            var jp = j
            var t = abs(a[j * n + j])
            for i in (j + 1)..<n {
                let ab = abs(a[i * n + j])
                if ab > t {
                    jp = i
                    t = ab
                }
            }
            piv[j] = Int64(jp)
            if jp != j {
                for k in 0..<n {
                    let tmp = a[j * n + k]
                    a[j * n + k] = a[jp * n + k]
                    a[jp * n + k] = tmp
                }
            }
            if j < n - 1 {
                let recp = 1.0 / a[j * n + j]
                for k in (j + 1)..<n {
                    a[k * n + j] *= recp
                }
                for ii in (j + 1)..<n {
                    let aii = a[ii * n + j]
                    for jj in (j + 1)..<n {
                        a[ii * n + jj] -= aii * a[j * n + jj]
                    }
                }
            }
        }
        for idx in 0..<(n * n) {
            luAcc += abs(a[idx])
        }
        var ps: Int64 = 0
        for idx in 0..<n {
            ps += piv[idx]
        }
        pivChk = (pivChk + ps) % 1000000007
    }
    let ans = Int64((luAcc * 100.0 + 0.5).rounded(.down)) + pivChk
    print(ans)
}

main()
