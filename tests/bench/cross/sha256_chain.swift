import CryptoKit
import Foundation

func sha256Hex(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

var body = Data()
var i: Int64 = 0
let chunk = Data("The quick brown fox jumps over the lazy dog. 0123456789.".utf8)
while i < 1024 {
    body.append(chunk)
    i += 1
}
var h = sha256Hex(body)
var r: Int64 = 0
while r < 4 {
    var cat = Data(h.utf8)
    cat.append(body)
    h = sha256Hex(cat)
    r += 1
}
print(h)
