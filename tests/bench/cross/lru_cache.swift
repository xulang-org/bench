import Foundation

struct Node {
    var key: Int64
    var val: Int64
    var prev: Int32
    var next: Int32
}

struct LRU {
    var nodes: [Node]
    var table: [Int32]
    var head: Int32
    var tail: Int32
    var cap: Int32
    var count: Int32

    init(cap: Int, tableSize: Int) {
        self.nodes = [Node](repeating: Node(key: -1, val: 0, prev: -1, next: -1), count: cap)
        self.table = [Int32](repeating: -1, count: tableSize)
        self.head = -1
        self.tail = -1
        self.cap = Int32(cap)
        self.count = 0
    }

    mutating func removeNode(_ idx: Int32) {
        let p = nodes[Int(idx)].prev
        let n = nodes[Int(idx)].next
        if p >= 0 { nodes[Int(p)].next = n }
        else { head = n }
        if n >= 0 { nodes[Int(n)].prev = p }
        else { tail = p }
    }

    mutating func pushFront(_ idx: Int32) {
        nodes[Int(idx)].prev = -1
        nodes[Int(idx)].next = head
        if head >= 0 { nodes[Int(head)].prev = idx }
        head = idx
        if tail < 0 { tail = idx }
    }

    mutating func put(_ key: Int64, _ val: Int64) -> Int64 {
        let oldIdx = table[Int(key)]
        if oldIdx >= 0 {
            nodes[Int(oldIdx)].val = val
            removeNode(oldIdx)
            pushFront(oldIdx)
            return val
        }
        var idx: Int32 = 0
        if count < cap {
            idx = count
            count += 1
        } else {
            idx = tail
            let oldKey = nodes[Int(idx)].key
            table[Int(oldKey)] = -1
            removeNode(idx)
        }
        nodes[Int(idx)].key = key
        nodes[Int(idx)].val = val
        table[Int(key)] = idx
        pushFront(idx)
        return val
    }

    mutating func get(_ key: Int64) -> Int64 {
        let idx = table[Int(key)]
        if idx < 0 { return -1 }
        removeNode(idx)
        pushFront(idx)
        return nodes[Int(idx)].val
    }
}

var lru = LRU(cap: 1000, tableSize: 3000)
var seed: Int64 = 123456789
var checksum: Int64 = 0

for _ in 0..<2500000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    let key = seed % 3000
    let val = seed % 1000000
    if (seed & 1) == 0 {
        let res = lru.put(key, val)
        checksum = (checksum * 33 + res) % 1000000007
    } else {
        let res = lru.get(key)
        checksum = (checksum * 33 + res) % 1000000007
    }
}

print(checksum)
