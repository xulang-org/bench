let modV = 1000000007

func pushStr(_ buf: inout [Int], _ s: String) {
    for b in s.utf8 {
        buf.append(Int(b))
    }
}

func pushInt(_ buf: inout [Int], _ v: Int) {
    var x = v
    if x < 0 {
        buf.append(45)
        x = -x
    }
    if x == 0 {
        buf.append(48)
        return
    }
    var digs = [Int](repeating: 0, count: 24)
    var dc = 0
    while x > 0 {
        digs[dc] = 48 + (x % 10)
        dc += 1
        x /= 10
    }
    var i = dc - 1
    while i >= 0 {
        buf.append(digs[i])
        i -= 1
    }
}

func hexVal(_ b: Int) -> Int {
    if b >= 48 && b <= 57 { return b - 48 }
    if b >= 65 && b <= 70 { return b - 55 }
    if b >= 97 && b <= 102 { return b - 87 }
    return -1
}

func decodePctHash(_ buf: [Int], _ start: Int, _ end: Int) -> Int {
    var h = 0
    var i = start
    while i < end {
        let b = buf[i]
        var ch = b
        if b == 43 {
            ch = 32
            i += 1
        } else if b == 37 && i + 2 < end {
            let hi = hexVal(buf[i + 1])
            let lo = hexVal(buf[i + 2])
            if hi >= 0 && lo >= 0 {
                ch = (hi << 4) | lo
                i += 3
            } else {
                i += 1
            }
        } else {
            i += 1
        }
        h = (h * 131 + ch) % modV
    }
    return h
}

final class TrieRouter {
    var nodeEdgeHead: [Int] = []
    var nodeParam: [Int] = []
    var nodeWild: [Int] = []
    var nodeRoutes: [Int] = []
    var edgeOff: [Int] = []
    var edgeLen: [Int] = []
    var edgeChild: [Int] = []
    var edgeNext: [Int] = []
    var segPool: [Int] = []

    init() {
        _ = newNode()
    }

    func newNode() -> Int {
        let idx = nodeEdgeHead.count
        nodeEdgeHead.append(-1)
        nodeParam.append(-1)
        nodeWild.append(-1)
        for _ in 0..<5 {
            nodeRoutes.append(0)
        }
        return idx
    }

    func eqSlice(_ off: Int, _ ln: Int, _ segBytes: [Int]) -> Bool {
        if ln != segBytes.count { return false }
        for i in 0..<ln {
            if segPool[off + i] != segBytes[i] { return false }
        }
        return true
    }

    func eqBuf(_ buf: [Int], _ s: Int, _ ln: Int, _ off: Int, _ plen: Int) -> Bool {
        if ln != plen { return false }
        for i in 0..<ln {
            if buf[s + i] != segPool[off + i] { return false }
        }
        return true
    }

    func addRoute(_ method: Int, _ pat: [String], _ rid: Int) {
        var cur = 0
        for seg in pat {
            if seg == "*" {
                if nodeWild[cur] < 0 {
                    nodeWild[cur] = newNode()
                }
                cur = nodeWild[cur]
            } else if seg.hasPrefix(":") {
                if nodeParam[cur] < 0 {
                    nodeParam[cur] = newNode()
                }
                cur = nodeParam[cur]
            } else {
                let sb = seg.utf8.map { Int($0) }
                var e = nodeEdgeHead[cur]
                var found = -1
                while e >= 0 {
                    if eqSlice(edgeOff[e], edgeLen[e], sb) {
                        found = e
                        break
                    }
                    e = edgeNext[e]
                }
                if found >= 0 {
                    cur = edgeChild[found]
                } else {
                    let nn = newNode()
                    let off = segPool.count
                    segPool.append(contentsOf: sb)
                    let ei = edgeOff.count
                    edgeOff.append(off)
                    edgeLen.append(sb.count)
                    edgeChild.append(nn)
                    edgeNext.append(nodeEdgeHead[cur])
                    nodeEdgeHead[cur] = ei
                    cur = nn
                }
            }
        }
        nodeRoutes[cur * 5 + method] = rid
    }
}

func matchLowerKey(_ buf: [Int], _ s: Int, _ e: Int, _ target: [Int]) -> Bool {
    if e - s != target.count { return false }
    for i in 0..<target.count {
        var c = buf[s + i]
        if c >= 65 && c <= 90 { c += 32 }
        if c != target[i] { return false }
    }
    return true
}

func mainFunc() {
    let rt = TrieRouter()
    rt.addRoute(1, ["health"], 1)
    rt.addRoute(1, ["metrics"], 2)
    rt.addRoute(1, ["api", "v1", "users", ":id"], 3)
    rt.addRoute(2, ["api", "v1", "users"], 4)
    rt.addRoute(1, ["api", "v1", "users", ":id", "posts", ":pid"], 5)
    rt.addRoute(4, ["api", "v1", "users", ":id", "posts", ":pid"], 6)
    rt.addRoute(1, ["api", "v1", "orders", ":oid", "items"], 7)
    rt.addRoute(3, ["api", "v1", "orders", ":oid", "status"], 8)
    rt.addRoute(1, ["api", "v1", "orgs", ":org", "repos", ":repo", "issues", ":num"], 9)
    rt.addRoute(2, ["api", "v1", "orgs", ":org", "repos", ":repo", "issues"], 10)
    rt.addRoute(1, ["api", "v2", "search"], 11)
    rt.addRoute(1, ["static", "*"], 12)

    let users = ["alice", "bob42", "charlie", "dana_9", "eve", "frank01", "grace", "heidi"]
    let orgs = ["xulang", "acme", "nebula", "kernel"]
    let repos = ["xu", "bench", "runtime", "stdlib", "docs"]
    let queries = [
        "page=2&limit=50&q=hello+world%21",
        "sort=desc&filter=open%2Factive&tag=v1%2E0",
        "q=%41%42%43+test%20case&offset=100",
        "",
        "lang=zh%2DCN&mode=fast&debug=1",
        "path=%2Fusr%2Fbin&retry=3",
    ]
    let clKey = "content-length".utf8.map { Int($0) }
    let ridKey = "x-request-id".utf8.map { Int($0) }

    var reqBuf: [Int] = []
    reqBuf.reserveCapacity(65536)
    var reqOff: [Int] = []
    var reqLen: [Int] = []
    var rng = 246813579
    for i in 0..<240 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let k = rng % 14
        rng = (rng * 1103515245 + 12345) & 2147483647
        let u = users[rng % 8]
        rng = (rng * 1103515245 + 12345) & 2147483647
        let pid = 100 + (rng % 900)
        rng = (rng * 1103515245 + 12345) & 2147483647
        let oid = 10000 + (rng % 90000)
        rng = (rng * 1103515245 + 12345) & 2147483647
        let org = orgs[rng % 4]
        rng = (rng * 1103515245 + 12345) & 2147483647
        let repo = repos[rng % 5]
        rng = (rng * 1103515245 + 12345) & 2147483647
        let num = 1 + (rng % 500)
        rng = (rng * 1103515245 + 12345) & 2147483647
        let q = queries[rng % 6]
        rng = (rng * 1103515245 + 12345) & 2147483647
        let cl = rng % 4096

        let off = reqBuf.count
        reqOff.append(off)
        switch k {
        case 0: pushStr(&reqBuf, "GET /health")
        case 1: pushStr(&reqBuf, "GET /metrics")
        case 2: pushStr(&reqBuf, "GET /api/v1/users/"); pushStr(&reqBuf, u)
        case 3: pushStr(&reqBuf, "POST /api/v1/users")
        case 4: pushStr(&reqBuf, "GET /api/v1/users/"); pushStr(&reqBuf, u); pushStr(&reqBuf, "/posts/"); pushInt(&reqBuf, pid)
        case 5: pushStr(&reqBuf, "DELETE /api/v1/users/"); pushStr(&reqBuf, u); pushStr(&reqBuf, "/posts/"); pushInt(&reqBuf, pid)
        case 6: pushStr(&reqBuf, "GET /api/v1/orders/"); pushInt(&reqBuf, oid); pushStr(&reqBuf, "/items")
        case 7: pushStr(&reqBuf, "PUT /api/v1/orders/"); pushInt(&reqBuf, oid); pushStr(&reqBuf, "/status")
        case 8: pushStr(&reqBuf, "GET /api/v1/orgs/"); pushStr(&reqBuf, org); pushStr(&reqBuf, "/repos/"); pushStr(&reqBuf, repo); pushStr(&reqBuf, "/issues/"); pushInt(&reqBuf, num)
        case 9: pushStr(&reqBuf, "POST /api/v1/orgs/"); pushStr(&reqBuf, org); pushStr(&reqBuf, "/repos/"); pushStr(&reqBuf, repo); pushStr(&reqBuf, "/issues")
        case 10: pushStr(&reqBuf, "GET /api/v2/search")
        case 11: pushStr(&reqBuf, "GET /static/js/"); pushStr(&reqBuf, repo); pushStr(&reqBuf, "/bundle_"); pushInt(&reqBuf, pid); pushStr(&reqBuf, ".js")
        case 12: pushStr(&reqBuf, "GET /api/v1/unknown/"); pushStr(&reqBuf, u); pushStr(&reqBuf, "/nope")
        default: pushStr(&reqBuf, "POST /health")
        }
        if !q.isEmpty {
            reqBuf.append(63)
            pushStr(&reqBuf, q)
        }
        pushStr(&reqBuf, " HTTP/1.1\r\n")
        if (i % 3) != 0 {
            pushStr(&reqBuf, "Host: api.xulang.org\r\n")
        } else {
            pushStr(&reqBuf, "HOST: api.xulang.org\r\n")
        }
        pushStr(&reqBuf, "User-Agent: xu-bench/1.0\r\n")
        if (i & 1) == 0 {
            pushStr(&reqBuf, "Content-Length: ")
        } else {
            pushStr(&reqBuf, "content-length: ")
        }
        pushInt(&reqBuf, cl)
        pushStr(&reqBuf, "\r\nX-Request-Id: req-")
        pushInt(&reqBuf, i)
        reqBuf.append(45)
        pushInt(&reqBuf, num)
        pushStr(&reqBuf, "\r\n\r\n")
        reqLen.append(reqBuf.count - off)
    }

    var segStarts = [Int](repeating: 0, count: 16)
    var segEnds = [Int](repeating: 0, count: 16)
    var matched = 0
    var ck = 0
    for _ in 0..<500 {
        for ri in 0..<240 {
            let rStart = reqOff[ri]
            let rEnd = rStart + reqLen[ri]
            var sp1 = rStart
            while reqBuf[sp1] != 32 { sp1 += 1 }
            let mlen = sp1 - rStart
            var mc = 0
            if mlen == 3 && reqBuf[rStart] == 71 { mc = 1 }
            else if mlen == 4 && reqBuf[rStart] == 80 { mc = 2 }
            else if mlen == 3 && reqBuf[rStart] == 80 { mc = 3 }
            else if mlen == 6 && reqBuf[rStart] == 68 { mc = 4 }

            let tStart = sp1 + 1
            var sp2 = tStart
            while reqBuf[sp2] != 32 { sp2 += 1 }
            var crlf = sp2 + 1
            while !(reqBuf[crlf] == 13 && reqBuf[crlf + 1] == 10) { crlf += 1 }
            var qpos = -1
            for p in tStart..<sp2 {
                if reqBuf[p] == 63 { qpos = p; break }
            }
            let pathEnd = qpos >= 0 ? qpos : sp2
            var nSegs = 0
            var sp = tStart
            while sp < pathEnd {
                while sp < pathEnd && reqBuf[sp] == 47 { sp += 1 }
                if sp >= pathEnd { break }
                var se = sp
                while se < pathEnd && reqBuf[se] != 47 { se += 1 }
                segStarts[nSegs] = sp
                segEnds[nSegs] = se
                nSegs += 1
                sp = se
            }

            var pos = crlf + 2
            var hdrCnt = 0
            var contentLen = 0
            var reqIdHash = 0
            while pos < rEnd {
                var lend = pos
                while lend + 1 < rEnd && !(reqBuf[lend] == 13 && reqBuf[lend + 1] == 10) { lend += 1 }
                if lend == pos { break }
                var col = pos
                while col < lend && reqBuf[col] != 58 { col += 1 }
                var vs = col + 1
                while vs < lend && (reqBuf[vs] == 32 || reqBuf[vs] == 9) { vs += 1 }
                var ve = lend
                while ve > vs && (reqBuf[ve - 1] == 32 || reqBuf[ve - 1] == 9) { ve -= 1 }
                hdrCnt += 1
                if matchLowerKey(reqBuf, pos, col, clKey) {
                    var v = 0
                    for vp in vs..<ve { v = v * 10 + (reqBuf[vp] - 48) }
                    contentLen = v
                } else if matchLowerKey(reqBuf, pos, col, ridKey) {
                    for vp in vs..<ve { reqIdHash = (reqIdHash * 31 + reqBuf[vp]) % modV }
                }
                pos = lend + 2
            }

            var cur = 0
            var ph = 0
            var sj = 0
            var dead = false
            while sj < nSegs {
                let ss = segStarts[sj]
                let sln = segEnds[sj] - ss
                var e = rt.nodeEdgeHead[cur]
                var nxt = -1
                while e >= 0 {
                    if rt.eqBuf(reqBuf, ss, sln, rt.edgeOff[e], rt.edgeLen[e]) {
                        nxt = rt.edgeChild[e]
                        break
                    }
                    e = rt.edgeNext[e]
                }
                if nxt >= 0 {
                    cur = nxt
                    sj += 1
                } else if rt.nodeParam[cur] >= 0 {
                    for cp in ss..<(ss + sln) { ph = (ph * 131 + reqBuf[cp]) % modV }
                    cur = rt.nodeParam[cur]
                    sj += 1
                } else if rt.nodeWild[cur] >= 0 {
                    while sj < nSegs {
                        for cp in segStarts[sj]..<segEnds[sj] { ph = (ph * 131 + reqBuf[cp]) % modV }
                        sj += 1
                    }
                    cur = rt.nodeWild[cur]
                    break
                } else {
                    dead = true
                    break
                }
            }
            var routeId = 0
            var paramHash = 0
            if !dead {
                let rid = rt.nodeRoutes[cur * 5 + mc]
                if rid > 0 {
                    routeId = rid
                    paramHash = ph
                }
            }
            var qHash = 0
            if qpos >= 0 && qpos + 1 < sp2 {
                var qp = qpos + 1
                while qp < sp2 {
                    var qe = qp
                    while qe < sp2 && reqBuf[qe] != 38 { qe += 1 }
                    var eq = -1
                    for qt in qp..<qe {
                        if reqBuf[qt] == 61 { eq = qt; break }
                    }
                    if eq >= 0 {
                        let kh = decodePctHash(reqBuf, qp, eq)
                        let vh = decodePctHash(reqBuf, eq + 1, qe)
                        qHash = (qHash * 257 + kh * 17 + vh) % modV
                    } else {
                        qHash = (qHash * 257 + decodePctHash(reqBuf, qp, qe)) % modV
                    }
                    qp = qe + 1
                }
            }
            if routeId > 0 { matched += 1 }
            let row = (routeId * 1000003 + mc * 97 + paramHash * 7 + qHash * 13 + contentLen * 3 + hdrCnt * 19 + reqIdHash) % modV
            ck = (ck * 31 + row) % modV
        }
    }
    print(matched)
    print(ck)
}

mainFunc()
