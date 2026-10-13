func main() {
    let n = 100000
    var data = [Int64]()
    data.reserveCapacity(n)
    var seed: Int64 = 123456789
    var i = 0
    while i < n {
        seed = (seed &* 1103515245 &+ 12345) & 2147483647
        data.append(seed & 255)
        i += 1
    }
    let poly: Int64 = 3988292384
    let mask32: Int64 = 4294967295
    var total: Int64 = 0
    var round = 0
    while round < 20 {
        var crc: Int64 = mask32
        var k = 0
        while k < n {
            let b = data[k]
            crc = crc ^ b
            var bit = 0
            while bit < 8 {
                if (crc & 1) != 0 {
                    crc = ((crc >> 1) & 2147483647) ^ poly
                } else {
                    crc = (crc >> 1) & 2147483647
                }
                bit += 1
            }
            k += 1
        }
        total += crc ^ mask32
        round += 1
    }
    print(total)
}
main()
