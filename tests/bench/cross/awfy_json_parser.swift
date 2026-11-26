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
    var digs = [Int](repeating: 0, count: 32)
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

func buildJsonPayload() -> [Int] {
    var buf: [Int] = []
    buf.reserveCapacity(8192)
    pushStr(&buf, "{\"meta\":{\"id\":1000,\"active\":true,\"deleted\":false,\"note\":null,\"ratio\":-12.375e2},\"records\":[")
    for r in 0..<48 {
        if r > 0 {
            buf.append(44)
        }
        let v0 = (r * 37 + 11) % 997 - 400
        let v1 = (r * 53 + 7) % 503
        let v2 = -(r * 19 + 3)
        let v3 = r * 7 + 1
        pushStr(&buf, "{\"id\":")
        pushInt(&buf, r)
        pushStr(&buf, ",\"name\":\"item_")
        pushInt(&buf, r)
        buf.append(92)
        buf.append(34)
        buf.append(118)
        buf.append(92)
        buf.append(92)
        buf.append(110)
        buf.append(34)
        if r % 2 == 0 {
            pushStr(&buf, ",\"ok\":true,\"err\":null,\"vals\":[")
        } else {
            pushStr(&buf, ",\"ok\":false,\"err\":null,\"vals\":[")
        }
        pushInt(&buf, v0)
        buf.append(44)
        pushInt(&buf, v1)
        buf.append(46)
        buf.append(48 + (r % 10))
        buf.append(44)
        pushInt(&buf, v2)
        pushStr(&buf, "e1,")
        pushInt(&buf, v3)
        pushStr(&buf, "],\"cfg\":{\"a\":")
        pushInt(&buf, r * 3 + 1)
        pushStr(&buf, ",\"b\":\"tag_")
        buf.append(48 + (r % 7))
        pushStr(&buf, "\",\"c\":[true,false,null]}}")
    }
    pushStr(&buf, "]}")
    return buf
}

final class JsonParser {
    let buf: [Int]
    var pos = 0
    let n: Int
    var kind: [Int] = []
    var val: [Int] = []
    var firstChild: [Int] = []
    var nextSib: [Int] = []

    init(_ buf: [Int]) {
        self.buf = buf
        self.n = buf.count
        self.kind.reserveCapacity(1024)
        self.val.reserveCapacity(1024)
        self.firstChild.reserveCapacity(1024)
        self.nextSib.reserveCapacity(1024)
    }

    func newNode(_ k: Int, _ v: Int) -> Int {
        let idx = kind.count
        kind.append(k)
        val.append(v)
        firstChild.append(-1)
        nextSib.append(-1)
        return idx
    }

    func skipWs() {
        while pos < n {
            let c = buf[pos]
            if c == 32 || c == 9 || c == 10 || c == 13 {
                pos += 1
            } else {
                break
            }
        }
    }

    func parseStringHash() -> Int {
        pos += 1
        var h = 0
        while pos < n {
            let c = buf[pos]
            pos += 1
            if c == 34 {
                return h
            }
            if c == 92 {
                if pos < n {
                    let ec = buf[pos]
                    pos += 1
                    h = (h * 131 + ec + 256) % 1000000007
                }
            } else {
                h = (h * 131 + c) % 1000000007
            }
        }
        return h
    }

    func parseNumberHash() -> Int {
        var h = 0
        if pos < n && buf[pos] == 45 {
            h = 45
            pos += 1
        }
        while pos < n && buf[pos] >= 48 && buf[pos] <= 57 {
            h = (h * 131 + buf[pos]) % 1000000007
            pos += 1
        }
        if pos < n && buf[pos] == 46 {
            h = (h * 131 + 46) % 1000000007
            pos += 1
            while pos < n && buf[pos] >= 48 && buf[pos] <= 57 {
                h = (h * 131 + buf[pos]) % 1000000007
                pos += 1
            }
        }
        if pos < n && (buf[pos] == 101 || buf[pos] == 69) {
            h = (h * 131 + 101) % 1000000007
            pos += 1
            if pos < n && (buf[pos] == 43 || buf[pos] == 45) {
                h = (h * 131 + buf[pos]) % 1000000007
                pos += 1
            }
            while pos < n && buf[pos] >= 48 && buf[pos] <= 57 {
                h = (h * 131 + buf[pos]) % 1000000007
                pos += 1
            }
        }
        return h
    }

    func parseVal() -> Int {
        skipWs()
        let c = buf[pos]
        if c == 123 {
            pos += 1
            let node = newNode(6, 0)
            skipWs()
            if pos < n && buf[pos] == 125 {
                pos += 1
                return node
            }
            var tail = -1
            var cnt = 0
            while pos < n {
                skipWs()
                let kh = parseStringHash()
                skipWs()
                pos += 1
                let child = parseVal()
                val[node] = (val[node] * 31 + kh) % 1000000007
                if tail == -1 {
                    firstChild[node] = child
                } else {
                    nextSib[tail] = child
                }
                tail = child
                cnt += 1
                skipWs()
                if pos < n && buf[pos] == 44 {
                    pos += 1
                } else {
                    pos += 1
                    break
                }
            }
            val[node] = (val[node] * 31 + cnt) % 1000000007
            return node
        } else if c == 91 {
            pos += 1
            let node = newNode(5, 0)
            skipWs()
            if pos < n && buf[pos] == 93 {
                pos += 1
                return node
            }
            var tail = -1
            var cnt = 0
            while pos < n {
                let child = parseVal()
                if tail == -1 {
                    firstChild[node] = child
                } else {
                    nextSib[tail] = child
                }
                tail = child
                cnt += 1
                skipWs()
                if pos < n && buf[pos] == 44 {
                    pos += 1
                } else {
                    pos += 1
                    break
                }
            }
            val[node] = cnt
            return node
        } else if c == 34 {
            return newNode(4, parseStringHash())
        } else if c == 116 {
            pos += 4
            return newNode(2, 1)
        } else if c == 102 {
            pos += 5
            return newNode(2, 0)
        } else if c == 110 {
            pos += 4
            return newNode(1, 0)
        } else {
            return newNode(3, parseNumberHash())
        }
    }

    func walk(_ u: Int) -> Int {
        var h = (kind[u] * 1000003 + val[u]) % 1000000007
        var ch = firstChild[u]
        while ch != -1 {
            h = (h * 31 + walk(ch)) % 1000000007
            ch = nextSib[ch]
        }
        return h
    }
}

func main() {
    var buf = buildJsonPayload()
    var totNodes = 0
    var totHash = 0
    for r in 0..<400 {
        let v = 1000 + r
        buf[14] = 48 + (v / 1000) % 10
        buf[15] = 48 + (v / 100) % 10
        buf[16] = 48 + (v / 10) % 10
        buf[17] = 48 + v % 10
        let p = JsonParser(buf)
        let root = p.parseVal()
        totNodes += p.kind.count
        totHash = (totHash + p.walk(root)) % 1000000007
    }
    print(totNodes)
    print(totHash)
}

main()
