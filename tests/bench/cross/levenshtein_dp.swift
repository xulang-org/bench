func main() {
    var a = [Int](repeating: 0, count: 256)
    var b = [Int](repeating: 0, count: 256)
    var dp = [Int](repeating: 0, count: 512)

    var rng = 987654321
    var sumLev = 0
    var ckLev = 0
    for _ in 0..<400 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let la = 120 + (rng % 100)
        rng = (rng * 1103515245 + 12345) & 2147483647
        let lb = 120 + (rng % 100)
        for i in 0..<la {
            rng = (rng * 1103515245 + 12345) & 2147483647
            a[i] = 97 + ((rng >> 16) & 7)
        }
        for i in 0..<lb {
            rng = (rng * 1103515245 + 12345) & 2147483647
            if i < la && (rng % 5) == 0 {
                b[i] = a[i]
            } else {
                b[i] = 97 + ((rng >> 16) & 7)
            }
        }

        for j in 0...lb {
            dp[j] = j
        }
        for i in 1...la {
            let curOff = (i & 1) * 256
            let prevOff = 256 - curOff
            dp[curOff] = i
            let ai = a[i - 1]
            for j in 1...lb {
                let cost = (ai == b[j - 1]) ? 0 : 1
                let d1 = dp[prevOff + j] + 1
                let d2 = dp[curOff + j - 1] + 1
                let d3 = dp[prevOff + j - 1] + cost
                var best = d1
                if d2 < best { best = d2 }
                if d3 < best { best = d3 }
                dp[curOff + j] = best
            }
        }
        let d = dp[(la & 1) * 256 + lb]
        sumLev += d
        ckLev = (ckLev * 1000003 + d) % 1000000007
    }
    print(sumLev)
    print(ckLev)
}

main()
