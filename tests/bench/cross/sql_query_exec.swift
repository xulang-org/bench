let modV = 1000000007

func run() {
    let nCust = 8192
    let htCap = 16384
    let htMask = 16383
    let nOrd = 200000
    var rng = 42424242

    var custId = [Int](repeating: 0, count: nCust)
    var custReg = [Int](repeating: 0, count: nCust)
    var custTier = [Int](repeating: 0, count: nCust)
    var htKey = [Int](repeating: -1, count: htCap)
    var htVal = [Int](repeating: -1, count: htCap)

    for i in 0..<nCust {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let cid = 100000 + i * 7 + (rng % 5)
        custId[i] = cid
        rng = (rng * 1103515245 + 12345) & 2147483647
        custReg[i] = rng % 16
        rng = (rng * 1103515245 + 12345) & 2147483647
        custTier[i] = rng % 4
        var slot = ((cid * 2654435761) >> 16) & htMask
        while htKey[slot] != -1 {
            slot = (slot + 1) & htMask
        }
        htKey[slot] = cid
        htVal[slot] = i
    }

    var ordCid = [Int](repeating: 0, count: nOrd)
    var ordCat = [Int](repeating: 0, count: nOrd)
    var ordAmt = [Int](repeating: 0, count: nOrd)
    var ordStatus = [Int](repeating: 0, count: nOrd)

    for i in 0..<nOrd {
        rng = (rng * 1103515245 + 12345) & 2147483647
        if (rng % 20) < 17 {
            rng = (rng * 1103515245 + 12345) & 2147483647
            ordCid[i] = custId[rng % nCust]
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647
            ordCid[i] = 9000000 + (rng % 50000)
        }
        rng = (rng * 1103515245 + 12345) & 2147483647
        ordCat[i] = rng % 32
        rng = (rng * 1103515245 + 12345) & 2147483647
        ordAmt[i] = 100 + (rng % 2000)
        rng = (rng * 1103515245 + 12345) & 2147483647
        ordStatus[i] = (rng % 5) != 0 ? 1 : 0
    }

    var grpCnt = [Int](repeating: 0, count: 512)
    var grpRev = [Int](repeating: 0, count: 512)
    var active = [Int](repeating: 0, count: 512)
    var totalRows = 0
    var ck = 0

    for rnd in 0..<16 {
        let minAmt = 350 + rnd * 50
        for b in 0..<512 {
            grpCnt[b] = 0
            grpRev[b] = 0
        }
        for i in 0..<nOrd {
            if ordStatus[i] != 1 {
                continue
            }
            let amt = ordAmt[i]
            if amt < minAmt {
                continue
            }
            let cid = ordCid[i]
            var slot = ((cid * 2654435761) >> 16) & htMask
            var found = -1
            while htKey[slot] != -1 {
                if htKey[slot] == cid {
                    found = htVal[slot]
                    break
                }
                slot = (slot + 1) & htMask
            }
            if found == -1 {
                continue
            }
            let tier = custTier[found]
            if tier == 0 {
                continue
            }
            let gb = custReg[found] * 32 + ordCat[i]
            grpCnt[gb] += 1
            grpRev[gb] += amt * tier
            totalRows += 1
        }

        var acnt = 0
        for b in 0..<512 {
            if grpCnt[b] > 0 {
                active[acnt] = b
                acnt += 1
            }
        }
        if acnt > 1 {
            for i in 1..<acnt {
                let kb = active[i]
                let kr = grpRev[kb]
                var j = i - 1
                while j >= 0 {
                    let jb = active[j]
                    let jr = grpRev[jb]
                    if jr < kr || (jr == kr && jb > kb) {
                        active[j + 1] = jb
                        j -= 1
                    } else {
                        break
                    }
                }
                active[j + 1] = kb
            }
        }
        for i in 0..<acnt {
            let gb = active[i]
            let row = (gb * 1000003 + grpCnt[gb] * 97 + (grpRev[gb] % modV)) % modV
            ck = (ck * 31 + row) % modV
        }
    }

    print("\(totalRows)\n\(ck)")
}

run()
