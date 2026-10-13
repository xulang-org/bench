struct HeapItem {
    var freq: Int32
    var nid: Int32
}

class MinHeap {
    var items: [HeapItem]
    var size: Int

    init() {
        items = [HeapItem](repeating: HeapItem(freq: 0, nid: 0), count: 256)
        size = 0
    }

    @inline(__always)
    static func less(_ a: HeapItem, _ b: HeapItem) -> Bool {
        if a.freq != b.freq {
            return a.freq < b.freq
        }
        return a.nid < b.nid
    }

    func push(_ freq: Int32, _ nid: Int32) {
        var i = size
        size += 1
        let item = HeapItem(freq: freq, nid: nid)
        while i > 0 {
            let p = (i - 1) / 2
            if MinHeap.less(item, items[p]) {
                items[i] = items[p]
                i = p
            } else {
                break
            }
        }
        items[i] = item
    }

    func pop() -> HeapItem {
        let top = items[0]
        size -= 1
        let last = items[size]
        if size == 0 {
            return top
        }
        var i = 0
        while i * 2 + 1 < size {
            let left = i * 2 + 1
            let right = left + 1
            var best = left
            if right < size && MinHeap.less(items[right], items[left]) {
                best = right
            }
            if MinHeap.less(items[best], last) {
                items[i] = items[best]
                i = best
            } else {
                break
            }
        }
        items[i] = last
        return top
    }
}

class HuffmanTree {
    var nodesFreq: [Int32]
    var nodesCh: [Int32]
    var nodesLeft: [Int32]
    var nodesRight: [Int32]
    var codes: [Int32]
    var codeLens: [Int32]

    init() {
        nodesFreq = [Int32](repeating: 0, count: 256)
        nodesCh = [Int32](repeating: 0, count: 256)
        nodesLeft = [Int32](repeating: -1, count: 256)
        nodesRight = [Int32](repeating: -1, count: 256)
        codes = [Int32](repeating: 0, count: 64)
        codeLens = [Int32](repeating: 0, count: 64)
    }

    func getCodes(_ nid: Int, _ currCode: Int32, _ currLen: Int32) {
        if nodesLeft[nid] == -1 && nodesRight[nid] == -1 {
            let ch = Int(nodesCh[nid])
            codes[ch] = currCode
            codeLens[ch] = currLen
            return
        }
        getCodes(Int(nodesLeft[nid]), (currCode << 1) | 0, currLen + 1)
        getCodes(Int(nodesRight[nid]), (currCode << 1) | 1, currLen + 1)
    }
}

func isqrt(_ n: Int64) -> Int64 {
    if n <= 0 { return 0 }
    var x = n
    var y = (x + 1) / 2
    while y < x {
        x = y
        y = (x + n / x) / 2
    }
    return x
}

func main() {
    var raw = [Int32](repeating: 0, count: 20000)
    var freqs = [Int32](repeating: 0, count: 64)
    var seed: Int64 = 123456789
    for i in 0..<20000 {
        seed = (seed &* 1103515245 &+ 12345) & 0x7fffffff
        let c = Int32(isqrt(seed % 4096))
        raw[i] = c
        freqs[Int(c)] += 1
    }

    let tree = HuffmanTree()
    let heap = MinHeap()
    var nodeCount = 0

    for ch in 0..<64 {
        if freqs[ch] > 0 {
            let nid = Int32(nodeCount)
            nodeCount += 1
            tree.nodesFreq[Int(nid)] = freqs[ch]
            tree.nodesCh[Int(nid)] = Int32(ch)
            heap.push(freqs[ch], nid)
        }
    }

    while heap.size > 1 {
        let item1 = heap.pop()
        let item2 = heap.pop()
        let pid = Int32(nodeCount)
        nodeCount += 1
        tree.nodesFreq[Int(pid)] = item1.freq + item2.freq
        tree.nodesCh[Int(pid)] = -1
        tree.nodesLeft[Int(pid)] = item1.nid
        tree.nodesRight[Int(pid)] = item2.nid
        heap.push(tree.nodesFreq[Int(pid)], pid)
    }

    let root = Int(heap.pop().nid)
    tree.getCodes(root, 0, 0)

    var bitBuf = [UInt32]()
    var bitCount = 0
    var currWord: UInt32 = 0
    var currBits = 0

    for b in raw {
        let bu = Int(b)
        let c = tree.codes[bu]
        let l = tree.codeLens[bu]
        var bitIdx = l - 1
        while bitIdx >= 0 {
            let bit = UInt32((c >> bitIdx) & 1)
            currWord = (currWord << 1) | bit
            currBits += 1
            if currBits == 32 {
                bitBuf.append(currWord)
                currWord = 0
                currBits = 0
            }
            bitCount += 1
            bitIdx -= 1
        }
    }
    if currBits > 0 {
        currWord = currWord << (32 - currBits)
        bitBuf.append(currWord)
    }

    var totalChecksum: Int64 = 0
    for _ in 0..<50 {
        var curNode = root
        var decodedSum: Int64 = 0
        for i in 0..<bitCount {
            let wordIdx = i / 32
            let bitPos = 31 - (i % 32)
            let bit = (bitBuf[wordIdx] >> bitPos) & 1
            if bit == 0 {
                curNode = Int(tree.nodesLeft[curNode])
            } else {
                curNode = Int(tree.nodesRight[curNode])
            }
            if tree.nodesLeft[curNode] == -1 && tree.nodesRight[curNode] == -1 {
                let ch = Int64(tree.nodesCh[curNode])
                decodedSum = (decodedSum &* 33 &+ ch) & 0x7fffffff
                curNode = root
            }
        }
        totalChecksum = (totalChecksum &+ decodedSum) & 0x7fffffff
    }

    print(totalChecksum)
}

main()
