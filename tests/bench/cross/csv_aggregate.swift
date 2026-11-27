func main() {
    let prefixes = [
        "tokyo", "oslo", "lima", "cairo", "paris", "rome", "zurich", "seoul",
        "bergen", "kyoto", "milan", "vienna", "prague", "dublin", "lisbon", "athens"
    ]
    var stBytes: [Int] = []
    stBytes.reserveCapacity(1024)
    var stOff = [Int](repeating: 0, count: 64)
    var stLen = [Int](repeating: 0, count: 64)
    for i in 0..<64 {
        let p = prefixes[i & 15]
        stOff[i] = stBytes.count
        for b in p.utf8 {
            stBytes.append(Int(b))
        }
        stBytes.append(95)
        stBytes.append(48 + (i / 10))
        stBytes.append(48 + (i % 10))
        stLen[i] = stBytes.count - stOff[i]
    }

    var buf: [Int] = []
    buf.reserveCapacity(1600000)
    var digs = [Int](repeating: 0, count: 16)
    var rng = 135792468
    for _ in 0..<100000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let si = (rng >> 10) & 63
        rng = (rng * 1103515245 + 12345) & 2147483647
        let temp = (rng % 1999) - 999
        let off = stOff[si]
        let ln = stLen[si]
        for k in 0..<ln {
            buf.append(stBytes[off + k])
        }
        buf.append(59)
        var av = temp
        if av < 0 {
            buf.append(45)
            av = -av
        }
        let whole = av / 10
        if whole == 0 {
            buf.append(48)
        } else {
            var w = whole
            var dc = 0
            while w > 0 {
                digs[dc] = 48 + (w % 10)
                dc += 1
                w /= 10
            }
            var di = dc - 1
            while di >= 0 {
                buf.append(digs[di])
                di -= 1
            }
        }
        buf.append(46)
        buf.append(48 + (av % 10))
        buf.append(10)
    }

    let n = buf.count
    var firstDot = 0
    while firstDot < n && buf[firstDot] != 46 {
        firstDot += 1
    }
    let origFrac = buf[firstDot + 1] - 48

    let cap = 256
    let mask = 255
    var kStart = [Int](repeating: -1, count: cap)
    var kLen = [Int](repeating: 0, count: cap)
    var stMin = [Int](repeating: 0, count: cap)
    var stMax = [Int](repeating: 0, count: cap)
    var stSum = [Int](repeating: 0, count: cap)
    var stCnt = [Int](repeating: 0, count: cap)
    var occ = [Int](repeating: 0, count: cap)

    var totRows = 0
    var totCk = 0
    for rd in 0..<10 {
        buf[firstDot + 1] = 48 + ((origFrac + rd) % 10)
        for i in 0..<cap {
            kStart[i] = -1
        }
        var pos = 0
        var rows = 0
        while pos < n {
            let sStart = pos
            var h = 0
            while buf[pos] != 59 {
                h = (h * 131 + buf[pos]) & 2147483647
                pos += 1
            }
            let sLen = pos - sStart
            pos += 1
            var neg = false
            if buf[pos] == 45 {
                neg = true
                pos += 1
            }
            var v = 0
            while buf[pos] != 46 {
                v = v * 10 + (buf[pos] - 48)
                pos += 1
            }
            pos += 1
            v = v * 10 + (buf[pos] - 48)
            pos += 1
            if neg { v = -v }
            if pos < n && buf[pos] == 10 { pos += 1 }
            rows += 1

            var slot = h & mask
            while true {
                let ks = kStart[slot]
                if ks == -1 {
                    kStart[slot] = sStart
                    kLen[slot] = sLen
                    stMin[slot] = v
                    stMax[slot] = v
                    stSum[slot] = v
                    stCnt[slot] = 1
                    break
                }
                if kLen[slot] == sLen {
                    var eq = true
                    for ci in 0..<sLen {
                        if buf[ks + ci] != buf[sStart + ci] {
                            eq = false
                            break
                        }
                    }
                    if eq {
                        if v < stMin[slot] { stMin[slot] = v }
                        if v > stMax[slot] { stMax[slot] = v }
                        stSum[slot] += v
                        stCnt[slot] += 1
                        break
                    }
                }
                slot = (slot + 1) & mask
            }
        }

        var occLen = 0
        for i in 0..<cap {
            if kStart[i] != -1 {
                occ[occLen] = i
                occLen += 1
            }
        }
        if occLen > 1 {
            for i in 1..<occLen {
                let keySlot = occ[i]
                var j = i - 1
                while j >= 0 {
                    let a = occ[j]
                    let la = kLen[a]
                    let lb = kLen[keySlot]
                    let ml = la < lb ? la : lb
                    var cmp = 0
                    for t in 0..<ml {
                        let ba = buf[kStart[a] + t]
                        let bb = buf[kStart[keySlot] + t]
                        if ba != bb {
                            cmp = (ba < bb) ? -1 : 1
                            break
                        }
                    }
                    if cmp == 0 {
                        if la < lb { cmp = -1 }
                        else if la > lb { cmp = 1 }
                    }
                    if cmp > 0 {
                        occ[j + 1] = occ[j]
                        j -= 1
                    } else {
                        break
                    }
                }
                occ[j + 1] = keySlot
            }
        }

        var ck = 0
        for i in 0..<occLen {
            let sl = occ[i]
            var sMod = stSum[sl] % 1000000007
            if sMod < 0 { sMod += 1000000007 }
            let term = ((i + 1) * 7 + (stMin[sl] + 1000) * 13 + (stMax[sl] + 1000) * 17 + stCnt[sl] * 19 + sMod) % 1000000007
            ck = (ck * 1000003 + term) % 1000000007
        }
        totRows += rows
        totCk = (totCk * 31 + ck) % 1000000007
    }
    print(totRows)
    print(totCk)
}

main()
