struct Pair {
    let l: Int
    let r: Int
}

final class Treap {
    var key: [Int] = []
    var pri: [Int] = []
    var left: [Int] = []
    var right: [Int] = []
    var freeHead = -1
    var root = -1
    var size = 0

    init() {
        key.reserveCapacity(32768)
        pri.reserveCapacity(32768)
        left.reserveCapacity(32768)
        right.reserveCapacity(32768)
    }

    func allocNode(_ k: Int, _ p: Int) -> Int {
        if freeHead != -1 {
            let idx = freeHead
            freeHead = left[idx]
            key[idx] = k
            pri[idx] = p
            left[idx] = -1
            right[idx] = -1
            return idx
        }
        let idx = key.count
        key.append(k)
        pri.append(p)
        left.append(-1)
        right.append(-1)
        return idx
    }

    func freeNode(_ idx: Int) {
        left[idx] = freeHead
        right[idx] = -1
        freeHead = idx
    }

    func split(_ u: Int, _ k: Int) -> Pair {
        if u == -1 {
            return Pair(l: -1, r: -1)
        }
        if key[u] < k {
            let p = split(right[u], k)
            right[u] = p.l
            return Pair(l: u, r: p.r)
        }
        let p = split(left[u], k)
        left[u] = p.r
        return Pair(l: p.l, r: u)
    }

    func merge(_ a: Int, _ b: Int) -> Int {
        if a == -1 { return b }
        if b == -1 { return a }
        if pri[a] > pri[b] {
            right[a] = merge(right[a], b)
            return a
        }
        left[b] = merge(a, left[b])
        return b
    }

    func contains(_ k: Int) -> Bool {
        var u = root
        while u != -1 {
            let ku = key[u]
            if k == ku { return true }
            u = (k < ku) ? left[u] : right[u]
        }
        return false
    }

    func insert(_ k: Int, _ p: Int) {
        if contains(k) { return }
        let sp = split(root, k)
        let n = allocNode(k, p)
        root = merge(merge(sp.l, n), sp.r)
        size += 1
    }

    func erase(_ k: Int) {
        let sp1 = split(root, k)
        let sp2 = split(sp1.r, k + 1)
        if sp2.l != -1 {
            freeNode(sp2.l)
            size -= 1
        }
        root = merge(sp1.l, sp2.r)
    }
}

func main() {
    let tr = Treap()
    var rng = 123456789
    var hits = 0
    var ck = 0
    for _ in 0..<120000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let op = rng % 10
        rng = (rng * 1103515245 + 12345) & 2147483647
        let k = rng % 40000
        if op < 4 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            tr.insert(k, rng)
        } else if op < 6 {
            tr.erase(k)
        } else if tr.contains(k) {
            hits += 1
            ck = (ck * 131 + k + 1) % 1000000007
        }
    }
    print(hits)
    print(ck)
    print(tr.size)
}

main()
