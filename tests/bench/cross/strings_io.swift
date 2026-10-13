import Foundation

let seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu"
let base = String(repeating: seed, count: 384)
var total: Int64 = 0
var i = 0
while i < 2500 {
    let s = base.replacingOccurrences(of: "a", with: "A")
    total += Int64(s.utf8.count)
    let parts = s.components(separatedBy: ";")
    total += Int64(parts.count)
    var j = 0
    while j < parts.count {
        let p = parts[j]
        total += Int64(p.utf8.count)
        if p.hasPrefix("A") {
            total += 1
        }
        total += Int64(p.filter { $0 == "a" }.count)
        j += 1
    }
    let line = parts.joined(separator: "|")
    total += Int64(line.utf8.count)

    let trimmed = line.trimmingCharacters(in: .whitespaces)
    let tcount = trimmed.utf8.count
    let read_n = min(tcount, 256)
    total += Int64(read_n)
    let rem = tcount - read_n
    if rem > 0 {
        total += Int64(rem)
    }
    i += 1
}
print(total)
