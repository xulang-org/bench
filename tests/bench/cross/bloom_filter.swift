import Foundation

struct BloomFilter {
    var bits: [UInt64]
    var mask: UInt64

    init(numBits: Int) {
        self.bits = [UInt64](repeating: 0, count: numBits / 64)
        self.mask = UInt64(numBits - 1)
    }

    mutating func add(_ val: Int64) {
        let h1 = (val * 1103515245 + 12345) & 2147483647
        let h2 = (val * 1664525 + 1013904223) & 2147483647
        for i: Int64 in 0..<4 {
            let bit = UInt64(h1 + i * h2) & mask
            bits[Int(bit >> 6)] |= (1 << (bit & 63))
        }
    }

    func contains(_ val: Int64) -> Bool {
        let h1 = (val * 1103515245 + 12345) & 2147483647
        let h2 = (val * 1664525 + 1013904223) & 2147483647
        for i: Int64 in 0..<4 {
            let bit = UInt64(h1 + i * h2) & mask
            if (bits[Int(bit >> 6)] & (1 << (bit & 63))) == 0 {
                return false
            }
        }
        return true
    }
}

var bf = BloomFilter(numBits: 1048576)
var seed: Int64 = 123456789

for _ in 0..<200000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    bf.add(seed)
}

var checksum: Int64 = 0
for _ in 0..<2000000 {
    seed = (seed * 1664525 + 1013904223) % 2147483647
    if bf.contains(seed) {
        checksum = (checksum * 31 + seed) % 1000000007
    }
}

print(checksum)
