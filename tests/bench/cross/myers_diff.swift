let modV = 1000000007

func run() {
    let maxD = 120
    let stride = 241
    let off = 120

    var v = [Int](repeating: 0, count: stride)
    var trace = [Int](repeating: 0, count: (maxD + 1) * stride)
    var a = [Int](repeating: 0, count: 200)
    var b = [Int](repeating: 0, count: 300)
    var opType = [Int](repeating: 0, count: 600)
    var opVal = [Int](repeating: 0, count: 600)

    var rng = 20260501
    var totalEdits = 0
    var ck = 0

    for _ in 0..<1200 {
        let n = 200
        for i in 0..<n {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let val = rng & 63
            a[i] = val
            b[i] = val
        }
        var m = n
        rng = (rng * 1103515245 + 12345) & 2147483647
        let nmut = 18 + (rng % 11)
        for _ in 0..<nmut {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let kind = rng % 3
            if kind == 0 && m > 120 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let pos = rng % m
                var p = pos
                while p + 1 < m {
                    b[p] = b[p + 1]
                    p += 1
                }
                m -= 1
            } else if kind == 1 && m < 260 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let pos = rng % (m + 1)
                rng = (rng * 1103515245 + 12345) & 2147483647
                let nv = rng & 63
                var p = m
                while p > pos {
                    b[p] = b[p - 1]
                    p -= 1
                }
                b[pos] = nv
                m += 1
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let pos = rng % m
                rng = (rng * 1103515245 + 12345) & 2147483647
                b[pos] = rng & 63
            }
        }

        v[off + 1] = 0
        var foundD = -1
        for d in 0...maxD {
            let tbase = d * stride
            var k = -d
            while k <= d {
                var x = (k == -d || (k != d && v[off + k - 1] < v[off + k + 1]))
                    ? v[off + k + 1]
                    : v[off + k - 1] + 1
                var y = x - k
                while x < n && y < m && a[x] == b[y] {
                    x += 1
                    y += 1
                }
                v[off + k] = x
                trace[tbase + off + k] = x
                if x >= n && y >= m {
                    foundD = d
                    break
                }
                k += 2
            }
            if foundD >= 0 {
                break
            }
        }

        var x = n
        var y = m
        var oc = 0
        var bd = foundD
        while bd > 0 {
            let pbase = (bd - 1) * stride
            let k = x - y
            let prevK = (k == -bd || (k != bd && trace[pbase + off + k - 1] < trace[pbase + off + k + 1]))
                ? (k + 1)
                : (k - 1)
            let prevX = trace[pbase + off + prevK]
            let prevY = prevX - prevK
            while x > prevX && y > prevY {
                opType[oc] = 0
                opVal[oc] = a[x - 1]
                oc += 1
                x -= 1
                y -= 1
            }
            if x == prevX {
                opType[oc] = 1
                opVal[oc] = b[y - 1]
                oc += 1
                y -= 1
            } else {
                opType[oc] = 2
                opVal[oc] = a[x - 1]
                oc += 1
                x -= 1
            }
            bd -= 1
        }
        while x > 0 && y > 0 {
            opType[oc] = 0
            opVal[oc] = a[x - 1]
            oc += 1
            x -= 1
            y -= 1
        }

        totalEdits += foundD
        var sh = foundD
        for j in 0..<oc {
            sh = (sh * 131 + opType[j] * 67 + opVal[j]) % modV
        }
        ck = (ck * 31 + sh) % modV
    }

    print("\(totalEdits)\n\(ck)")
}

run()
