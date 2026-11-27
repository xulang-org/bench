let modV = 1000000007
let pmax = 2048
let maxOrd = 262144

final class OrderBook {
    var bHead = [Int](repeating: -1, count: pmax)
    var bTail = [Int](repeating: -1, count: pmax)
    var aHead = [Int](repeating: -1, count: pmax)
    var aTail = [Int](repeating: -1, count: pmax)
    var oSide = [Int](repeating: 0, count: maxOrd)
    var oPx = [Int](repeating: 0, count: maxOrd)
    var oQty = [Int](repeating: 0, count: maxOrd)
    var oAct = [Int](repeating: 0, count: maxOrd)
    var oPrev = [Int](repeating: -1, count: maxOrd)
    var oNext = [Int](repeating: -1, count: maxOrd)

    func pushBid(_ px: Int, _ oid: Int) {
        let t = bTail[px]
        oPrev[oid] = t
        oNext[oid] = -1
        if t != -1 {
            oNext[t] = oid
        } else {
            bHead[px] = oid
        }
        bTail[px] = oid
    }

    func pushAsk(_ px: Int, _ oid: Int) {
        let t = aTail[px]
        oPrev[oid] = t
        oNext[oid] = -1
        if t != -1 {
            oNext[t] = oid
        } else {
            aHead[px] = oid
        }
        aTail[px] = oid
    }

    func unlinkBid(_ px: Int, _ oid: Int) {
        let pr = oPrev[oid]
        let nx = oNext[oid]
        if pr != -1 {
            oNext[pr] = nx
        } else {
            bHead[px] = nx
        }
        if nx != -1 {
            oPrev[nx] = pr
        } else {
            bTail[px] = pr
        }
        oPrev[oid] = -1
        oNext[oid] = -1
    }

    func unlinkAsk(_ px: Int, _ oid: Int) {
        let pr = oPrev[oid]
        let nx = oNext[oid]
        if pr != -1 {
            oNext[pr] = nx
        } else {
            aHead[px] = nx
        }
        if nx != -1 {
            oPrev[nx] = pr
        } else {
            aTail[px] = pr
        }
        oPrev[oid] = -1
        oNext[oid] = -1
    }
}

func run() {
    let ob = OrderBook()
    var rng = 70707070

    var bestBid = -1
    var bestAsk = pmax
    var nextId = 0
    var trades = 0
    var cancels = 0
    var ck = 0

    for _ in 0..<250000 {
        rng = (rng * 1103515245 + 12345) & 2147483647
        let r = rng % 10
        if r < 2 && nextId > 0 {
            let win = nextId < 4096 ? nextId : 4096
            rng = (rng * 1103515245 + 12345) & 2147483647
            let cid = nextId - 1 - (rng % win)
            if ob.oAct[cid] == 1 {
                let px = ob.oPx[cid]
                if ob.oSide[cid] == 0 {
                    ob.unlinkBid(px, cid)
                    if px == bestBid && ob.bHead[px] == -1 {
                        while bestBid >= 0 && ob.bHead[bestBid] == -1 {
                            bestBid -= 1
                        }
                    }
                } else {
                    ob.unlinkAsk(px, cid)
                    if px == bestAsk && ob.aHead[px] == -1 {
                        while bestAsk < pmax && ob.aHead[bestAsk] == -1 {
                            bestAsk += 1
                        }
                    }
                }
                ob.oAct[cid] = 0
                cancels += 1
            }
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647
            let side = (rng >> 16) & 1
            let mid: Int
            if bestBid >= 0 && bestAsk < pmax {
                mid = (bestBid + bestAsk) >> 1
            } else if bestBid >= 0 {
                mid = bestBid
            } else if bestAsk < pmax {
                mid = bestAsk
            } else {
                mid = 1024
            }
            rng = (rng * 1103515245 + 12345) & 2147483647
            var px = mid + (rng % 41) - 20
            if px < 1 { px = 1 }
            if px > pmax - 2 { px = pmax - 2 }
            rng = (rng * 1103515245 + 12345) & 2147483647
            var qty = 1 + (rng % 50)

            if side == 0 {
                while qty > 0 && bestAsk <= px {
                    let oid = ob.aHead[bestAsk]
                    let fill = qty < ob.oQty[oid] ? qty : ob.oQty[oid]
                    qty -= fill
                    ob.oQty[oid] -= fill
                    trades += 1
                    ck = (ck * 31 + fill * 1009 + bestAsk) % modV
                    if ob.oQty[oid] == 0 {
                        ob.unlinkAsk(bestAsk, oid)
                        ob.oAct[oid] = 0
                        if ob.aHead[bestAsk] == -1 {
                            while bestAsk < pmax && ob.aHead[bestAsk] == -1 {
                                bestAsk += 1
                            }
                        }
                    }
                }
                if qty > 0 {
                    let oid = nextId
                    nextId += 1
                    ob.oSide[oid] = 0
                    ob.oPx[oid] = px
                    ob.oQty[oid] = qty
                    ob.oAct[oid] = 1
                    ob.pushBid(px, oid)
                    if px > bestBid { bestBid = px }
                }
            } else {
                while qty > 0 && bestBid >= px {
                    let oid = ob.bHead[bestBid]
                    let fill = qty < ob.oQty[oid] ? qty : ob.oQty[oid]
                    qty -= fill
                    ob.oQty[oid] -= fill
                    trades += 1
                    ck = (ck * 31 + fill * 1009 + bestBid) % modV
                    if ob.oQty[oid] == 0 {
                        ob.unlinkBid(bestBid, oid)
                        ob.oAct[oid] = 0
                        if ob.bHead[bestBid] == -1 {
                            while bestBid >= 0 && ob.bHead[bestBid] == -1 {
                                bestBid -= 1
                            }
                        }
                    }
                }
                if qty > 0 {
                    let oid = nextId
                    nextId += 1
                    ob.oSide[oid] = 1
                    ob.oPx[oid] = px
                    ob.oQty[oid] = qty
                    ob.oAct[oid] = 1
                    ob.pushAsk(px, oid)
                    if px < bestAsk { bestAsk = px }
                }
            }
        }
    }

    ck = (ck * 37 + cancels * 17 + (bestBid + 1) * 7 + bestAsk) % modV
    print("\(trades)\n\(ck)")
}

run()
