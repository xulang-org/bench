import Foundation

let base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP"
var payload = [UInt8]()
let baseBytes = Array(base.utf8)
for _ in 0..<6 {
    payload.append(contentsOf: baseBytes)
}
let data = Data(payload)

var total: Int64 = 0

for i in 0..<15000 {
    let enc = data.base64EncodedString()
    let encLen = Int64(enc.utf8.count)
    if let dec = Data(base64Encoded: enc) {
        let decLen = Int64(dec.count)
        total += encLen + decLen
        if i == 0 {
            total += Int64(dec.first!) + Int64(dec.last!)
        }
    }
}

print(total)
