let modV = 1000000007

func toBytes(_ s: String) -> [Int] {
    return s.utf8.map { Int($0) }
}

func emitRaw(_ out: inout [Int], _ s: [Int], _ start: Int, _ ln: Int) {
    for i in 0..<ln {
        out.append(s[start + i])
    }
}

func emitEsc(_ out: inout [Int], _ s: [Int]) {
    for ch in s {
        if ch == 38 { out.append(contentsOf: [38, 97, 109, 112, 59]) }
        else if ch == 60 { out.append(contentsOf: [38, 108, 116, 59]) }
        else if ch == 62 { out.append(contentsOf: [38, 103, 116, 59]) }
        else if ch == 34 { out.append(contentsOf: [38, 113, 117, 111, 116, 59]) }
        else if ch == 39 { out.append(contentsOf: [38, 35, 51, 57, 59]) }
        else { out.append(ch) }
    }
}

func matchBytes(_ src: [Int], _ s: Int, _ e: Int, _ pat: [Int]) -> Bool {
    var a = s
    var b = e
    while a < b && (src[a] == 32 || src[a] == 9) { a += 1 }
    while b > a && (src[b - 1] == 32 || src[b - 1] == 9) { b -= 1 }
    if b - a != pat.count { return false }
    for i in 0..<pat.count {
        if src[a + i] != pat[i] { return false }
    }
    return true
}

func varId(_ src: [Int], _ s: Int, _ e: Int) -> Int {
    if matchBytes(src, s, e, toBytes("title")) { return 0 }
    if matchBytes(src, s, e, toBytes("badge")) { return 1 }
    if matchBytes(src, s, e, toBytes("name")) { return 2 }
    if matchBytes(src, s, e, toBytes("desc")) { return 3 }
    return -1
}

func mainFunc() {
    let tmpl = toBytes("<div class=\"card\"><h1>{{title}}</h1>{{{badge}}}<ul>{%for item%}<li class=\"{%if featured%}hot{%else%}std{%endif%}\"><span>{{name}}</span><em>{{desc}}</em></li>{%endfor%}</ul></div>")
    let tlen = tmpl.count
    let patFor = toBytes("for item")
    let patEndfor = toBytes("endfor")
    let patIf = toBytes("if featured")
    let patElse = toBytes("else")
    let patEndif = toBytes("endif")

    let titles = [
        toBytes("Xu <Fast> & Safe"),
        toBytes("Bench \"Suite\" 'v1'"),
        toBytes("Release & Notes <2026>"),
        toBytes("Core / Engine"),
    ]
    let badges = [
        toBytes("<b>PRO</b>"),
        toBytes("<i>LTS</i>"),
        toBytes("<span>NEW</span>"),
        toBytes("<b>OK</b>"),
    ]
    let names = [
        toBytes("Item <alpha> & 1"),
        toBytes("Widget \"beta\""),
        toBytes("Node 'gamma' > 0"),
        toBytes("Cache & Pool"),
        toBytes("Router <v2>"),
        toBytes("Codec \"lz4\""),
        toBytes("Parser 'ast'"),
        toBytes("Engine <core>"),
    ]
    let descs = [
        toBytes("a < b && c > d"),
        toBytes("quote \"here\" & 'there'"),
        toBytes("plain fast path"),
        toBytes("x & y < z"),
    ]

    var opKind: [Int] = []
    var opA: [Int] = []
    var opB: [Int] = []
    var forStack = [Int](repeating: 0, count: 8)
    var ifStack = [Int](repeating: 0, count: 8)
    var elseStack = [Int](repeating: 0, count: 8)
    var out: [Int] = []
    out.reserveCapacity(2048)

    var totalBytes = 0
    var ck = 0
    for rnd in 0..<400 {
        opKind.removeAll(keepingCapacity: true)
        opA.removeAll(keepingCapacity: true)
        opB.removeAll(keepingCapacity: true)
        var forSp = 0
        var ifSp = 0
        var pos = 0
        while pos < tlen {
            var np = pos
            while np + 1 < tlen && !(tmpl[np] == 123 && (tmpl[np + 1] == 123 || tmpl[np + 1] == 37)) { np += 1 }
            if np + 1 >= tlen { np = tlen }
            if np > pos {
                opKind.append(0); opA.append(pos); opB.append(np - pos)
                pos = np
            }
            if pos >= tlen { break }
            if tmpl[pos + 1] == 123 {
                if pos + 2 < tlen && tmpl[pos + 2] == 123 {
                    var end = pos + 3
                    while !(tmpl[end] == 125 && tmpl[end + 1] == 125 && tmpl[end + 2] == 125) { end += 1 }
                    opKind.append(2); opA.append(varId(tmpl, pos + 3, end)); opB.append(0)
                    pos = end + 3
                } else {
                    var end = pos + 2
                    while !(tmpl[end] == 125 && tmpl[end + 1] == 125) { end += 1 }
                    opKind.append(1); opA.append(varId(tmpl, pos + 2, end)); opB.append(0)
                    pos = end + 2
                }
            } else {
                var end = pos + 2
                while !(tmpl[end] == 37 && tmpl[end + 1] == 125) { end += 1 }
                let ts = pos + 2
                if matchBytes(tmpl, ts, end, patFor) {
                    forStack[forSp] = opKind.count; forSp += 1
                    opKind.append(3); opA.append(0); opB.append(0)
                } else if matchBytes(tmpl, ts, end, patEndfor) {
                    forSp -= 1
                    let fidx = forStack[forSp]
                    opKind.append(4); opA.append(fidx + 1); opB.append(0)
                    opA[fidx] = opKind.count
                } else if matchBytes(tmpl, ts, end, patIf) {
                    ifStack[ifSp] = opKind.count; elseStack[ifSp] = -1; ifSp += 1
                    opKind.append(5); opA.append(0); opB.append(0)
                } else if matchBytes(tmpl, ts, end, patElse) {
                    let eidx = opKind.count
                    opKind.append(6); opA.append(0); opB.append(0)
                    let iidx = ifStack[ifSp - 1]
                    opA[iidx] = eidx + 1
                    elseStack[ifSp - 1] = eidx
                } else if matchBytes(tmpl, ts, end, patEndif) {
                    ifSp -= 1
                    let iidx = ifStack[ifSp]
                    let eidx = elseStack[ifSp]
                    if eidx >= 0 { opA[eidx] = opKind.count } else { opA[iidx] = opKind.count }
                    opKind.append(7); opA.append(0); opB.append(0)
                }
                pos = end + 2
            }
        }

        let nOps = opKind.count
        for page in 0..<25 {
            let titleV = titles[(rnd + page) & 3]
            let badgeV = badges[(rnd * 3 + page) & 3]
            out.removeAll(keepingCapacity: true)
            var pc = 0
            var itemIdx = 0
            let itemCnt = 12
            while pc < nOps {
                let op = opKind[pc]
                let a = opA[pc]
                if op == 0 { emitRaw(&out, tmpl, a, opB[pc]); pc += 1 }
                else if op == 1 {
                    if a == 0 { emitEsc(&out, titleV) }
                    else if a == 2 { emitEsc(&out, names[(page + itemIdx + rnd) & 7]) }
                    else if a == 3 { emitEsc(&out, descs[(page * 3 + itemIdx + rnd) & 3]) }
                    pc += 1
                } else if op == 2 {
                    if a == 1 { emitRaw(&out, badgeV, 0, badgeV.count) }
                    pc += 1
                } else if op == 3 {
                    if itemCnt == 0 { pc = a } else { itemIdx = 0; pc += 1 }
                } else if op == 4 {
                    itemIdx += 1
                    if itemIdx < itemCnt { pc = a } else { pc += 1 }
                } else if op == 5 {
                    if ((rnd + page + itemIdx) % 3) == 0 { pc += 1 } else { pc = a }
                } else if op == 6 {
                    pc = a
                } else {
                    pc += 1
                }
            }
            totalBytes += out.count
            var h = 0
            for b in out { h = (h * 131 + b) % modV }
            ck = (ck * 31 + h) % modV
        }
    }
    print(totalBytes)
    print(ck)
}

mainFunc()
