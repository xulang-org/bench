import Foundation

let hexDigits = Array("0123456789abcdef".utf8)

func hexVal(_ c: UInt8) -> Int {
    if c >= 48 && c <= 57 {
        return Int(c - 48)
    } else if c >= 97 && c <= 102 {
        return Int(c - 97 + 10)
    } else if c >= 65 && c <= 70 {
        return Int(c - 65 + 10)
    }
    return -1
}

let base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP"
var payload = [UInt8]()
let baseBytes = Array(base.utf8)
for _ in 0..<8 {
    payload.append(contentsOf: baseBytes)
}
let n = payload.count
var total: Int64 = 0

var enc = [UInt8](repeating: 0, count: n * 2)
var dec = [UInt8](repeating: 0, count: n)

for i in 0..<25000 {
    for j in 0..<n {
        let c = payload[j]
        enc[2 * j] = hexDigits[Int(c >> 4)]
        enc[2 * j + 1] = hexDigits[Int(c & 0x0f)]
    }
    let encLen = Int64(enc.count)

    for j in 0..<n {
        let hi = hexVal(enc[2 * j])
        let lo = hexVal(enc[2 * j + 1])
        dec[j] = UInt8((hi << 4) | lo)
    }
    let decLen = Int64(dec.count)

    total += encLen + decLen
    if i == 0 {
        total += Int64(dec[0]) + Int64(dec[dec.count - 1])
    }
}

print(total)
