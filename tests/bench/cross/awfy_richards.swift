final class RichardsState {
    var pktLink = [Int](repeating: -1, count: 8)
    var pktId = [Int](repeating: 0, count: 8)
    var pktKind = [Int](repeating: 0, count: 8)
    var pktDatum = [Int](repeating: 0, count: 8)
    var pktData = [Int](repeating: 0, count: 32)
    var pktN = 0
    var tLink = [Int](repeating: -1, count: 6)
    var tPri = [Int](repeating: 0, count: 6)
    var tInp = [Int](repeating: -1, count: 6)
    var tPktPend = [Int](repeating: 0, count: 6)
    var tWaiting = [Int](repeating: 0, count: 6)
    var tHolding = [Int](repeating: 0, count: 6)
    var tV1 = [Int](repeating: 0, count: 6)
    var tV2 = [Int](repeating: 0, count: 6)
    var taskList = -1
    var queueCount = 0
    var holdCount = 0
    var cur = -1
    var curId = -1

    func createPkt(_ link: Int, _ identity: Int, _ kind: Int) -> Int {
        let idx = pktN
        pktN += 1
        pktLink[idx] = link
        pktId[idx] = identity
        pktKind[idx] = kind
        pktDatum[idx] = 0
        let base = idx * 4
        pktData[base] = 0
        pktData[base + 1] = 0
        pktData[base + 2] = 0
        pktData[base + 3] = 0
        return idx
    }

    func appendPkt(_ pkt: Int, _ head: Int) -> Int {
        pktLink[pkt] = -1
        if head == -1 {
            return pkt
        }
        var c = head
        while pktLink[c] != -1 {
            c = pktLink[c]
        }
        pktLink[c] = pkt
        return head
    }

    func addTask(_ tid: Int, _ pri: Int, _ inp: Int, _ pktP: Int, _ waitF: Int, _ holdF: Int, _ v1: Int, _ v2: Int) {
        tLink[tid] = taskList
        tPri[tid] = pri
        tInp[tid] = inp
        tPktPend[tid] = pktP
        tWaiting[tid] = waitF
        tHolding[tid] = holdF
        tV1[tid] = v1
        tV2[tid] = v2
        taskList = tid
    }

    func queuePkt(_ p: Int) -> Int {
        let dest = pktId[p]
        if dest < 0 || dest >= 6 {
            return -1
        }
        queueCount += 1
        pktLink[p] = -1
        pktId[p] = curId
        if tInp[dest] == -1 {
            tInp[dest] = p
            tPktPend[dest] = 1
            if tPri[dest] > tPri[cur] {
                return dest
            }
        } else {
            tInp[dest] = appendPkt(p, tInp[dest])
        }
        return cur
    }

    func runOnce() {
        pktN = 0
        taskList = -1
        queueCount = 0
        holdCount = 0
        curId = -1

        addTask(0, 0, -1, 0, 0, 0, 1, 10000)

        var wq = createPkt(-1, 1, 1)
        wq = createPkt(wq, 1, 1)
        addTask(1, 1000, wq, 1, 1, 0, 2, 0)

        wq = createPkt(-1, 4, 0)
        wq = createPkt(wq, 4, 0)
        wq = createPkt(wq, 4, 0)
        addTask(2, 2000, wq, 1, 1, 0, -1, -1)

        wq = createPkt(-1, 5, 0)
        wq = createPkt(wq, 5, 0)
        wq = createPkt(wq, 5, 0)
        addTask(3, 3000, wq, 1, 1, 0, -1, -1)

        addTask(4, 4000, -1, 0, 1, 0, -1, 0)
        addTask(5, 5000, -1, 0, 1, 0, -1, 0)

        cur = taskList
        while cur != -1 {
            let c = cur
            if tHolding[c] != 0 || (tPktPend[c] == 0 && tWaiting[c] != 0) {
                cur = tLink[c]
                continue
            }
            curId = c
            var msg = -1
            if tHolding[c] == 0 && tWaiting[c] != 0 && tPktPend[c] != 0 {
                msg = tInp[c]
                tInp[c] = pktLink[msg]
                tPktPend[c] = (tInp[c] == -1) ? 0 : 1
                tWaiting[c] = 0
                tHolding[c] = 0
            }

            let cid = curId
            if cid == 0 {
                tV2[c] -= 1
                if tV2[c] == 0 {
                    holdCount += 1
                    tHolding[c] = 1
                    cur = tLink[c]
                } else if (tV1[c] & 1) == 0 {
                    tV1[c] >>= 1
                    tHolding[4] = 0
                    if tPri[4] > tPri[c] {
                        cur = 4
                    }
                } else {
                    tV1[c] = (tV1[c] >> 1) ^ 53256
                    tHolding[5] = 0
                    if tPri[5] > tPri[c] {
                        cur = 5
                    }
                }
            } else if cid == 1 {
                if msg == -1 {
                    tWaiting[c] = 1
                } else {
                    tV1[c] = (tV1[c] == 2) ? 3 : 2
                    pktId[msg] = tV1[c]
                    pktDatum[msg] = 0
                    let base = msg * 4
                    for i in 0..<4 {
                        tV2[c] += 1
                        if tV2[c] > 26 {
                            tV2[c] = 1
                        }
                        pktData[base + i] = 64 + tV2[c]
                    }
                    cur = queuePkt(msg)
                }
            } else if cid == 2 || cid == 3 {
                if msg != -1 {
                    if pktKind[msg] == 1 {
                        tV1[c] = appendPkt(msg, tV1[c])
                    } else {
                        tV2[c] = appendPkt(msg, tV2[c])
                    }
                }
                let wp = tV1[c]
                if wp == -1 {
                    tWaiting[c] = 1
                } else {
                    let cnt = pktDatum[wp]
                    if cnt >= 4 {
                        tV1[c] = pktLink[wp]
                        cur = queuePkt(wp)
                    } else {
                        let dp = tV2[c]
                        if dp == -1 {
                            tWaiting[c] = 1
                        } else {
                            tV2[c] = pktLink[dp]
                            pktDatum[dp] = pktData[wp * 4 + cnt]
                            pktDatum[wp] = cnt + 1
                            cur = queuePkt(dp)
                        }
                    }
                }
            } else {
                if msg == -1 {
                    if tV1[c] == -1 {
                        tWaiting[c] = 1
                    } else {
                        let fp = tV1[c]
                        tV1[c] = -1
                        cur = queuePkt(fp)
                    }
                } else {
                    tV1[c] = msg
                    holdCount += 1
                    tHolding[c] = 1
                    cur = tLink[c]
                }
            }
        }
    }
}

func main() {
    let st = RichardsState()
    var totQ = 0
    var totH = 0
    for _ in 0..<50 {
        st.runOnce()
        totQ += st.queueCount
        totH += st.holdCount
    }
    print(totQ)
    print(totH)
}

main()
