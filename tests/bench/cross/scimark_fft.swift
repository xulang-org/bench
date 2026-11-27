#if canImport(Glibc)
import Glibc
#elseif canImport(Darwin)
import Darwin
#endif

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

func fftBitreverse(_ data: inout [Double], _ n: Int) {
    var j = 0
    for i in 0..<(n - 1) {
        if i < j {
            let ii = 2 * i
            let jj = 2 * j
            let tr = data[ii]
            let ti = data[ii + 1]
            data[ii] = data[jj]
            data[ii + 1] = data[jj + 1]
            data[jj] = tr
            data[jj + 1] = ti
        }
        var k = n >> 1
        while k <= j {
            j -= k
            k >>= 1
        }
        j += k
    }
}

func fftTransform(_ data: inout [Double], _ n: Int, _ direction: Double) {
    fftBitreverse(&data, n)
    var dual = 1
    for _ in 0..<10 {
        var wReal = 1.0
        var wImag = 0.0
        let theta = 2.0 * direction * Double.pi / (2.0 * Double(dual))
        let s = sin(theta)
        let t = sin(theta * 0.5)
        let s2 = 2.0 * t * t

        var b = 0
        while b < n {
            let i = 2 * b
            let j = 2 * (b + dual)
            let wdReal = data[j]
            let wdImag = data[j + 1]
            data[j] = data[i] - wdReal
            data[j + 1] = data[i + 1] - wdImag
            data[i] += wdReal
            data[i + 1] += wdImag
            b += 2 * dual
        }

        for a in 1..<dual {
            let tmpReal = wReal - s * wImag - s2 * wReal
            let tmpImag = wImag + s * wReal - s2 * wImag
            wReal = tmpReal
            wImag = tmpImag
            b = 0
            while b < n {
                let i = 2 * (b + a)
                let j = 2 * (b + a + dual)
                let z1Real = data[j]
                let z1Imag = data[j + 1]
                let wdReal = wReal * z1Real - wImag * z1Imag
                let wdImag = wReal * z1Imag + wImag * z1Real
                data[j] = data[i] - wdReal
                data[j + 1] = data[i + 1] - wdImag
                data[i] += wdReal
                data[i + 1] += wdImag
                b += 2 * dual
            }
        }
        dual *= 2
    }
}

func main() {
    let n = 1024
    let rng = SciRandom(101010)
    var orig = [Double](repeating: 0.0, count: 2 * n)
    var data = [Double](repeating: 0.0, count: 2 * n)
    for i in 0..<(2 * n) {
        orig[i] = rng.nextDouble()
    }

    let norm = 1.0 / Double(n)
    var acc = 0.0
    for rep in 0..<200 {
        for i in 0..<(2 * n) {
            data[i] = orig[i]
        }
        fftTransform(&data, n, -1.0)
        acc += abs(data[0]) + abs(data[1]) + abs(data[2 * ((rep * 7) % 512)])
        fftTransform(&data, n, 1.0)
        for i in 0..<(2 * n) {
            data[i] *= norm
        }
        acc += abs(data[2 * ((rep * 13) % 512)])
    }
    print(Int64((acc * 10.0 + 0.5).rounded(.down)))
}

main()
