@inline(__always)
func rotl32(_ v: UInt32, _ c: UInt32) -> UInt32 {
    return (v << c) | (v >> (32 - c))
}

@inline(__always)
func qr(_ s: inout [UInt32], _ a: Int, _ b: Int, _ c: Int, _ d: Int) {
    s[a] = s[a] &+ s[b]
    s[d] = rotl32(s[d] ^ s[a], 16)
    s[c] = s[c] &+ s[d]
    s[b] = rotl32(s[b] ^ s[c], 12)
    s[a] = s[a] &+ s[b]
    s[d] = rotl32(s[d] ^ s[a], 8)
    s[c] = s[c] &+ s[d]
    s[b] = rotl32(s[b] ^ s[c], 7)
}

func main() {
    var key = [UInt32](repeating: 0, count: 8)
    for i in 0..<8 {
        key[i] = UInt32(i &* 16843009)
    }
    let nonce0: UInt32 = 305419896
    let nonce1: UInt32 = 2596069104
    let nonce2: UInt32 = 267246505

    let rounds = 30000
    var total_sum: UInt32 = 0
    var s = [UInt32](repeating: 0, count: 16)

    for block in 0..<rounds {
        s[0] = 1634760805
        s[1] = 857760878
        s[2] = 2036477234
        s[3] = 1797285236
        for k in 0..<8 {
            s[4 + k] = key[k] &+ UInt32(block)
        }
        s[12] = UInt32(block)
        s[13] = nonce0
        s[14] = nonce1
        s[15] = nonce2

        for _ in 0..<10 {
            qr(&s, 0, 4, 8, 12)
            qr(&s, 1, 5, 9, 13)
            qr(&s, 2, 6, 10, 14)
            qr(&s, 3, 7, 11, 15)
            qr(&s, 0, 5, 10, 15)
            qr(&s, 1, 6, 11, 12)
            qr(&s, 2, 7, 8, 13)
            qr(&s, 3, 4, 9, 14)
        }
        total_sum = total_sum &+ s[0] &+ s[5] &+ s[10] &+ s[15]
    }
    print(total_sum)
}

main()
