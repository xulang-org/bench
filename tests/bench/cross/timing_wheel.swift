let modV = 1000000007
let maxNodes = 131072

final class Wheel {
    var tExp = [Int](repeating: 0, count: maxNodes)
    var tPer = [Int](repeating: 0, count: maxNodes)
    var tRep = [Int](repeating: 0, count: maxNodes)
    var tPay = [Int](repeating: 0, count: maxNodes)
    var tSt = [Int](repeating: 0, count: maxNodes)
    var tPrev = [Int](repeating: -1, count: maxNodes)
    var tNext = [Int](repeating: -1, count: maxNodes)
    var tBkt = [Int](repeating: -1, count: maxNodes)
    var bHead = [Int](repeating: -1, count: 512)
    var bTail = [Int](repeating: -1, count: 512)
    var freeStack: [Int]
    var freeTop = maxNodes

    init() {
        var fs = [Int](repeating: 0, count: maxNodes)
        for i in 0..<maxNodes {
            fs[i] = maxNodes - 1 - i
        }
        freeStack = fs
    }

    func bktPush(_ b: Int, _ u: Int) {
        let tail = bTail[b]
        tPrev[u] = tail
        tNext[u] = -1
        tBkt[u] = b
        if tail != -1 {
            tNext[tail] = u
        } else {
            bHead[b] = u
        }
        bTail[b] = u
    }

    func bktRemove(_ u: Int) {
        let b = tBkt[u]
        let pr = tPrev[u]
        let nx = tNext[u]
        if pr != -1 {
            tNext[pr] = nx
        } else {
            bHead[b] = nx
        }
        if nx != -1 {
            tPrev[nx] = pr
        } else {
            bTail[b] = pr
        }
        tPrev[u] = -1
        tNext[u] = -1
        tBkt[u] = -1
    }

    func scheduleNode(_ u: Int, _ exp: Int, _ now: Int) {
        tExp[u] = exp
        tSt[u] = 1
        if (exp - now) < 256 {
            bktPush(exp & 255, u)
        } else {
            bktPush(256 + ((exp >> 8) & 255), u)
        }
    }
}

func run() {
    let ringH = 16384
    let w = Wheel()
    var rng = 888777666
    var handles = [Int](repeating: -1, count: ringH)
    var hWr = 0
    var fired = 0
    var canceled = 0
    var ck = 0

    for now in 0..<160000 {
        for _ in 0..<3 {
            if w.freeTop > 0 {
                w.freeTop -= 1
                let u = w.freeStack[w.freeTop]
                rng = (rng * 1103515245 + 12345) & 2147483647
                let delay: Int
                if (rng % 10) < 6 {
                    rng = (rng * 1103515245 + 12345) & 2147483647
                    delay = 1 + (rng % 250)
                } else {
                    rng = (rng * 1103515245 + 12345) & 2147483647
                    delay = 256 + (rng % 4096)
                }
                rng = (rng * 1103515245 + 12345) & 2147483647
                var per = 0
                var rep = 0
                if (rng % 5) == 0 {
                    rng = (rng * 1103515245 + 12345) & 2147483647
                    per = 17 + (rng % 200)
                    rep = 2
                }
                rng = (rng * 1103515245 + 12345) & 2147483647
                let pay = rng % 100000
                w.tPer[u] = per
                w.tRep[u] = rep
                w.tPay[u] = pay
                w.scheduleNode(u, now + delay, now)
                handles[hWr] = u
                hWr = (hWr + 1) & 16383
            }
        }

        rng = (rng * 1103515245 + 12345) & 2147483647
        let ci = rng & 16383
        let cu = handles[ci]
        if cu != -1 && w.tSt[cu] == 1 {
            w.bktRemove(cu)
            w.tSt[cu] = 0
            w.freeStack[w.freeTop] = cu
            w.freeTop += 1
            handles[ci] = -1
            canceled += 1
        }

        let tick = now + 1
        if (tick & 255) == 0 {
            let cb = 256 + ((tick >> 8) & 255)
            var u = w.bHead[cb]
            w.bHead[cb] = -1
            w.bTail[cb] = -1
            while u != -1 {
                let nx = w.tNext[u]
                w.tPrev[u] = -1
                w.tNext[u] = -1
                w.tBkt[u] = -1
                w.bktPush(w.tExp[u] & 255, u)
                u = nx
            }
        }

        let b0 = tick & 255
        var u = w.bHead[b0]
        w.bHead[b0] = -1
        w.bTail[b0] = -1
        while u != -1 {
            let nx = w.tNext[u]
            w.tPrev[u] = -1
            w.tNext[u] = -1
            w.tBkt[u] = -1
            fired += 1
            ck = (ck * 31 + w.tPay[u] * 7 + tick) % modV
            if w.tRep[u] > 0 {
                w.tRep[u] -= 1
                w.scheduleNode(u, tick + w.tPer[u], tick)
            } else {
                w.tSt[u] = 0
                w.freeStack[w.freeTop] = u
                w.freeTop += 1
            }
            u = nx
        }
    }

    ck = (ck * 37 + canceled) % modV
    print("\(fired)\n\(ck)")
}

run()
