let modV = 1000000007

final class SlabArena {
    var mem = [Int](repeating: 0, count: 256 * 256)
    var pageCls = [Int](repeating: -1, count: 256)
    var pageUsed = [Int](repeating: 0, count: 256)
    var pageHead = [Int](repeating: -1, count: 256)
    var pagePrev = [Int](repeating: -1, count: 256)
    var pageNext = [Int](repeating: -1, count: 256)
    var pageInList = [Int](repeating: 0, count: 256)
    var clsHead = [Int](repeating: -1, count: 6)
    var freeStack: [Int]
    var freeTop = 256
    let classSz = [2, 4, 8, 16, 32, 64]
    var pageAllocs = 0
    var pageReclaims = 0

    init() {
        var fs = [Int](repeating: 0, count: 256)
        for i in 0..<256 {
            fs[i] = 255 - i
        }
        freeStack = fs
    }

    func listPush(_ cls: Int, _ pg: Int) {
        let h = clsHead[cls]
        pagePrev[pg] = -1
        pageNext[pg] = h
        if h != -1 {
            pagePrev[h] = pg
        }
        clsHead[cls] = pg
        pageInList[pg] = 1
    }

    func listRemove(_ cls: Int, _ pg: Int) {
        let pr = pagePrev[pg]
        let nx = pageNext[pg]
        if pr != -1 {
            pageNext[pr] = nx
        } else {
            clsHead[cls] = nx
        }
        if nx != -1 {
            pagePrev[nx] = pr
        }
        pagePrev[pg] = -1
        pageNext[pg] = -1
        pageInList[pg] = 0
    }

    func alloc(_ cls: Int) -> Int {
        var pg = clsHead[cls]
        if pg == -1 {
            if freeTop == 0 {
                return -1
            }
            freeTop -= 1
            pg = freeStack[freeTop]
            pageAllocs += 1
            pageCls[pg] = cls
            pageUsed[pg] = 0
            let sz = classSz[cls]
            let base = pg << 8
            let cnt = 256 / sz
            for j in 0..<(cnt - 1) {
                mem[base + j * sz] = base + (j + 1) * sz
            }
            mem[base + (cnt - 1) * sz] = -1
            pageHead[pg] = base
            listPush(cls, pg)
        }
        let ptr = pageHead[pg]
        let nxtPtr = mem[ptr]
        pageHead[pg] = nxtPtr
        pageUsed[pg] += 1
        if nxtPtr == -1 {
            listRemove(cls, pg)
        }
        return ptr
    }

    func free(_ ptr: Int) {
        let pg = ptr >> 8
        let cls = pageCls[pg]
        let wasFull = pageHead[pg] == -1
        mem[ptr] = pageHead[pg]
        pageHead[pg] = ptr
        pageUsed[pg] -= 1
        if pageUsed[pg] == 0 {
            if pageInList[pg] == 1 {
                listRemove(cls, pg)
            }
            pageCls[pg] = -1
            pageHead[pg] = -1
            freeStack[freeTop] = pg
            freeTop += 1
            pageReclaims += 1
        } else if wasFull {
            listPush(cls, pg)
        }
    }
}

func run() {
    let live = 1024
    let s = SlabArena()
    var rng = 31415926
    var livePtr = [Int](repeating: -1, count: live)
    var liveCls = [Int](repeating: 0, count: live)
    var allocOk = 0
    var ck = 0

    for opI in 0..<600000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let slot = rng & 1023
        if (opI & 4095) == 4095 {
            var k = 0
            while k < live {
                let p = livePtr[k]
                if p != -1 {
                    let sz = s.classSz[liveCls[k]]
                    ck = (ck * 31 + s.mem[p] + s.mem[p + sz - 1]) % modV
                    s.free(p)
                    livePtr[k] = -1
                }
                k += 3
            }
        }
        if livePtr[slot] != -1 {
            let p = livePtr[slot]
            let sz = s.classSz[liveCls[slot]]
            ck = (ck * 31 + s.mem[p] + s.mem[p + sz - 1]) % modV
            s.free(p)
            livePtr[slot] = -1
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let r = rng % 100
            let cls: Int
            if r < 35 {
                cls = 0
            } else if r < 60 {
                cls = 1
            } else if r < 78 {
                cls = 2
            } else if r < 90 {
                cls = 3
            } else if r < 97 {
                cls = 4
            } else {
                cls = 5
            }
            let p = s.alloc(cls)
            if p >= 0 {
                let sz = s.classSz[cls]
                let tag = (opI * 13 + cls * 7 + 1) % modV
                s.mem[p] = tag
                s.mem[p + sz - 1] = (tag ^ (p * 3)) % modV
                livePtr[slot] = p
                liveCls[slot] = cls
                allocOk += 1
            }
        }
    }

    for k in 0..<live {
        let p = livePtr[k]
        if p != -1 {
            let sz = s.classSz[liveCls[k]]
            ck = (ck * 31 + s.mem[p] + s.mem[p + sz - 1]) % modV
            s.free(p)
            livePtr[k] = -1
        }
    }
    ck = (ck * 37 + s.pageAllocs * 17 + s.pageReclaims) % modV
    print("\(allocOk)\n\(ck)")
}

run()
