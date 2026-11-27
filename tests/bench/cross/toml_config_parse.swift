let modV = 1000000007

func pushStr(_ buf: inout [Int], _ s: String) {
    for b in s.utf8 {
        buf.append(Int(b))
    }
}

func pushInt(_ buf: inout [Int], _ v: Int) {
    var x = v
    if x < 0 { buf.append(45); x = -x }
    if x == 0 { buf.append(48); return }
    var digs = [Int](repeating: 0, count: 16)
    var dc = 0
    while x > 0 { digs[dc] = 48 + (x % 10); dc += 1; x /= 10 }
    var i = dc - 1
    while i >= 0 { buf.append(digs[i]); i -= 1 }
}

func push2d(_ buf: inout [Int], _ v: Int) {
    buf.append(48 + (v / 10))
    buf.append(48 + (v % 10))
}

func parseVal(_ doc: [Int], _ start: Int, _ n: Int) -> (Int, Int) {
    var p = start
    if doc[p] == 34 {
        p += 1
        var vh = 17
        while p < n && doc[p] != 34 {
            var ch = doc[p]
            if ch == 92 && p + 1 < n {
                p += 1
                let e = doc[p]
                if e == 110 { ch = 10 }
                else if e == 116 { ch = 9 }
                else if e == 34 { ch = 34 }
                else if e == 92 { ch = 92 }
                else { ch = e }
            }
            vh = (vh * 131 + ch) % modV
            p += 1
        }
        if p < n { p += 1 }
        return (vh, p)
    } else if doc[p] == 91 {
        p += 1
        var ah = 29
        while p < n {
            while p < n && (doc[p] == 32 || doc[p] == 9 || doc[p] == 44) { p += 1 }
            if p >= n || doc[p] == 93 {
                if p < n { p += 1 }
                break
            }
            let (ev, np) = parseVal(doc, p, n)
            ah = (ah * 257 + ev) % modV
            p = np
        }
        return (ah, p)
    } else if doc[p] == 116 {
        return (1, p + 4)
    } else if doc[p] == 102 {
        return (0, p + 5)
    }
    var neg = false
    if doc[p] == 45 { neg = true; p += 1 }
    var v = 0
    while p < n && ((doc[p] >= 48 && doc[p] <= 57) || doc[p] == 95) {
        if doc[p] != 95 { v = v * 10 + (doc[p] - 48) }
        p += 1
    }
    if neg { v = -v }
    v %= modV
    if v < 0 { v += modV }
    return (v, p)
}

func mainFunc() {
    var doc: [Int] = []
    doc.reserveCapacity(16384)
    pushStr(&doc, "# Auto-generated microservice configuration\n")
    for s in 0..<48 {
        pushStr(&doc, "\n[svc_"); push2d(&doc, s); pushStr(&doc, "]\n")
        pushStr(&doc, "name = \"worker-"); push2d(&doc, s)
        pushStr(&doc, "\\tprod\\n\\\"v"); pushInt(&doc, s % 5)
        pushStr(&doc, "\\\"\" # inline comment\n")
        pushStr(&doc, "port = "); pushInt(&doc, 8000 + s * 10); doc.append(10)
        pushStr(&doc, "max_conn = "); pushInt(&doc, 1000 + (s % 7) * 500)
        doc.append(95); pushInt(&doc, 100 + s); doc.append(10)
        if (s & 1) == 0 { pushStr(&doc, "enabled = true\n") }
        else { pushStr(&doc, "enabled = false\n") }
        if (s % 9) == 0 { pushStr(&doc, "timeout_ms = -"); pushInt(&doc, 50 + s * 3); doc.append(10) }
        else { pushStr(&doc, "timeout_ms = "); pushInt(&doc, 250 + s * 15); doc.append(10) }
        pushStr(&doc, "retries = [")
        pushInt(&doc, 1 + (s % 3)); pushStr(&doc, ", ")
        pushInt(&doc, 2 + (s % 5)); pushStr(&doc, ", ")
        pushInt(&doc, 4 + (s % 7)); pushStr(&doc, ", ")
        pushInt(&doc, 8 + (s % 11)); pushStr(&doc, "]\n")
        pushStr(&doc, "endpoints = [\"/v1/s"); pushInt(&doc, s)
        pushStr(&doc, "\", \"/health\\t"); pushInt(&doc, s)
        pushStr(&doc, "\", \"/metrics\"]\n")
    }

    let n = doc.count
    var totalEntries = 0
    var ck = 0
    for rnd in 0..<1000 {
        var pos = 0
        var secHash = 0
        var entries = 0
        var roundCk = 0
        while pos < n {
            while pos < n && (doc[pos] == 32 || doc[pos] == 9 || doc[pos] == 10 || doc[pos] == 13) { pos += 1 }
            if pos >= n { break }
            let c = doc[pos]
            if c == 35 {
                while pos < n && doc[pos] != 10 { pos += 1 }
                continue
            }
            if c == 91 {
                pos += 1
                var sh = 0
                while pos < n && doc[pos] != 93 { sh = (sh * 131 + doc[pos]) % modV; pos += 1 }
                if pos < n { pos += 1 }
                secHash = sh
                while pos < n && doc[pos] != 10 { pos += 1 }
                continue
            }
            var kh = secHash
            while pos < n && doc[pos] != 61 && doc[pos] != 32 && doc[pos] != 9 && doc[pos] != 10 {
                kh = (kh * 131 + doc[pos]) % modV
                pos += 1
            }
            while pos < n && (doc[pos] == 32 || doc[pos] == 9) { pos += 1 }
            if pos < n && doc[pos] == 61 { pos += 1 }
            while pos < n && (doc[pos] == 32 || doc[pos] == 9) { pos += 1 }
            let (vh, np) = parseVal(doc, pos, n)
            pos = np
            while pos < n && doc[pos] != 10 { pos += 1 }
            entries += 1
            roundCk = (roundCk * 31 + (kh * 7 + vh + rnd) % modV) % modV
        }
        totalEntries += entries
        ck = (ck * 37 + roundCk) % modV
    }
    print(totalEntries)
    print(ck)
}

mainFunc()
