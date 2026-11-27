let modV = 1000000007

func lz4Compress(_ blocks: [Int], _ srcOff: Int, _ n: Int, _ ht: inout [Int], _ comp: inout [Int]) -> Int {
    for i in 0..<4096 {
        ht[i] = -1
    }
    var op = 0
    var ip = 0
    var anchor = 0
    let limit = n - 12
    let mflimit = n - 5
    while ip < limit {
        let p = srcOff + ip
        let seq = blocks[p] | (blocks[p + 1] << 8) | (blocks[p + 2] << 16) | (blocks[p + 3] << 24)
        let h = ((seq * 73244475) >> 18) & 4095
        let ref = ht[h]
        ht[h] = ip
        if ref >= 0 && (ip - ref) <= 65535 {
            let rp = srcOff + ref
            if blocks[rp] == blocks[p]
                && blocks[rp + 1] == blocks[p + 1]
                && blocks[rp + 2] == blocks[p + 2]
                && blocks[rp + 3] == blocks[p + 3]
            {
                var mlen = 4
                while ip + mlen < mflimit && blocks[rp + mlen] == blocks[p + mlen] {
                    mlen += 1
                }
                let litLen = ip - anchor
                let mExtra = mlen - 4
                let tokLit = litLen >= 15 ? 15 : litLen
                let tokM = mExtra >= 15 ? 15 : mExtra
                comp[op] = (tokLit << 4) | tokM
                op += 1
                if litLen >= 15 {
                    var rem = litLen - 15
                    while rem >= 255 {
                        comp[op] = 255
                        op += 1
                        rem -= 255
                    }
                    comp[op] = rem
                    op += 1
                }
                for j in 0..<litLen {
                    comp[op] = blocks[srcOff + anchor + j]
                    op += 1
                }
                let off = ip - ref
                comp[op] = off & 255
                comp[op + 1] = (off >> 8) & 255
                op += 2
                if mExtra >= 15 {
                    var rem = mExtra - 15
                    while rem >= 255 {
                        comp[op] = 255
                        op += 1
                        rem -= 255
                    }
                    comp[op] = rem
                    op += 1
                }
                ip += mlen
                anchor = ip
                continue
            }
        }
        ip += 1
    }
    let litLen = n - anchor
    let tokLit = litLen >= 15 ? 15 : litLen
    comp[op] = tokLit << 4
    op += 1
    if litLen >= 15 {
        var rem = litLen - 15
        while rem >= 255 {
            comp[op] = 255
            op += 1
            rem -= 255
        }
        comp[op] = rem
        op += 1
    }
    for j in 0..<litLen {
        comp[op] = blocks[srcOff + anchor + j]
        op += 1
    }
    return op
}

func lz4Decompress(_ comp: [Int], _ clen: Int, _ decomp: inout [Int]) {
    var ip = 0
    var op = 0
    while ip < clen {
        let tok = comp[ip]
        ip += 1
        var litLen = tok >> 4
        if litLen == 15 {
            while true {
                let b = comp[ip]
                ip += 1
                litLen += b
                if b != 255 {
                    break
                }
            }
        }
        for _ in 0..<litLen {
            decomp[op] = comp[ip]
            op += 1
            ip += 1
        }
        if ip >= clen {
            break
        }
        let off = comp[ip] | (comp[ip + 1] << 8)
        ip += 2
        var mlen = (tok & 15) + 4
        if (tok & 15) == 15 {
            while true {
                let b = comp[ip]
                ip += 1
                mlen += b
                if b != 255 {
                    break
                }
            }
        }
        let mp = op - off
        for j in 0..<mlen {
            decomp[op] = decomp[mp + j]
            op += 1
        }
    }
}

func run() {
    let blkLen = 32768
    var rng = 135724680
    let rawPhrases = [
        "{\"level\":\"INFO\",\"service\":\"storage-node\",\"msg\":\"compaction_ok\",\"ms\":",
        "{\"level\":\"WARN\",\"service\":\"rpc-gateway\",\"msg\":\"retry_backoff\",\"ms\":",
        "SELECT region, category, SUM(amount) FROM orders WHERE status = 1; ",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "GET /api/v1/users/profile HTTP/1.1\r\nHost: api.xulang.org\r\n\r\n",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    ]
    let phrases = rawPhrases.map { Array($0.utf8).map { Int($0) } }

    var blocks: [Int] = []
    blocks.reserveCapacity(24 * blkLen)
    for _ in 0..<24 {
        var src: [Int] = []
        src.reserveCapacity(blkLen + 128)
        while src.count < blkLen {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let k = rng % 10
            if k < 6 {
                for b in phrases[k] {
                    src.append(b)
                }
                rng = (rng * 1103515245 + 12345) & 2147483647
                let v = rng % 1000
                src.append(48 + (v / 100))
                src.append(48 + ((v / 10) % 10))
                src.append(48 + (v % 10))
                src.append(10)
            } else if k < 8 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let ch = 65 + (rng % 26)
                rng = (rng * 1103515245 + 12345) & 2147483647
                let rl = 12 + (rng % 48)
                for _ in 0..<rl {
                    src.append(ch)
                }
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let rl = 8 + (rng % 24)
                for _ in 0..<rl {
                    rng = (rng * 1103515245 + 12345) & 2147483647
                    src.append(32 + (rng % 95))
                }
            }
        }
        blocks.append(contentsOf: src[0..<blkLen])
    }

    var ht = [Int](repeating: -1, count: 4096)
    var comp = [Int](repeating: 0, count: blkLen + 4096)
    var decomp = [Int](repeating: 0, count: blkLen)

    var totalComp = 0
    var ck = 0
    for _ in 0..<4 {
        for bi in 0..<24 {
            let clen = lz4Compress(blocks, bi * blkLen, blkLen, &ht, &comp)
            lz4Decompress(comp, clen, &decomp)
            var h = clen
            for i in 0..<blkLen {
                h = (h * 131 + decomp[i]) % modV
            }
            totalComp += clen
            ck = (ck * 31 + h) % modV
        }
    }

    print("\(totalComp)\n\(ck)")
}

run()
