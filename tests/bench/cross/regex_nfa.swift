final class NfaPool {
    var stKind: [Int] = []
    var stOut1: [Int] = []
    var stOut2: [Int] = []
    var pSt: [Int] = []
    var pWh: [Int] = []
    var pNext: [Int] = []
    var startSt: [Int] = []
    var matchSt: [Int] = []

    func prec(_ op: Int) -> Int {
        if op == -3 { return 1 }
        if op == -2 { return 2 }
        if op == -4 || op == -5 || op == -6 { return 3 }
        return 0
    }

    func addSt(_ k: Int, _ o1: Int, _ o2: Int) -> Int {
        let idx = stKind.count
        stKind.append(k)
        stOut1.append(o1)
        stOut2.append(o2)
        return idx
    }

    func newPatch(_ si: Int, _ wh: Int) -> Int {
        let idx = pSt.count
        pSt.append(si)
        pWh.append(wh)
        pNext.append(-1)
        return idx
    }

    func appendPatch(_ h1: Int, _ t1: Int, _ h2: Int) -> Int {
        if h1 == -1 { return h2 }
        if h2 == -1 { return h1 }
        pNext[t1] = h2
        return h1
    }

    func applyPatch(_ head: Int, _ target: Int) {
        var cur = head
        while cur != -1 {
            if pWh[cur] == 1 {
                stOut1[pSt[cur]] = target
            } else {
                stOut2[pSt[cur]] = target
            }
            cur = pNext[cur]
        }
    }

    func compilePattern(_ pat: String) {
        var toks: [Int] = []
        var prevAtom = false
        for b in pat.utf8 {
            let c = Int(b)
            if c == 40 {
                if prevAtom { toks.append(-2) }
                toks.append(-10)
                prevAtom = false
            } else if c == 41 {
                toks.append(-11)
                prevAtom = true
            } else if c == 124 {
                toks.append(-3)
                prevAtom = false
            } else if c == 42 {
                toks.append(-4)
                prevAtom = true
            } else if c == 43 {
                toks.append(-5)
                prevAtom = true
            } else if c == 63 {
                toks.append(-6)
                prevAtom = true
            } else {
                if prevAtom { toks.append(-2) }
                toks.append(c == 46 ? -1 : c)
                prevAtom = true
            }
        }

        var post: [Int] = []
        var ops: [Int] = []
        for t in toks {
            if t >= 0 || t == -1 {
                post.append(t)
            } else if t == -10 {
                ops.append(t)
            } else if t == -11 {
                while !ops.isEmpty && ops[ops.count - 1] != -10 {
                    post.append(ops.removeLast())
                }
                if !ops.isEmpty { ops.removeLast() }
            } else {
                let pt = prec(t)
                while !ops.isEmpty && ops[ops.count - 1] != -10 && prec(ops[ops.count - 1]) >= pt {
                    post.append(ops.removeLast())
                }
                ops.append(t)
            }
        }
        while !ops.isEmpty {
            post.append(ops.removeLast())
        }

        var fs: [Int] = []
        var fh: [Int] = []
        var ft: [Int] = []
        for t in post {
            if t >= 0 || t == -1 {
                let s = addSt(t, -1, -1)
                let p = newPatch(s, 1)
                fs.append(s)
                fh.append(p)
                ft.append(p)
            } else if t == -2 {
                let s2 = fs.removeLast()
                let h2 = fh.removeLast()
                let t2 = ft.removeLast()
                let s1 = fs.removeLast()
                let h1 = fh.removeLast()
                ft.removeLast()
                applyPatch(h1, s2)
                fs.append(s1)
                fh.append(h2)
                ft.append(t2)
            } else if t == -3 {
                let s2 = fs.removeLast()
                let h2 = fh.removeLast()
                let t2 = ft.removeLast()
                let s1 = fs.removeLast()
                let h1 = fh.removeLast()
                let t1 = ft.removeLast()
                let s = addSt(-2, s1, s2)
                let hn = appendPatch(h1, t1, h2)
                fs.append(s)
                fh.append(hn)
                ft.append(t2)
            } else if t == -6 {
                let s1 = fs.removeLast()
                let h1 = fh.removeLast()
                let t1 = ft.removeLast()
                let s = addSt(-2, s1, -1)
                let p = newPatch(s, 2)
                let hn = appendPatch(h1, t1, p)
                fs.append(s)
                fh.append(hn)
                ft.append(p)
            } else if t == -4 {
                let s1 = fs.removeLast()
                let h1 = fh.removeLast()
                ft.removeLast()
                let s = addSt(-2, s1, -1)
                applyPatch(h1, s)
                let p = newPatch(s, 2)
                fs.append(s)
                fh.append(p)
                ft.append(p)
            } else if t == -5 {
                let s1 = fs.removeLast()
                let h1 = fh.removeLast()
                ft.removeLast()
                let s = addSt(-2, s1, -1)
                applyPatch(h1, s)
                let p = newPatch(s, 2)
                fs.append(s1)
                fh.append(p)
                ft.append(p)
            }
        }
        let m = addSt(-3, -1, -1)
        applyPatch(fh.removeLast(), m)
        startSt.append(fs.removeLast())
        matchSt.append(m)
    }
}

func addState(
    _ nfa: NfaPool,
    _ vis: inout [Int],
    _ lst: inout [Int],
    _ lstLen: inout Int,
    _ stk: inout [Int],
    _ s: Int,
    _ gen: Int
) {
    var sp = 0
    stk[sp] = s
    sp += 1
    while sp > 0 {
        sp -= 1
        let u = stk[sp]
        if u < 0 || vis[u] == gen {
            continue
        }
        vis[u] = gen
        if nfa.stKind[u] == -2 {
            stk[sp] = nfa.stOut2[u]
            sp += 1
            stk[sp] = nfa.stOut1[u]
            sp += 1
        } else {
            lst[lstLen] = u
            lstLen += 1
        }
    }
}

func nfaSearch(
    _ nfa: NfaPool,
    _ start: Int,
    _ matchSt: Int,
    _ text: [Int],
    _ tlen: Int,
    _ vis: inout [Int],
    _ genBox: inout Int,
    _ cur: inout [Int],
    _ nxt: inout [Int],
    _ stk: inout [Int]
) -> Bool {
    var gen = genBox + 1
    var curLen = 0
    addState(nfa, &vis, &cur, &curLen, &stk, start, gen)
    if vis[matchSt] == gen {
        genBox = gen
        return true
    }
    for i in 0..<tlen {
        let c = text[i]
        gen += 1
        var nxtLen = 0
        for j in 0..<curLen {
            let u = cur[j]
            let k = nfa.stKind[u]
            if k == c || k == -1 {
                addState(nfa, &vis, &nxt, &nxtLen, &stk, nfa.stOut1[u], gen)
            }
        }
        addState(nfa, &vis, &nxt, &nxtLen, &stk, start, gen)
        if vis[matchSt] == gen {
            genBox = gen
            return true
        }
        for k in 0..<nxtLen {
            cur[k] = nxt[k]
        }
        curLen = nxtLen
    }
    genBox = gen
    return false
}

func main() {
    let nfa = NfaPool()
    let patterns = ["ab+c", "(a|ab)*cd", "x..y*z", "(foo|bar)+baz", "a(b|c)+d?", "k(m|n)*p+q"]
    for p in patterns {
        nfa.compilePattern(p)
    }
    let tokens = [
        "ab", "bc", "cd", "foo", "bar", "baz", "xyz", "x12y", "yz", "kmpq",
        "knppq", "abc", "abbc", "abd", "acd", "a", "b", "c", "d", "x",
        "y", "z", "k", "m", "n", "p", "q", "0", "_", "-"
    ]
    let tokBytes = tokens.map { Array($0.utf8).map { Int($0) } }

    let nSt = nfa.stKind.count
    var vis = [Int](repeating: 0, count: nSt)
    var cur = [Int](repeating: 0, count: nSt)
    var nxt = [Int](repeating: 0, count: nSt)
    var stk = [Int](repeating: 0, count: nSt * 2)
    var genBox = 0
    var line = [Int](repeating: 0, count: 256)

    var rng = 2463534242
    var matches = 0
    var weighted = 0
    for li in 0..<6000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let nTok = 8 + (rng % 10)
        var tlen = 0
        for _ in 0..<nTok {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let tb = tokBytes[rng % 30]
            for b in tb {
                line[tlen] = b
                tlen += 1
            }
        }
        for pi in 0..<6 {
            if nfaSearch(nfa, nfa.startSt[pi], nfa.matchSt[pi], line, tlen, &vis, &genBox, &cur, &nxt, &stk) {
                matches += 1
                weighted = (weighted + (li + 1) * (pi + 1)) % 1000000007
            }
        }
    }
    print(matches)
    print(weighted)
}

main()
