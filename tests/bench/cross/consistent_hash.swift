let modV = 1000000007

func mix32(_ x: Int) -> Int {
    let mask = 4294967295
    let mul = 73244475
    var h = x & mask
    h ^= h >> 16
    h = (h * mul) & mask
    h ^= h >> 16
    h = (h * mul) & mask
    h ^= h >> 16
    return h
}

func siftMaxRing(_ rt: inout [Int], _ rn: inout [Int], _ start: Int, _ n: Int) {
    var i = start
    while true {
        let l = i * 2 + 1
        if l >= n {
            break
        }
        var best = l
        let r = l + 1
        if r < n && rt[r] > rt[best] {
            best = r
        }
        if rt[i] < rt[best] {
            rt.swapAt(i, best)
            rn.swapAt(i, best)
            i = best
        } else {
            break
        }
    }
}

func heapsortRing(_ rt: inout [Int], _ rn: inout [Int], _ n: Int) {
    var start = n / 2 - 1
    while start >= 0 {
        siftMaxRing(&rt, &rn, start, n)
        start -= 1
    }
    var end = n - 1
    while end > 0 {
        rt.swapAt(0, end)
        rn.swapAt(0, end)
        siftMaxRing(&rt, &rn, 0, end)
        end -= 1
    }
}

func buildRing(_ alive: [Int], _ ringTok: inout [Int], _ ringNode: inout [Int]) -> Int {
    let maxNodes = 48
    let vnodes = 128
    let goldC = 2654435769
    var sz = 0
    for nid in 0..<maxNodes {
        if alive[nid] == 1 {
            for v in 0..<vnodes {
                ringTok[sz] = mix32(((nid << 10) | v) ^ goldC)
                ringNode[sz] = nid
                sz += 1
            }
        }
    }
    heapsortRing(&ringTok, &ringNode, sz)
    return sz
}

func routeTok(_ ringTok: [Int], _ ringNode: [Int], _ tok: Int, _ sz: Int) -> Int {
    var lo = 0
    var hi = sz
    while lo < hi {
        let mid = (lo + hi) >> 1
        if ringTok[mid] < tok {
            lo = mid + 1
        } else {
            hi = mid
        }
    }
    if lo == sz {
        lo = 0
    }
    return ringNode[lo]
}

func run() {
    let mask32 = 4294967295
    let maxNodes = 48
    let vnodes = 128
    let nKeys = 150000

    var alive = [Int](repeating: 0, count: maxNodes)
    var nodeLoad = [Int](repeating: 0, count: maxNodes)
    for nid in 0..<32 {
        alive[nid] = 1
    }

    var ringTok = [Int](repeating: 0, count: maxNodes * vnodes)
    var ringNode = [Int](repeating: 0, count: maxNodes * vnodes)
    var keyTok = [Int](repeating: 0, count: nKeys)
    var prevOwner = [Int](repeating: 0, count: nKeys)

    for i in 0..<nKeys {
        keyTok[i] = mix32((i * 2654435761 + 12345) & mask32)
    }

    var ringSz = buildRing(alive, &ringTok, &ringNode)
    var ck = 0
    for p in 0..<4 {
        let salt = p * 7919
        for i in 0..<nKeys {
            let t = mix32((keyTok[i] + salt) & mask32)
            let owner = routeTok(ringTok, ringNode, t, ringSz)
            nodeLoad[owner] += 1
            ck = (ck * 31 + owner + 1) % modV
        }
    }

    for i in 0..<nKeys {
        prevOwner[i] = routeTok(ringTok, ringNode, keyTok[i], ringSz)
    }

    var totalMoved = 0
    for step in 0..<4 {
        if step == 0 {
            alive[32] = 1; alive[33] = 1; alive[34] = 1; alive[35] = 1
        } else if step == 1 {
            alive[5] = 0; alive[19] = 0
        } else if step == 2 {
            alive[36] = 1; alive[37] = 1; alive[38] = 1; alive[39] = 1; alive[40] = 1; alive[41] = 1
        } else {
            alive[2] = 0; alive[11] = 0; alive[24] = 0; alive[33] = 0
        }
        ringSz = buildRing(alive, &ringTok, &ringNode)
        var moved = 0
        for i in 0..<nKeys {
            let o = routeTok(ringTok, ringNode, keyTok[i], ringSz)
            if o != prevOwner[i] {
                moved += 1
                prevOwner[i] = o
            }
            ck = (ck * 31 + o + 1) % modV
        }
        totalMoved += moved
        ck = (ck * 37 + moved) % modV
    }

    for nid in 0..<maxNodes {
        ck = (ck * 31 + nodeLoad[nid]) % modV
    }

    print("\(totalMoved)\n\(ck)")
}

run()
