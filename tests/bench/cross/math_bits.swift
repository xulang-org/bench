var x: UInt64 = 0x123456789abcdef0
var sum: UInt64 = 0
for i: UInt64 in 0..<5000000 {
    let shifted = (x ^ i)
    x = (shifted << 13) | (shifted >> (64 - 13))
    let lz = UInt64(x.leadingZeroBitCount)
    sum = sum &+ (64 - lz)
    sum = sum &+ lz
    sum = sum &+ UInt64(x.trailingZeroBitCount)
    sum = sum &+ UInt64(x.nonzeroBitCount)
    x = x.byteSwapped
    var v = x
    v = ((v >> 1) & 0x5555555555555555) | ((v & 0x5555555555555555) << 1)
    v = ((v >> 2) & 0x3333333333333333) | ((v & 0x3333333333333333) << 2)
    v = ((v >> 4) & 0x0F0F0F0F0F0F0F0F) | ((v & 0x0F0F0F0F0F0F0F0F) << 4)
    v = ((v >> 8) & 0x00FF00FF00FF00FF) | ((v & 0x00FF00FF00FF00FF) << 8)
    v = ((v >> 16) & 0x0000FFFF0000FFFF) | ((v & 0x0000FFFF0000FFFF) << 16)
    v = (v >> 32) | (v << 32)
    sum ^= v
}
print(Int64(bitPattern: sum))
