let modV = 1000000007

func putUvarint(_ buf: inout [Int], _ val: Int) {
    var v = val
    while v >= 128 {
        buf.append((v & 127) | 128)
        v >>= 7
    }
    buf.append(v & 127)
}

func zigzagEnc(_ v: Int) -> Int {
    if v >= 0 { return v << 1 }
    return ((-v) << 1) - 1
}

func zigzagDec(_ u: Int) -> Int {
    if (u & 1) == 0 { return u >> 1 }
    return -((u >> 1) + 1)
}

func pushStrBytes(_ buf: inout [Int], _ s: String) {
    for b in s.utf8 {
        buf.append(Int(b))
    }
}

func mainFunc() {
    let symbols = ["BTC-USD", "ETH-EUR", "SOL-JPY", "XU-USD", "NVDA", "AAPL", "GOOG", "MSFT"]
    let tags = ["fast", "batch", "edge", "core", "prod", "canary", "blue", "green"]

    var buf: [Int] = []
    buf.reserveCapacity(32768)
    var meta: [Int] = []
    var packed: [Int] = []
    var msg: [Int] = []
    var qs = [Int](repeating: 0, count: 8)

    var rng = 314159265
    var totalWire = 0
    var ck = 0
    for batch in 0..<400 {
        buf.removeAll(keepingCapacity: true)
        for i in 0..<500 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let orderId = (batch * 500 + i + 1) * 131 + (rng & 1023)
            rng = (rng * 1103515245 + 12345) & 2147483647
            let priceDelta = (rng % 200001) - 100000
            rng = (rng * 1103515245 + 12345) & 2147483647
            let sym = symbols[rng & 7]
            rng = (rng * 1103515245 + 12345) & 2147483647
            let qcnt = 4 + (rng & 3)
            for qi in 0..<qcnt {
                rng = (rng * 1103515245 + 12345) & 2147483647
                qs[qi] = 1 + (rng % 5000)
            }
            rng = (rng * 1103515245 + 12345) & 2147483647
            let regId = 1 + (rng & 31)
            rng = (rng * 1103515245 + 12345) & 2147483647
            let latUs = (rng % 10001) - 5000
            rng = (rng * 1103515245 + 12345) & 2147483647
            let tag = tags[rng & 7]

            meta.removeAll(keepingCapacity: true)
            putUvarint(&meta, (1 << 3) | 0)
            putUvarint(&meta, regId)
            putUvarint(&meta, (2 << 3) | 0)
            putUvarint(&meta, zigzagEnc(latUs))
            putUvarint(&meta, (3 << 3) | 2)
            putUvarint(&meta, tag.utf8.count)
            pushStrBytes(&meta, tag)

            packed.removeAll(keepingCapacity: true)
            for qi in 0..<qcnt { putUvarint(&packed, qs[qi]) }

            msg.removeAll(keepingCapacity: true)
            putUvarint(&msg, (1 << 3) | 0)
            putUvarint(&msg, orderId)
            putUvarint(&msg, (2 << 3) | 0)
            putUvarint(&msg, zigzagEnc(priceDelta))
            putUvarint(&msg, (3 << 3) | 2)
            putUvarint(&msg, sym.utf8.count)
            pushStrBytes(&msg, sym)
            putUvarint(&msg, (4 << 3) | 2)
            putUvarint(&msg, packed.count)
            msg.append(contentsOf: packed)
            putUvarint(&msg, (5 << 3) | 2)
            putUvarint(&msg, meta.count)
            msg.append(contentsOf: meta)

            putUvarint(&buf, msg.count)
            buf.append(contentsOf: msg)
        }

        totalWire += buf.count
        var pos = 0
        let blen = buf.count
        while pos < blen {
            var mlen = 0
            var sh = 0
            while true {
                let b = buf[pos]
                pos += 1
                mlen |= (b & 127) << sh
                if (b & 128) == 0 { break }
                sh += 7
            }
            let end = pos + mlen
            var oid = 0
            var pdelta = 0
            var symSum = 0
            var qSum = 0
            var reg = 0
            var lat = 0
            var tlen = 0
            while pos < end {
                var tagW = 0
                sh = 0
                while true {
                    let b = buf[pos]
                    pos += 1
                    tagW |= (b & 127) << sh
                    if (b & 128) == 0 { break }
                    sh += 7
                }
                let fnum = tagW >> 3
                let wtype = tagW & 7
                if wtype == 0 {
                    var val = 0
                    sh = 0
                    while true {
                        let b = buf[pos]
                        pos += 1
                        val |= (b & 127) << sh
                        if (b & 128) == 0 { break }
                        sh += 7
                    }
                    if fnum == 1 { oid = val }
                    else if fnum == 2 { pdelta = zigzagDec(val) }
                } else if wtype == 2 {
                    var ln = 0
                    sh = 0
                    while true {
                        let b = buf[pos]
                        pos += 1
                        ln |= (b & 127) << sh
                        if (b & 128) == 0 { break }
                        sh += 7
                    }
                    let subEnd = pos + ln
                    if fnum == 3 {
                        while pos < subEnd { symSum += buf[pos]; pos += 1 }
                    } else if fnum == 4 {
                        while pos < subEnd {
                            var qv = 0
                            sh = 0
                            while true {
                                let b = buf[pos]
                                pos += 1
                                qv |= (b & 127) << sh
                                if (b & 128) == 0 { break }
                                sh += 7
                            }
                            qSum += qv
                        }
                    } else if fnum == 5 {
                        while pos < subEnd {
                            var mtag = 0
                            sh = 0
                            while true {
                                let b = buf[pos]
                                pos += 1
                                mtag |= (b & 127) << sh
                                if (b & 128) == 0 { break }
                                sh += 7
                            }
                            let mf = mtag >> 3
                            let mw = mtag & 7
                            if mw == 0 {
                                var mv = 0
                                sh = 0
                                while true {
                                    let b = buf[pos]
                                    pos += 1
                                    mv |= (b & 127) << sh
                                    if (b & 128) == 0 { break }
                                    sh += 7
                                }
                                if mf == 1 { reg = mv }
                                else if mf == 2 { lat = zigzagDec(mv) }
                            } else if mw == 2 {
                                var sln = 0
                                sh = 0
                                while true {
                                    let b = buf[pos]
                                    pos += 1
                                    sln |= (b & 127) << sh
                                    if (b & 128) == 0 { break }
                                    sh += 7
                                }
                                if mf == 3 { tlen = sln }
                                pos += sln
                            }
                        }
                    } else {
                        pos = subEnd
                    }
                }
            }
            var row = (oid + pdelta + symSum + qSum + reg * 13 + lat + tlen * 7) % modV
            if row < 0 { row += modV }
            ck = (ck * 31 + row) % modV
        }
    }
    print(totalWire)
    print(ck)
}

mainFunc()
