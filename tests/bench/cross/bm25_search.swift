let modV = 1000000007

func ilog2X1000(_ x: Int, _ lut: [Int]) -> Int {
    var b = 0
    var t = x
    while t >= 2 {
        t >>= 1
        b += 1
    }
    let frac = ((x - (1 << b)) << 4) >> b
    return b * 1000 + lut[frac]
}

func run() {
    let nDocs = 6000
    let vocab = 2048
    var rng = 777654321
    let lut = [0, 87, 170, 248, 322, 392, 459, 524, 585, 644, 700, 755, 807, 858, 907, 954]

    var docLen = [Int](repeating: 0, count: nDocs)
    var scores = [Int](repeating: 0, count: nDocs)
    var stamp = [Int](repeating: 0, count: nDocs)
    var touched = [Int](repeating: 0, count: nDocs)

    var df = [Int](repeating: 0, count: vocab)
    var postOff = [Int](repeating: 0, count: vocab + 1)
    var cur = [Int](repeating: 0, count: vocab)
    var idf = [Int](repeating: 0, count: vocab)

    var rawD: [Int] = []
    var rawT: [Int] = []
    var rawF: [Int] = []
    rawD.reserveCapacity(nDocs * 40)
    rawT.reserveCapacity(nDocs * 40)
    rawF.reserveCapacity(nDocs * 40)
    var tmp = [Int](repeating: 0, count: 64)

    var totalLen = 0
    for d in 0..<nDocs {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let dl = 24 + (rng % 32)
        docLen[d] = dl
        totalLen += dl
        for j in 0..<dl {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let term: Int
            if (rng % 3) == 0 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                term = rng % 64
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647
                term = 64 + (rng % (vocab - 64))
            }
            tmp[j] = term
        }
        for j in 1..<dl {
            let key = tmp[j]
            var p = j - 1
            while p >= 0 && tmp[p] > key {
                tmp[p + 1] = tmp[p]
                p -= 1
            }
            tmp[p + 1] = key
        }
        var j = 0
        while j < dl {
            let term = tmp[j]
            var cnt = 1
            while j + cnt < dl && tmp[j + cnt] == term {
                cnt += 1
            }
            df[term] += 1
            rawD.append(d)
            rawT.append(term)
            rawF.append(cnt)
            j += cnt
        }
    }

    for t in 0..<vocab {
        postOff[t + 1] = postOff[t] + df[t]
        cur[t] = postOff[t]
    }
    let totalP = postOff[vocab]
    var postDoc = [Int](repeating: 0, count: totalP)
    var postTf = [Int](repeating: 0, count: totalP)
    for i in 0..<rawD.count {
        let term = rawT[i]
        let idx = cur[term]
        postDoc[idx] = rawD[i]
        postTf[idx] = rawF[i]
        cur[term] = idx + 1
    }

    for t in 0..<vocab {
        if df[t] > 0 {
            let ratioX1024 = (((nDocs - df[t]) * 2 + 1) * 1024) / (df[t] * 2 + 1) + 1024
            idf[t] = ilog2X1000(ratioX1024, lut) - 10000
        }
    }

    let avgdlX100 = (totalLen * 100) / nDocs
    var dlNorm = [Int](repeating: 0, count: nDocs)
    for d in 0..<nDocs {
        dlNorm[d] = 250 + (750 * docLen[d] * 100) / avgdlX100
    }

    var qterms = [Int](repeating: 0, count: 5)
    var topD = [Int](repeating: 0, count: 10)
    var topS = [Int](repeating: 0, count: 10)
    var totalHits = 0
    var ck = 0

    for q in 1...2000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let qn = 3 + (rng % 3)
        rng = (rng * 1103515245 + 12345) & 2147483647
        qterms[0] = rng % 64
        for j in 1..<qn {
            rng = (rng * 1103515245 + 12345) & 2147483647
            qterms[j] = 64 + (rng % (vocab - 64))
        }
        var tCnt = 0
        for j in 0..<qn {
            let term = qterms[j]
            let it = idf[term]
            if it > 0 {
                let pend = postOff[term + 1]
                for p in postOff[term]..<pend {
                    let docI = postDoc[p]
                    let tf = postTf[p]
                    let sc = (it * tf * 2200) / (tf * 1000 + (12 * dlNorm[docI]) / 10)
                    if stamp[docI] != q {
                        stamp[docI] = q
                        scores[docI] = sc
                        touched[tCnt] = docI
                        tCnt += 1
                    } else {
                        scores[docI] += sc
                    }
                }
            }
        }
        var kFound = 0
        for i in 0..<tCnt {
            let docI = touched[i]
            let s = scores[docI]
            if kFound < 10 || s > topS[9] || (s == topS[9] && docI < topD[9]) {
                var pos = 9
                if kFound < 10 {
                    pos = kFound
                    kFound += 1
                }
                while pos > 0 && (s > topS[pos - 1] || (s == topS[pos - 1] && docI < topD[pos - 1])) {
                    topS[pos] = topS[pos - 1]
                    topD[pos] = topD[pos - 1]
                    pos -= 1
                }
                topS[pos] = s
                topD[pos] = docI
            }
        }
        totalHits += kFound
        for r in 0..<kFound {
            ck = (ck * 31 + topD[r] * 10007 + topS[r]) % modV
        }
    }

    print("\(totalHits)\n\(ck)")
}

run()
