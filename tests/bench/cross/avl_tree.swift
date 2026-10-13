class AVL {
    var keys: [Int64]
    var vals: [Int64]
    var heights: [Int32]
    var lefts: [Int32]
    var rights: [Int32]
    var count: Int32
    var root: Int32

    init(cap: Int) {
        keys = [Int64](repeating: 0, count: cap)
        vals = [Int64](repeating: 0, count: cap)
        heights = [Int32](repeating: 0, count: cap)
        lefts = [Int32](repeating: -1, count: cap)
        rights = [Int32](repeating: -1, count: cap)
        count = 0
        root = -1
    }

    @inline(__always)
    func getH(_ idx: Int32) -> Int32 {
        if idx == -1 { return 0 }
        return heights[Int(idx)]
    }

    @inline(__always)
    func upd(_ idx: Int32) {
        let u = Int(idx)
        let hl = getH(lefts[u])
        let hr = getH(rights[u])
        heights[u] = 1 + (hl > hr ? hl : hr)
    }

    @inline(__always)
    func bf(_ idx: Int32) -> Int32 {
        let u = Int(idx)
        return getH(lefts[u]) - getH(rights[u])
    }

    func rotR(_ y: Int32) -> Int32 {
        let yu = Int(y)
        let x = lefts[yu]
        let xu = Int(x)
        let t2 = rights[xu]
        rights[xu] = y
        lefts[yu] = t2
        upd(y)
        upd(x)
        return x
    }

    func rotL(_ x: Int32) -> Int32 {
        let xu = Int(x)
        let y = rights[xu]
        let yu = Int(y)
        let t2 = lefts[yu]
        lefts[yu] = x
        rights[xu] = t2
        upd(x)
        upd(y)
        return y
    }

    func insert(_ idx: Int32, _ key: Int64, _ val: Int64) -> Int32 {
        if idx == -1 {
            let nid = count
            count += 1
            let nu = Int(nid)
            keys[nu] = key
            vals[nu] = val
            heights[nu] = 1
            lefts[nu] = -1
            rights[nu] = -1
            return nid
        }
        let u = Int(idx)
        if key < keys[u] {
            lefts[u] = insert(lefts[u], key, val)
        } else if key > keys[u] {
            rights[u] = insert(rights[u], key, val)
        } else {
            vals[u] = val
            return idx
        }
        upd(idx)
        let b = bf(idx)
        if b > 1 && key < keys[Int(lefts[u])] {
            return rotR(idx)
        }
        if b < -1 && key > keys[Int(rights[u])] {
            return rotL(idx)
        }
        if b > 1 && key > keys[Int(lefts[u])] {
            lefts[u] = rotL(lefts[u])
            return rotR(idx)
        }
        if b < -1 && key < keys[Int(rights[u])] {
            rights[u] = rotR(rights[u])
            return rotL(idx)
        }
        return idx
    }

    func search(_ key: Int64) -> Int64 {
        var cur = root
        while cur != -1 {
            let u = Int(cur)
            let k = keys[u]
            if key == k {
                return vals[u]
            } else if key < k {
                cur = lefts[u]
            } else {
                cur = rights[u]
            }
        }
        return 0
    }
}

func main() {
    let t = AVL(cap: 100000)
    var seed: Int64 = 123456789
    for i in 0..<80000 {
        seed = (seed &* 1103515245 &+ 12345) & 0x7fffffff
        let k = seed % 200000
        let v = (Int64(i) &* 3 &+ 7) & 0x7fffffff
        t.root = t.insert(t.root, k, v)
    }

    var checksum: Int64 = 0
    for _ in 0..<300000 {
        seed = (seed &* 1103515245 &+ 12345) & 0x7fffffff
        let k = seed % 200000
        let val = t.search(k)
        checksum = (checksum &* 31 &+ val) % 1000000007
    }
    print(checksum)
}

main()
