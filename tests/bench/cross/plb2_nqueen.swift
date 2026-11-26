func nqSolve(_ n: Int) -> Int64 {
    var l = [Int64](repeating: 0, count: 32)
    var c = [Int64](repeating: 0, count: 32)
    var r = [Int64](repeating: 0, count: 32)
    var m = [Int64](repeating: 0, count: 32)
    let y0: Int64 = (1 << n) - 1
    var k = 0
    m[0] = y0
    var cnt: Int64 = 0
    while k >= 0 {
        let y = m[k]
        if y == 0 {
            k -= 1
        } else {
            let z = y & (0 &- y)
            m[k] = y - z
            if k == n - 1 {
                cnt += 1
            } else {
                let nk = k + 1
                l[nk] = ((l[k] | z) << 1) & y0
                c[nk] = c[k] | z
                r[nk] = (r[k] | z) >> 1
                m[nk] = y0 ^ (l[nk] | c[nk] | r[nk])
                k = nk
            }
        }
    }
    return cnt
}

func main() {
    print(nqSolve(15))
}

main()
