@inline(__always)
func lcg(_ seed: Int64) -> Int64 {
    return (seed &* 1103515245 &+ 12345) & 2147483647
}

func main() {
    let n = 200000
    let q = 200000
    var st = [Int64]()
    var en = [Int64]()
    st.reserveCapacity(n)
    en.reserveCapacity(n)
    var maxEn = [Int64](repeating: 0, count: n)

    var seed: Int64 = 123456789
    var curSt: Int64 = 0
    for _ in 0..<n {
        seed = lcg(seed)
        curSt += seed % 100
        seed = lcg(seed)
        let ln = 1 + (seed % 5000)
        st.append(curSt)
        en.append(curSt + ln)
    }
    let maxCoord = curSt + 1

    var qst = [Int64]()
    var qen = [Int64]()
    qst.reserveCapacity(q)
    qen.reserveCapacity(q)
    for _ in 0..<q {
        seed = lcg(seed)
        let qs = seed % maxCoord
        seed = lcg(seed)
        let ln = 1 + (seed % 5000)
        qst.append(qs)
        qen.append(qs + ln)
    }

    var i = 0
    while i < n {
        maxEn[i] = en[i]
        i += 2
    }
    var k = 1
    while (1 << k) <= n {
        let x = 1 << (k - 1)
        let i0 = (x << 1) - 1
        let step = x << 2
        var idx = i0
        while idx < n {
            let el = maxEn[idx - x]
            var er: Int64 = 0
            if idx + x < n {
                er = maxEn[idx + x]
            } else {
                er = en[idx]
                var lim = idx + (x << 1)
                if lim > n { lim = n }
                var j = idx + 1
                while j < lim {
                    if en[j] > er { er = en[j] }
                    j += 1
                }
            }
            var e = en[idx]
            if el > e { e = el }
            if er > e { e = er }
            maxEn[idx] = e
            idx += step
        }
        k += 1
    }
    let maxK = k - 1

    var sk = [Int](repeating: 0, count: 64)
    var sx = [Int](repeating: 0, count: 64)
    var sw = [Int](repeating: 0, count: 64)
    var hits: Int64 = 0
    var covSum: Int64 = 0
    let rootX = (1 << maxK) - 1

    for qi in 0..<q {
        let qs = qst[qi]
        let qe = qen[qi]
        sk[0] = maxK
        sx[0] = rootX
        sw[0] = 0
        var sp = 1
        while sp > 0 {
            sp -= 1
            let kk = sk[sp]
            let x = sx[sp]
            let w = sw[sp]
            if kk <= 3 {
                let i0 = (x >> kk) << kk
                var i1 = i0 + (1 << (kk + 1)) - 1
                if i1 >= n { i1 = n }
                var ii = i0
                while ii < i1 && st[ii] < qe {
                    if qs < en[ii] {
                        hits += 1
                        let os = qs > st[ii] ? qs : st[ii]
                        let oe = qe < en[ii] ? qe : en[ii]
                        covSum += oe - os
                    }
                    ii += 1
                }
            } else if w == 0 {
                let y = x - (1 << (kk - 1))
                sk[sp] = kk
                sx[sp] = x
                sw[sp] = 1
                sp += 1
                if y >= n || maxEn[y] > qs {
                    sk[sp] = kk - 1
                    sx[sp] = y
                    sw[sp] = 0
                    sp += 1
                }
            } else if x < n && st[x] < qe {
                if qs < en[x] {
                    hits += 1
                    let os = qs > st[x] ? qs : st[x]
                    let oe = qe < en[x] ? qe : en[x]
                    covSum += oe - os
                }
                sk[sp] = kk - 1
                sx[sp] = x + (1 << (kk - 1))
                sw[sp] = 0
                sp += 1
            }
        }
    }
    print(hits)
    print(covSum)
}

main()
