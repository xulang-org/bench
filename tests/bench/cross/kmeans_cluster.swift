let modV = 1000000007

func run() {
    let n = 8192
    let d = 8
    let k = 16
    var rng = 84848484

    var gt = [Double](repeating: 0.0, count: k * d)
    for c in 0..<(k * d) {
        rng = (rng * 1103515245 + 12345) & 2147483647
        gt[c] = Double((rng % 1000) - 500) / 16.0
    }

    var pts = [Double](repeating: 0.0, count: n * d)
    var assign = [Int](repeating: 0, count: n)
    for i in 0..<n {
        let g = i & 15
        for dim in 0..<d {
            rng = (rng * 1103515245 + 12345) & 2147483647
            pts[i * d + dim] = gt[g * d + dim] + Double((rng % 129) - 64) / 32.0
        }
    }

    var cent = [Double](repeating: 0.0, count: k * d)
    var sumC = [Double](repeating: 0.0, count: k * d)
    for c in 0..<(k * d) {
        cent[c] = pts[c]
    }
    var cnt = [Int](repeating: 0, count: k)
    var finalInertia = 0.0

    for _ in 0..<25 {
        for c in 0..<(k * d) {
            sumC[c] = 0.0
        }
        for c in 0..<k {
            cnt[c] = 0
        }
        var inertia = 0.0
        for i in 0..<n {
            let pb = i * d
            var bestC = 0
            var bestD = 1.0e18
            for c in 0..<k {
                let cb = c * d
                var dist = 0.0
                for dim in 0..<d {
                    let diff = pts[pb + dim] - cent[cb + dim]
                    dist += diff * diff
                }
                if dist < bestD {
                    bestD = dist
                    bestC = c
                }
            }
            assign[i] = bestC
            cnt[bestC] += 1
            inertia += bestD
            let cb = bestC * d
            for dim in 0..<d {
                sumC[cb + dim] += pts[pb + dim]
            }
        }
        for c in 0..<k {
            if cnt[c] > 0 {
                let inv = 1.0 / Double(cnt[c])
                let cb = c * d
                for dim in 0..<d {
                    cent[cb + dim] = sumC[cb + dim] * inv
                }
            }
        }
        finalInertia = inertia
    }

    var ack = 0
    for i in 0..<n {
        ack = (ack * 31 + assign[i] + 1) % modV
    }

    print("\(ack)\n\(Int((finalInertia + 0.5).rounded(.down)))")
}

run()
