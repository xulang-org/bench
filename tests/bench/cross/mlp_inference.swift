func run() {
    let d0 = 64
    let d1 = 128
    let d2 = 64
    let d3 = 16
    var rng = 73737373

    var w1 = [Double](repeating: 0.0, count: d1 * d0)
    var b1 = [Double](repeating: 0.0, count: d1)
    var w2 = [Double](repeating: 0.0, count: d2 * d1)
    var b2 = [Double](repeating: 0.0, count: d2)
    var w3 = [Double](repeating: 0.0, count: d3 * d2)
    var b3 = [Double](repeating: 0.0, count: d3)

    for k in 0..<(d1 * d0) {
        rng = (rng * 1103515245 + 12345) & 2147483647
        w1[k] = Double((rng % 255) - 127) / 1024.0
    }
    for k in 0..<d1 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        b1[k] = Double((rng % 63) - 31) / 256.0
    }
    for k in 0..<(d2 * d1) {
        rng = (rng * 1103515245 + 12345) & 2147483647
        w2[k] = Double((rng % 255) - 127) / 1024.0
    }
    for k in 0..<d2 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        b2[k] = Double((rng % 63) - 31) / 256.0
    }
    for k in 0..<(d3 * d2) {
        rng = (rng * 1103515245 + 12345) & 2147483647
        w3[k] = Double((rng % 255) - 127) / 1024.0
    }
    for k in 0..<d3 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        b3[k] = Double((rng % 63) - 31) / 256.0
    }

    var x = [Double](repeating: 0.0, count: d0)
    var h1 = [Double](repeating: 0.0, count: d1)
    var h2 = [Double](repeating: 0.0, count: d2)
    var clsSum = 0
    var logitAcc = 0.0

    for _ in 0..<2000 {
        for i in 0..<d0 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            x[i] = Double((rng % 255) - 127) / 128.0
        }
        for j in 0..<d1 {
            var s = b1[j]
            let base = j * d0
            for i in 0..<d0 {
                s += x[i] * w1[base + i]
            }
            h1[j] = s > 0.0 ? s : 0.0
        }
        for j in 0..<d2 {
            var s = b2[j]
            let base = j * d1
            for i in 0..<d1 {
                s += h1[i] * w2[base + i]
            }
            h2[j] = s > 0.0 ? s : 0.0
        }
        var bestC = 0
        var bestV = -1.0e18
        for j in 0..<d3 {
            var s = b3[j]
            let base = j * d2
            for i in 0..<d2 {
                s += h2[i] * w3[base + i]
            }
            if s > bestV {
                bestV = s
                bestC = j
            }
        }
        clsSum += bestC
        logitAcc += abs(bestV)
    }

    print("\(clsSum)\n\(Int((logitAcc * 10.0 + 0.5).rounded(.down)))")
}

run()
