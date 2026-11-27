let modV = 1000000007

func crc32Slice(_ crcTbl: [Int], _ buf: [Int], _ start: Int, _ length: Int) -> Int {
    let mask32 = 4294967295
    var c = mask32
    let end = start + length
    for i in start..<end {
        let idx = (c ^ buf[i]) & 255
        c = crcTbl[idx] ^ (c >> 8)
    }
    return c ^ mask32
}

func kvPut(_ kvKey: inout [Int], _ kvVal: inout [Int], _ k: Int, _ v: Int) {
    let kvMask = 8191
    var slot = ((k * 2654435761) >> 16) & kvMask
    var firstTomb = -1
    while true {
        let cur = kvKey[slot]
        if cur == k {
            kvVal[slot] = v
            return
        }
        if cur == -1 {
            let dst = firstTomb != -1 ? firstTomb : slot
            kvKey[dst] = k
            kvVal[dst] = v
            return
        }
        if cur == -2 && firstTomb == -1 {
            firstTomb = slot
        }
        slot = (slot + 1) & kvMask
    }
}

func kvDel(_ kvKey: inout [Int], _ kvVal: inout [Int], _ k: Int) {
    let kvMask = 8191
    var slot = ((k * 2654435761) >> 16) & kvMask
    while true {
        let cur = kvKey[slot]
        if cur == -1 {
            return
        }
        if cur == k {
            kvKey[slot] = -2
            kvVal[slot] = 0
            return
        }
        slot = (slot + 1) & kvMask
    }
}

func kvGet(_ kvKey: [Int], _ kvVal: [Int], _ k: Int) -> Int {
    let kvMask = 8191
    var slot = ((k * 2654435761) >> 16) & kvMask
    while true {
        let cur = kvKey[slot]
        if cur == -1 {
            return -1
        }
        if cur == k {
            return kvVal[slot]
        }
        slot = (slot + 1) & kvMask
    }
}

func run() {
    let poly = 3988292384
    var crcTbl = [Int](repeating: 0, count: 256)
    for i in 0..<256 {
        var c = i
        for _ in 0..<8 {
            if (c & 1) != 0 {
                c = poly ^ (c >> 1)
            } else {
                c >>= 1
            }
        }
        crcTbl[i] = c
    }

    let kvCap = 8192
    var kvKey = [Int](repeating: -1, count: kvCap)
    var kvVal = [Int](repeating: 0, count: kvCap)
    var buf = [Int](repeating: 0, count: 180000)

    var rng = 999888777
    var lsn = 1
    var replayed = 0
    var ck = 0

    for seg in 0..<40 {
        var blen = 0
        for _ in 0..<3000 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let op = (rng % 6) == 0 ? 2 : 1
            rng = (rng * 1103515245 + 12345) & 2147483647
            let key = rng % 4096
            var vlen = 0
            if op == 1 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                vlen = 8 + (rng % 32)
            }
            rng = (rng * 1103515245 + 12345) & 2147483647
            let seed = (rng >> 4) & 255

            let recStart = blen
            buf[blen] = 87
            buf[blen + 1] = 76
            buf[blen + 2] = op
            buf[blen + 3] = (lsn ^ key) & 255
            buf[blen + 4] = lsn & 255
            buf[blen + 5] = (lsn >> 8) & 255
            buf[blen + 6] = (lsn >> 16) & 255
            buf[blen + 7] = (lsn >> 24) & 255
            buf[blen + 8] = key & 255
            buf[blen + 9] = (key >> 8) & 255
            buf[blen + 10] = (key >> 16) & 255
            buf[blen + 11] = (key >> 24) & 255
            buf[blen + 12] = vlen & 255
            buf[blen + 13] = (vlen >> 8) & 255
            blen += 14
            for j in 0..<vlen {
                buf[blen] = (seed + j * 13 + lsn) & 255
                blen += 1
            }
            let crc = crc32Slice(crcTbl, buf, recStart, 14 + vlen)
            buf[blen] = crc & 255
            buf[blen + 1] = (crc >> 8) & 255
            buf[blen + 2] = (crc >> 16) & 255
            buf[blen + 3] = (crc >> 24) & 255
            blen += 4
            lsn += 1
        }

        if (seg % 4) == 3 {
            blen -= 7
        } else if (seg % 5) == 4 {
            buf[blen - 2] ^= 1
        }

        var pos = 0
        var segRep = 0
        var early = 0
        while pos < blen {
            if pos + 18 > blen {
                early = 1
                break
            }
            if buf[pos] != 87 || buf[pos + 1] != 76 {
                early = 1
                break
            }
            let op = buf[pos + 2]
            if op != 1 && op != 2 {
                early = 1
                break
            }
            let vlen = buf[pos + 12] | (buf[pos + 13] << 8)
            if pos + 18 + vlen > blen {
                early = 1
                break
            }
            let stored = buf[pos + 14 + vlen]
                | (buf[pos + 15 + vlen] << 8)
                | (buf[pos + 16 + vlen] << 16)
                | (buf[pos + 17 + vlen] << 24)
            let calc = crc32Slice(crcTbl, buf, pos, 14 + vlen)
            if calc != stored {
                early = 1
                break
            }
            let key = buf[pos + 8]
                | (buf[pos + 9] << 8)
                | (buf[pos + 10] << 16)
                | (buf[pos + 11] << 24)
            if op == 1 {
                var vh = 0
                for j in 0..<vlen {
                    vh = (vh * 131 + buf[pos + 14 + j]) % modV
                }
                kvPut(&kvKey, &kvVal, key, vh)
            } else {
                kvDel(&kvKey, &kvVal, key)
            }
            segRep += 1
            pos += 18 + vlen
        }
        replayed += segRep
        ck = (ck * 37 + seg * 1009 + segRep * 17 + early) % modV
    }

    for k in 0..<4096 {
        let v = kvGet(kvKey, kvVal, k)
        if v >= 0 {
            ck = (ck * 31 + k * 97 + v) % modV
        }
    }

    print("\(replayed)\n\(ck)")
}

run()
