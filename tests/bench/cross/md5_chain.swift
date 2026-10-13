import Foundation
import CryptoKit

var h = "The quick brown fox jumps over the lazy dog"
for _ in 0..<100000 {
    let digest = Insecure.MD5.hash(data: Data(h.utf8))
    h = digest.map { String(format: "%02x", $0) }.joined()
}
print(h)
