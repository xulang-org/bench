import Foundation

let n = 524_288
let rounds = 32
let url = URL(fileURLWithPath: "roundtrip.bin")
let payload = Data(repeating: 65, count: n)
var sum: Int64 = 0

for _ in 0..<rounds {
    do {
        try payload.write(to: url)
        let got = try Data(contentsOf: url)
        guard got == payload else { exit(1) }
        sum += Int64(got[0]) + Int64(got[n / 2]) + Int64(got[n - 1])
    } catch {
        exit(1)
    }
}
print(sum)
