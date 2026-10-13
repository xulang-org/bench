import Foundation
var pool: [String] = []
var si: Int64 = 0
while si < 32 {
    let n = 8 + si % 24; var src: [UInt8] = []; var j: Int64 = 0
    while j < n { src.append(UInt8(97 + (j + si) % 3)); j += 1 }
    pool.append(String(decoding: src, as: UTF8.self)); si += 1
}
var state: Int64 = 1
var total: Int64 = 0
var i: Int64 = 0
while i < 1000000 {
    state = (state * 1103515245 + 12345) & 2147483647
    let idx = Int((state >> 16) & 31); let needle = UInt8(97 + ((state >> 8) & 1))
    var count: Int64 = 0
    for byte in pool[idx].utf8 { if byte == needle { count += 1 } }
    total += count; i += 1
}
print(total)
