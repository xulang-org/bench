package main

import "fmt"

type RichardsState struct {
	pktLink   [8]int64
	pktID     [8]int64
	pktKind   [8]int64
	pktDatum  [8]int64
	pktData   [32]int64
	pktN      int64
	tLink     [6]int64
	tPri      [6]int64
	tInp      [6]int64
	tPktPend  [6]int64
	tWaiting  [6]int64
	tHolding  [6]int64
	tV1       [6]int64
	tV2       [6]int64
	taskList  int64
	queueCnt  int64
	holdCnt   int64
	cur       int64
	curID     int64
}

func createPkt(s *RichardsState, link, identity, kind int64) int64 {
	idx := s.pktN
	s.pktN++
	s.pktLink[idx] = link
	s.pktID[idx] = identity
	s.pktKind[idx] = kind
	s.pktDatum[idx] = 0
	base := idx * 4
	s.pktData[base] = 0
	s.pktData[base+1] = 0
	s.pktData[base+2] = 0
	s.pktData[base+3] = 0
	return idx
}

func appendPkt(s *RichardsState, pkt, head int64) int64 {
	s.pktLink[pkt] = -1
	if head == -1 {
		return pkt
	}
	cur := head
	for s.pktLink[cur] != -1 {
		cur = s.pktLink[cur]
	}
	s.pktLink[cur] = pkt
	return head
}

func addTask(s *RichardsState, tid, pri, inp, pktP, waitF, holdF, v1, v2 int64) {
	s.tLink[tid] = s.taskList
	s.tPri[tid] = pri
	s.tInp[tid] = inp
	s.tPktPend[tid] = pktP
	s.tWaiting[tid] = waitF
	s.tHolding[tid] = holdF
	s.tV1[tid] = v1
	s.tV2[tid] = v2
	s.taskList = tid
}

func queuePkt(s *RichardsState, p int64) int64 {
	dest := s.pktID[p]
	if dest < 0 || dest >= 6 {
		return -1
	}
	s.queueCnt++
	s.pktLink[p] = -1
	s.pktID[p] = s.curID
	if s.tInp[dest] == -1 {
		s.tInp[dest] = p
		s.tPktPend[dest] = 1
		if s.tPri[dest] > s.tPri[s.cur] {
			return dest
		}
	} else {
		s.tInp[dest] = appendPkt(s, p, s.tInp[dest])
	}
	return s.cur
}

func runRichardsOnce(s *RichardsState) {
	s.pktN = 0
	s.taskList = -1
	s.queueCnt = 0
	s.holdCnt = 0
	s.curID = -1

	addTask(s, 0, 0, -1, 0, 0, 0, 1, 10000)

	wq := createPkt(s, -1, 1, 1)
	wq = createPkt(s, wq, 1, 1)
	addTask(s, 1, 1000, wq, 1, 1, 0, 2, 0)

	wq = createPkt(s, -1, 4, 0)
	wq = createPkt(s, wq, 4, 0)
	wq = createPkt(s, wq, 4, 0)
	addTask(s, 2, 2000, wq, 1, 1, 0, -1, -1)

	wq = createPkt(s, -1, 5, 0)
	wq = createPkt(s, wq, 5, 0)
	wq = createPkt(s, wq, 5, 0)
	addTask(s, 3, 3000, wq, 1, 1, 0, -1, -1)

	addTask(s, 4, 4000, -1, 0, 1, 0, -1, 0)
	addTask(s, 5, 5000, -1, 0, 1, 0, -1, 0)

	s.cur = s.taskList
	for s.cur != -1 {
		c := s.cur
		if s.tHolding[c] != 0 || (s.tPktPend[c] == 0 && s.tWaiting[c] != 0) {
			s.cur = s.tLink[c]
			continue
		}
		s.curID = c
		var msg int64 = -1
		if s.tHolding[c] == 0 && s.tWaiting[c] != 0 && s.tPktPend[c] != 0 {
			msg = s.tInp[c]
			s.tInp[c] = s.pktLink[msg]
			if s.tInp[c] == -1 {
				s.tPktPend[c] = 0
			} else {
				s.tPktPend[c] = 1
			}
			s.tWaiting[c] = 0
			s.tHolding[c] = 0
		}

		cid := s.curID
		if cid == 0 {
			s.tV2[c]--
			if s.tV2[c] == 0 {
				s.holdCnt++
				s.tHolding[c] = 1
				s.cur = s.tLink[c]
			} else if (s.tV1[c] & 1) == 0 {
				s.tV1[c] >>= 1
				s.tHolding[4] = 0
				if s.tPri[4] > s.tPri[c] {
					s.cur = 4
				}
			} else {
				s.tV1[c] = (s.tV1[c] >> 1) ^ 53256
				s.tHolding[5] = 0
				if s.tPri[5] > s.tPri[c] {
					s.cur = 5
				}
			}
		} else if cid == 1 {
			if msg == -1 {
				s.tWaiting[c] = 1
			} else {
				if s.tV1[c] == 2 {
					s.tV1[c] = 3
				} else {
					s.tV1[c] = 2
				}
				s.pktID[msg] = s.tV1[c]
				s.pktDatum[msg] = 0
				base := msg * 4
				for i := int64(0); i < 4; i++ {
					s.tV2[c]++
					if s.tV2[c] > 26 {
						s.tV2[c] = 1
					}
					s.pktData[base+i] = 64 + s.tV2[c]
				}
				s.cur = queuePkt(s, msg)
			}
		} else if cid == 2 || cid == 3 {
			if msg != -1 {
				if s.pktKind[msg] == 1 {
					s.tV1[c] = appendPkt(s, msg, s.tV1[c])
				} else {
					s.tV2[c] = appendPkt(s, msg, s.tV2[c])
				}
			}
			wp := s.tV1[c]
			if wp == -1 {
				s.tWaiting[c] = 1
			} else {
				cnt := s.pktDatum[wp]
				if cnt >= 4 {
					s.tV1[c] = s.pktLink[wp]
					s.cur = queuePkt(s, wp)
				} else {
					dp := s.tV2[c]
					if dp == -1 {
						s.tWaiting[c] = 1
					} else {
						s.tV2[c] = s.pktLink[dp]
						s.pktDatum[dp] = s.pktData[wp*4+cnt]
						s.pktDatum[wp] = cnt + 1
						s.cur = queuePkt(s, dp)
					}
				}
			}
		} else {
			if msg == -1 {
				if s.tV1[c] == -1 {
					s.tWaiting[c] = 1
				} else {
					fp := s.tV1[c]
					s.tV1[c] = -1
					s.cur = queuePkt(s, fp)
				}
			} else {
				s.tV1[c] = msg
				s.holdCnt++
				s.tHolding[c] = 1
				s.cur = s.tLink[c]
			}
		}
	}
}

func main() {
	var st RichardsState
	var totQ int64
	var totH int64
	for r := int64(0); r < 50; r++ {
		runRichardsOnce(&st)
		totQ += st.queueCnt
		totH += st.holdCnt
	}
	fmt.Println(totQ)
	fmt.Println(totH)
}
