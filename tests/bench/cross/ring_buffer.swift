import Foundation

struct Deque {
    var buf: [Int64]
    var head: Int
    var tail: Int
    var count: Int
    var mask: Int

    init() {
        self.buf = [Int64](repeating: 0, count: 16)
        self.head = 0
        self.tail = 0
        self.count = 0
        self.mask = 15
    }

    mutating func grow() {
        let oldCap = mask + 1
        let oldMask = mask
        let newCap = oldCap * 2
        var newBuf = [Int64](repeating: 0, count: newCap)
        for j in 0..<count {
            newBuf[j] = buf[(head + j) & oldMask]
        }
        self.buf = newBuf
        self.head = 0
        self.tail = self.count
        self.mask = newCap - 1
    }

    mutating func pushBack(_ val: Int64) {
        if count == mask + 1 {
            grow()
        }
        buf[tail] = val
        tail = (tail + 1) & mask
        count += 1
    }

    mutating func pushFront(_ val: Int64) {
        if count == mask + 1 {
            grow()
        }
        head = (head - 1) & mask
        buf[head] = val
        count += 1
    }

    mutating func popFront() -> Int64 {
        if count == 0 {
            return 0
        }
        let val = buf[head]
        head = (head + 1) & mask
        count -= 1
        return val
    }

    mutating func popBack() -> Int64 {
        if count == 0 {
            return 0
        }
        tail = (tail - 1) & mask
        let val = buf[tail]
        count -= 1
        return val
    }
}

var q = Deque()
var seed: Int64 = 123456789
var checksum: Int64 = 0

for _ in 0..<5000000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    let op = seed % 4
    if op == 0 {
        q.pushBack(seed)
    } else if op == 1 {
        q.pushFront(seed)
    } else if op == 2 {
        let v = q.popFront()
        checksum = (checksum * 33 + v) % 1000000007
    } else {
        let v = q.popBack()
        checksum = (checksum * 33 + v) % 1000000007
    }
}

while q.count > 0 {
    let v = q.popFront()
    checksum = (checksum * 33 + v) % 1000000007
}

print(checksum)
