let modV = 1000000007

final class BPlusTree {
    var isLeaf: [Int] = []
    var nkeys: [Int] = []
    var nextLeaf: [Int] = []
    var keys: [Int] = []
    var vals: [Int] = []
    var children: [Int] = []
    var pathNode = [Int](repeating: 0, count: 16)
    var pathIdx = [Int](repeating: 0, count: 16)
    var root: Int = 0

    init() {
        root = allocNode(1)
    }

    func allocNode(_ leaf: Int) -> Int {
        let u = isLeaf.count
        isLeaf.append(leaf)
        nkeys.append(0)
        nextLeaf.append(-1)
        for _ in 0..<32 {
            keys.append(0)
            vals.append(0)
        }
        for _ in 0..<33 {
            children.append(-1)
        }
        return u
    }

    func descendLeaf(_ k: Int) -> Int {
        var u = root
        while isLeaf[u] == 0 {
            let base = u * 32
            var lo = 0
            var hi = nkeys[u]
            while lo < hi {
                let mid = (lo + hi) >> 1
                if keys[base + mid] <= k {
                    lo = mid + 1
                } else {
                    hi = mid
                }
            }
            u = children[u * 33 + lo]
        }
        return u
    }

    func insert(_ k: Int, _ v: Int) {
        var u = root
        var depth = 0
        while isLeaf[u] == 0 {
            let base = u * 32
            var lo = 0
            var hi = nkeys[u]
            while lo < hi {
                let mid = (lo + hi) >> 1
                if keys[base + mid] <= k {
                    lo = mid + 1
                } else {
                    hi = mid
                }
            }
            pathNode[depth] = u
            pathIdx[depth] = lo
            depth += 1
            u = children[u * 33 + lo]
        }

        let base = u * 32
        var n = nkeys[u]
        var lo = 0
        var hi = n
        while lo < hi {
            let mid = (lo + hi) >> 1
            if keys[base + mid] < k {
                lo = mid + 1
            } else {
                hi = mid
            }
        }
        if lo < n && keys[base + lo] == k {
            vals[base + lo] = v
            return
        }
        var j = n
        while j > lo {
            keys[base + j] = keys[base + j - 1]
            vals[base + j] = vals[base + j - 1]
            j -= 1
        }
        keys[base + lo] = k
        vals[base + lo] = v
        n += 1
        nkeys[u] = n
        if n < 32 {
            return
        }

        let r = allocNode(1)
        let rbase = r * 32
        for m in 0..<16 {
            keys[rbase + m] = keys[base + 16 + m]
            vals[rbase + m] = vals[base + 16 + m]
        }
        nkeys[u] = 16
        nkeys[r] = 16
        nextLeaf[r] = nextLeaf[u]
        nextLeaf[u] = r
        var upKey = keys[rbase]
        var upRight = r

        var d = depth - 1
        while d >= 0 {
            let p = pathNode[d]
            let ins = pathIdx[d]
            let pbase = p * 32
            let pcbase = p * 33
            var pn = nkeys[p]
            var kIdx = pn
            while kIdx > ins {
                keys[pbase + kIdx] = keys[pbase + kIdx - 1]
                children[pcbase + kIdx + 1] = children[pcbase + kIdx]
                kIdx -= 1
            }
            keys[pbase + ins] = upKey
            children[pcbase + ins + 1] = upRight
            pn += 1
            nkeys[p] = pn
            if pn < 32 {
                return
            }
            let nr = allocNode(0)
            let nrbase = nr * 32
            let nrcbase = nr * 33
            let midKey = keys[pbase + 16]
            for m in 0..<15 {
                keys[nrbase + m] = keys[pbase + 17 + m]
            }
            for c in 0..<16 {
                children[nrcbase + c] = children[pcbase + 17 + c]
            }
            nkeys[p] = 16
            nkeys[nr] = 15
            upKey = midKey
            upRight = nr
            d -= 1
        }

        let newRoot = allocNode(0)
        keys[newRoot * 32] = upKey
        children[newRoot * 33] = root
        children[newRoot * 33 + 1] = upRight
        nkeys[newRoot] = 1
        root = newRoot
    }

    func lookup(_ k: Int) -> Int {
        let u = descendLeaf(k)
        let base = u * 32
        let n = nkeys[u]
        var lo = 0
        var hi = n
        while lo < hi {
            let mid = (lo + hi) >> 1
            if keys[base + mid] < k {
                lo = mid + 1
            } else {
                hi = mid
            }
        }
        if lo < n && keys[base + lo] == k {
            return vals[base + lo]
        }
        return -1
    }
}

func run() {
    let t = BPlusTree()
    var rng = 123456789

    for i in 0..<80000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let k = rng % 1000000
        rng = (rng * 1103515245 + 12345) & 2147483647
        let v = (i * 17 + (rng & 1023)) % 1000000
        t.insert(k, v)
    }

    var hits = 0
    var ck = 0
    for _ in 0..<120000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let k = rng % 1000000
        let v = t.lookup(k)
        if v >= 0 {
            hits += 1
            ck = (ck * 31 + v) % modV
        }
    }

    var rcnt = 0
    for _ in 0..<2000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let loK = rng % 999000
        let hiK = loK + 1000
        var u = t.descendLeaf(loK)
        let base0 = u * 32
        var lo = 0
        var hi = t.nkeys[u]
        while lo < hi {
            let mid = (lo + hi) >> 1
            if t.keys[base0 + mid] < loK {
                lo = mid + 1
            } else {
                hi = mid
            }
        }
        var cnt = 0
        var s = 0
        var idx = lo
        while u != -1 {
            let base = u * 32
            let n = t.nkeys[u]
            var done = false
            for j in idx..<n {
                if t.keys[base + j] > hiK {
                    done = true
                    break
                }
                cnt += 1
                s = (s + t.vals[base + j]) % modV
            }
            if done {
                break
            }
            u = t.nextLeaf[u]
            idx = 0
        }
        rcnt += cnt
        ck = (ck * 37 + s + cnt) % modV
    }

    print("\(hits + rcnt)\n\(ck)")
}

run()
