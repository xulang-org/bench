let modV = 1000000007

func mainFunc() {
    var sFin = [Int](repeating: 0, count: 80)
    var sOp = [Int](repeating: 0, count: 80)
    var sM0 = [Int](repeating: 0, count: 80)
    var sM1 = [Int](repeating: 0, count: 80)
    var sM2 = [Int](repeating: 0, count: 80)
    var sM3 = [Int](repeating: 0, count: 80)
    var sLen = [Int](repeating: 0, count: 80)
    var sSeed = [Int](repeating: 0, count: 80)

    var rng = 987654321
    for i in 0..<80 {
        let tier = i % 4
        rng = (rng * 1103515245 + 12345) & 2147483647
        let ln: Int
        if tier == 0 { ln = 13 + (rng % 90) }
        else if tier == 1 { ln = 126 + (rng % 300) }
        else if tier == 2 { ln = 500 + (rng % 1500) }
        else { ln = 2000 + (rng % 2048) }
        sFin[i] = (i % 5) != 0 ? 1 : 0
        sOp[i] = (i & 1) == 0 ? 2 : 1
        rng = (rng * 1103515245 + 12345) & 2147483647
        sM0[i] = (rng >> 8) & 255
        rng = (rng * 1103515245 + 12345) & 2147483647
        sM1[i] = (rng >> 8) & 255
        rng = (rng * 1103515245 + 12345) & 2147483647
        sM2[i] = (rng >> 8) & 255
        rng = (rng * 1103515245 + 12345) & 2147483647
        sM3[i] = (rng >> 8) & 255
        rng = (rng * 1103515245 + 12345) & 2147483647
        sSeed[i] = (rng >> 4) & 255
        sLen[i] = ln
    }

    var wire: [Int] = []
    wire.reserveCapacity(131072)
    var totalBytes = 0
    var ck = 0
    for rnd in 0..<180 {
        wire.removeAll(keepingCapacity: true)
        for idx in 0..<80 {
            let fin = sFin[idx]
            let op = sOp[idx]
            let ln = sLen[idx]
            let seed = sSeed[idx]
            let m0 = (sM0[idx] + rnd) & 255
            let m1 = (sM1[idx] + idx) & 255
            let m2 = sM2[idx]
            let m3 = sM3[idx]

            wire.append(((fin & 1) << 7) | (op & 15))
            if ln <= 125 {
                wire.append(128 | ln)
            } else {
                wire.append(128 | 126)
                wire.append((ln >> 8) & 255)
                wire.append(ln & 255)
            }
            wire.append(m0)
            wire.append(m1)
            wire.append(m2)
            wire.append(m3)

            for j in 0..<ln {
                let pb = (seed + j * 17 + rnd * 3) & 255
                let mk: Int
                switch j & 3 {
                case 1: mk = m1
                case 2: mk = m2
                case 3: mk = m3
                default: mk = m0
                }
                wire.append(pb ^ mk)
            }
        }

        var pos = 0
        let wlen = wire.count
        while pos < wlen {
            let b0 = wire[pos]
            let b1 = wire[pos + 1]
            pos += 2
            let fin = (b0 >> 7) & 1
            let op = b0 & 15
            let masked = (b1 >> 7) & 1
            var plen = b1 & 127
            if plen == 126 {
                plen = (wire[pos] << 8) | wire[pos + 1]
                pos += 2
            }
            var m0 = 0
            var m1 = 0
            var m2 = 0
            var m3 = 0
            if masked != 0 {
                m0 = wire[pos]
                m1 = wire[pos + 1]
                m2 = wire[pos + 2]
                m3 = wire[pos + 3]
                pos += 4
            }
            var fh = (fin * 17 + op) % modV
            for j in 0..<plen {
                let mk: Int
                switch j & 3 {
                case 1: mk = m1
                case 2: mk = m2
                case 3: mk = m3
                default: mk = m0
                }
                let ch = wire[pos + j] ^ mk
                fh = (fh * 131 + ch) % modV
            }
            pos += plen
            totalBytes += plen
            ck = (ck * 31 + fh) % modV
        }
    }
    print(totalBytes)
    print(ck)
}

mainFunc()
