let modV = 1000000007

func lessRec(_ k1: Int, _ s1: Int, _ k2: Int, _ s2: Int) -> Bool {
    if k1 != k2 {
        return k1 < k2
    }
    return s1 > s2
}

func swapRun(_ rk: inout [Int], _ rs: inout [Int], _ rv: inout [Int], _ rt: inout [Int], _ a: Int, _ b: Int) {
    rk.swapAt(a, b)
    rs.swapAt(a, b)
    rv.swapAt(a, b)
    rt.swapAt(a, b)
}

func siftMaxRun(_ rk: inout [Int], _ rs: inout [Int], _ rv: inout [Int], _ rt: inout [Int], _ start: Int, _ n: Int) {
    var i = start
    while true {
        let l = i * 2 + 1
        if l >= n {
            break
        }
        var best = l
        let r = l + 1
        if r < n && lessRec(rk[best], rs[best], rk[r], rs[r]) {
            best = r
        }
        if lessRec(rk[i], rs[i], rk[best], rs[best]) {
            swapRun(&rk, &rs, &rv, &rt, i, best)
            i = best
        } else {
            break
        }
    }
}

func heapsortRun(_ rk: inout [Int], _ rs: inout [Int], _ rv: inout [Int], _ rt: inout [Int], _ n: Int) {
    var start = n / 2 - 1
    while start >= 0 {
        siftMaxRun(&rk, &rs, &rv, &rt, start, n)
        start -= 1
    }
    var end = n - 1
    while end > 0 {
        swapRun(&rk, &rs, &rv, &rt, 0, end)
        siftMaxRun(&rk, &rs, &rv, &rt, 0, end)
        end -= 1
    }
}

func heapLess(_ allK: [Int], _ allS: [Int], _ runPos: [Int], _ ra: Int, _ rb: Int) -> Bool {
    let pa = runPos[ra]
    let pb = runPos[rb]
    return lessRec(allK[pa], allS[pa], allK[pb], allS[pb])
}

func siftMinMerge(_ heap: inout [Int], _ hsz: Int, _ allK: [Int], _ allS: [Int], _ runPos: [Int]) {
    var i = 0
    while true {
        let l = i * 2 + 1
        if l >= hsz {
            break
        }
        var best = l
        let rr = l + 1
        if rr < hsz && heapLess(allK, allS, runPos, heap[rr], heap[best]) {
            best = rr
        }
        if heapLess(allK, allS, runPos, heap[best], heap[i]) {
            heap.swapAt(i, best)
            i = best
        } else {
            break
        }
    }
}

func run() {
    var rng = 555123456
    var globalSeq = 1
    var l1K: [Int] = []
    var l1V: [Int] = []
    var hits = 0
    var ck = 0

    var rk = [Int](repeating: 0, count: 12000)
    var rs = [Int](repeating: 0, count: 12000)
    var rv = [Int](repeating: 0, count: 12000)
    var rt = [Int](repeating: 0, count: 12000)

    for _ in 0..<4 {
        var allK: [Int] = []
        var allS: [Int] = []
        var allV: [Int] = []
        var allT: [Int] = []
        allK.reserveCapacity(120000)
        allS.reserveCapacity(120000)
        allV.reserveCapacity(120000)
        allT.reserveCapacity(120000)
        var runPos: [Int] = []
        var runEnd: [Int] = []

        for _ in 0..<8 {
            for j in 0..<12000 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let k = rng % 40000
                rng = (rng * 1103515245 + 12345) & 2147483647
                let tomb = (rng % 10) == 0 ? 1 : 0
                var val = 0
                if tomb == 0 {
                    rng = (rng * 1103515245 + 12345) & 2147483647
                    val = 1 + (rng % 100000)
                }
                rk[j] = k
                rs[j] = globalSeq
                rv[j] = val
                rt[j] = tomb
                globalSeq += 1
            }
            heapsortRun(&rk, &rs, &rv, &rt, 12000)
            let st = allK.count
            var prevK = -1
            for j in 0..<12000 {
                if rk[j] != prevK {
                    allK.append(rk[j])
                    allS.append(rs[j])
                    allV.append(rv[j])
                    allT.append(rt[j])
                    prevK = rk[j]
                }
            }
            runPos.append(st)
            runEnd.append(allK.count)
        }

        if !l1K.isEmpty {
            let st = allK.count
            for j in 0..<l1K.count {
                allK.append(l1K[j])
                allS.append(0)
                allV.append(l1V[j])
                allT.append(0)
            }
            runPos.append(st)
            runEnd.append(allK.count)
        }

        var heap: [Int] = []
        for r in 0..<runPos.count {
            if runPos[r] < runEnd[r] {
                heap.append(r)
                var hi = heap.count - 1
                while hi > 0 {
                    let p = (hi - 1) >> 1
                    if heapLess(allK, allS, runPos, heap[hi], heap[p]) {
                        heap.swapAt(hi, p)
                        hi = p
                    } else {
                        break
                    }
                }
            }
        }

        var newK: [Int] = []
        var newV: [Int] = []
        newK.reserveCapacity(40000)
        newV.reserveCapacity(40000)
        var lastK = -1
        var hsz = heap.count
        while hsz > 0 {
            let topR = heap[0]
            let pos = runPos[topR]
            let k = allK[pos]
            let v = allV[pos]
            let t = allT[pos]
            runPos[topR] = pos + 1
            if runPos[topR] < runEnd[topR] {
                siftMinMerge(&heap, hsz, allK, allS, runPos)
            } else {
                hsz -= 1
                if hsz > 0 {
                    heap[0] = heap[hsz]
                    siftMinMerge(&heap, hsz, allK, allS, runPos)
                }
            }
            if k != lastK {
                lastK = k
                if t == 0 {
                    newK.append(k)
                    newV.append(v)
                }
            }
        }

        l1K = newK
        l1V = newV
        let nL1 = l1K.count
        ck = (ck * 37 + nL1) % modV

        for _ in 0..<60000 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let qk = rng % 40000
            var lo = 0
            var hi = nL1
            while lo < hi {
                let mid = (lo + hi) >> 1
                if l1K[mid] < qk {
                    lo = mid + 1
                } else {
                    hi = mid
                }
            }
            if lo < nL1 && l1K[lo] == qk {
                hits += 1
                ck = (ck * 31 + l1V[lo]) % modV
            }
        }
    }

    print("\(hits)\n\(ck)")
}

run()
