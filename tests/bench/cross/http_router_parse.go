package main

import "fmt"

const modV int64 = 1000000007

func pushStr(buf *[]int64, s string) {
	for i := 0; i < len(s); i++ {
		*buf = append(*buf, int64(s[i]))
	}
}

func pushInt(buf *[]int64, v int64) {
	x := v
	if x < 0 {
		*buf = append(*buf, 45)
		x = -x
	}
	if x == 0 {
		*buf = append(*buf, 48)
		return
	}
	var digs [24]int64
	dc := 0
	for x > 0 {
		digs[dc] = 48 + (x % 10)
		dc++
		x /= 10
	}
	for i := dc - 1; i >= 0; i-- {
		*buf = append(*buf, digs[i])
	}
}

func hexVal(b int64) int64 {
	if b >= 48 && b <= 57 {
		return b - 48
	}
	if b >= 65 && b <= 70 {
		return b - 55
	}
	if b >= 97 && b <= 102 {
		return b - 87
	}
	return -1
}

func decodePctHash(buf []int64, start, end int) int64 {
	var h int64
	i := start
	for i < end {
		b := buf[i]
		ch := b
		if b == 43 {
			ch = 32
			i++
		} else if b == 37 && i+2 < end {
			hi := hexVal(buf[i+1])
			lo := hexVal(buf[i+2])
			if hi >= 0 && lo >= 0 {
				ch = (hi << 4) | lo
				i += 3
			} else {
				i++
			}
		} else {
			i++
		}
		h = (h*131 + ch) % modV
	}
	return h
}

type trieRouter struct {
	nodeEdgeHead []int
	nodeParam    []int
	nodeWild     []int
	nodeRoutes   []int
	edgeOff      []int
	edgeLen      []int
	edgeChild    []int
	edgeNext     []int
	segPool      []int64
}

func (rt *trieRouter) newNode() int {
	idx := len(rt.nodeEdgeHead)
	rt.nodeEdgeHead = append(rt.nodeEdgeHead, -1)
	rt.nodeParam = append(rt.nodeParam, -1)
	rt.nodeWild = append(rt.nodeWild, -1)
	for m := 0; m < 5; m++ {
		rt.nodeRoutes = append(rt.nodeRoutes, 0)
	}
	return idx
}

func eqSliceStr(pool []int64, off, ln int, s string) bool {
	if ln != len(s) {
		return false
	}
	for i := 0; i < ln; i++ {
		if pool[off+i] != int64(s[i]) {
			return false
		}
	}
	return true
}

func eqBufPool(buf []int64, s, ln int, pool []int64, off, plen int) bool {
	if ln != plen {
		return false
	}
	for i := 0; i < ln; i++ {
		if buf[s+i] != pool[off+i] {
			return false
		}
	}
	return true
}

func (rt *trieRouter) addRoute(method int, pat []string, rid int) {
	cur := 0
	for i := 0; i < len(pat); i++ {
		seg := pat[i]
		if seg == "*" {
			if rt.nodeWild[cur] < 0 {
				rt.nodeWild[cur] = rt.newNode()
			}
			cur = rt.nodeWild[cur]
		} else if len(seg) > 0 && seg[0] == ':' {
			if rt.nodeParam[cur] < 0 {
				rt.nodeParam[cur] = rt.newNode()
			}
			cur = rt.nodeParam[cur]
		} else {
			e := rt.nodeEdgeHead[cur]
			found := -1
			for e >= 0 {
				if eqSliceStr(rt.segPool, rt.edgeOff[e], rt.edgeLen[e], seg) {
					found = e
					break
				}
				e = rt.edgeNext[e]
			}
			if found >= 0 {
				cur = rt.edgeChild[found]
			} else {
				nxtNode := rt.newNode()
				off := len(rt.segPool)
				for j := 0; j < len(seg); j++ {
					rt.segPool = append(rt.segPool, int64(seg[j]))
				}
				ei := len(rt.edgeOff)
				rt.edgeOff = append(rt.edgeOff, off)
				rt.edgeLen = append(rt.edgeLen, len(seg))
				rt.edgeChild = append(rt.edgeChild, nxtNode)
				rt.edgeNext = append(rt.edgeNext, rt.nodeEdgeHead[cur])
				rt.nodeEdgeHead[cur] = ei
				cur = nxtNode
			}
		}
	}
	rt.nodeRoutes[cur*5+method] = rid
}

func matchLowerKey(buf []int64, s, e int, target string) bool {
	if e-s != len(target) {
		return false
	}
	for i := 0; i < len(target); i++ {
		c := buf[s+i]
		if c >= 65 && c <= 90 {
			c += 32
		}
		if c != int64(target[i]) {
			return false
		}
	}
	return true
}

func main() {
	var rt trieRouter
	rt.newNode()
	rt.addRoute(1, []string{"health"}, 1)
	rt.addRoute(1, []string{"metrics"}, 2)
	rt.addRoute(1, []string{"api", "v1", "users", ":id"}, 3)
	rt.addRoute(2, []string{"api", "v1", "users"}, 4)
	rt.addRoute(1, []string{"api", "v1", "users", ":id", "posts", ":pid"}, 5)
	rt.addRoute(4, []string{"api", "v1", "users", ":id", "posts", ":pid"}, 6)
	rt.addRoute(1, []string{"api", "v1", "orders", ":oid", "items"}, 7)
	rt.addRoute(3, []string{"api", "v1", "orders", ":oid", "status"}, 8)
	rt.addRoute(1, []string{"api", "v1", "orgs", ":org", "repos", ":repo", "issues", ":num"}, 9)
	rt.addRoute(2, []string{"api", "v1", "orgs", ":org", "repos", ":repo", "issues"}, 10)
	rt.addRoute(1, []string{"api", "v2", "search"}, 11)
	rt.addRoute(1, []string{"static", "*"}, 12)

	users := []string{"alice", "bob42", "charlie", "dana_9", "eve", "frank01", "grace", "heidi"}
	orgs := []string{"xulang", "acme", "nebula", "kernel"}
	repos := []string{"xu", "bench", "runtime", "stdlib", "docs"}
	queries := []string{
		"page=2&limit=50&q=hello+world%21",
		"sort=desc&filter=open%2Factive&tag=v1%2E0",
		"q=%41%42%43+test%20case&offset=100",
		"",
		"lang=zh%2DCN&mode=fast&debug=1",
		"path=%2Fusr%2Fbin&retry=3",
	}

	reqBuf := make([]int64, 0, 65536)
	reqOff := make([]int, 0, 240)
	reqLen := make([]int, 0, 240)
	var rng int64 = 246813579
	for i := int64(0); i < 240; i++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		k := rng % 14
		rng = (rng*1103515245 + 12345) & 2147483647
		u := users[rng%8]
		rng = (rng*1103515245 + 12345) & 2147483647
		pid := 100 + (rng % 900)
		rng = (rng*1103515245 + 12345) & 2147483647
		oid := 10000 + (rng % 90000)
		rng = (rng*1103515245 + 12345) & 2147483647
		org := orgs[rng%4]
		rng = (rng*1103515245 + 12345) & 2147483647
		repo := repos[rng%5]
		rng = (rng*1103515245 + 12345) & 2147483647
		num := 1 + (rng % 500)
		rng = (rng*1103515245 + 12345) & 2147483647
		q := queries[rng%6]
		rng = (rng*1103515245 + 12345) & 2147483647
		cl := rng % 4096

		off := len(reqBuf)
		reqOff = append(reqOff, off)
		switch k {
		case 0:
			pushStr(&reqBuf, "GET /health")
		case 1:
			pushStr(&reqBuf, "GET /metrics")
		case 2:
			pushStr(&reqBuf, "GET /api/v1/users/")
			pushStr(&reqBuf, u)
		case 3:
			pushStr(&reqBuf, "POST /api/v1/users")
		case 4:
			pushStr(&reqBuf, "GET /api/v1/users/")
			pushStr(&reqBuf, u)
			pushStr(&reqBuf, "/posts/")
			pushInt(&reqBuf, pid)
		case 5:
			pushStr(&reqBuf, "DELETE /api/v1/users/")
			pushStr(&reqBuf, u)
			pushStr(&reqBuf, "/posts/")
			pushInt(&reqBuf, pid)
		case 6:
			pushStr(&reqBuf, "GET /api/v1/orders/")
			pushInt(&reqBuf, oid)
			pushStr(&reqBuf, "/items")
		case 7:
			pushStr(&reqBuf, "PUT /api/v1/orders/")
			pushInt(&reqBuf, oid)
			pushStr(&reqBuf, "/status")
		case 8:
			pushStr(&reqBuf, "GET /api/v1/orgs/")
			pushStr(&reqBuf, org)
			pushStr(&reqBuf, "/repos/")
			pushStr(&reqBuf, repo)
			pushStr(&reqBuf, "/issues/")
			pushInt(&reqBuf, num)
		case 9:
			pushStr(&reqBuf, "POST /api/v1/orgs/")
			pushStr(&reqBuf, org)
			pushStr(&reqBuf, "/repos/")
			pushStr(&reqBuf, repo)
			pushStr(&reqBuf, "/issues")
		case 10:
			pushStr(&reqBuf, "GET /api/v2/search")
		case 11:
			pushStr(&reqBuf, "GET /static/js/")
			pushStr(&reqBuf, repo)
			pushStr(&reqBuf, "/bundle_")
			pushInt(&reqBuf, pid)
			pushStr(&reqBuf, ".js")
		case 12:
			pushStr(&reqBuf, "GET /api/v1/unknown/")
			pushStr(&reqBuf, u)
			pushStr(&reqBuf, "/nope")
		default:
			pushStr(&reqBuf, "POST /health")
		}
		if len(q) > 0 {
			reqBuf = append(reqBuf, 63)
			pushStr(&reqBuf, q)
		}
		pushStr(&reqBuf, " HTTP/1.1\r\n")
		if (i % 3) != 0 {
			pushStr(&reqBuf, "Host: api.xulang.org\r\n")
		} else {
			pushStr(&reqBuf, "HOST: api.xulang.org\r\n")
		}
		pushStr(&reqBuf, "User-Agent: xu-bench/1.0\r\n")
		if (i & 1) == 0 {
			pushStr(&reqBuf, "Content-Length: ")
		} else {
			pushStr(&reqBuf, "content-length: ")
		}
		pushInt(&reqBuf, cl)
		pushStr(&reqBuf, "\r\nX-Request-Id: req-")
		pushInt(&reqBuf, i)
		reqBuf = append(reqBuf, 45)
		pushInt(&reqBuf, num)
		pushStr(&reqBuf, "\r\n\r\n")
		reqLen = append(reqLen, len(reqBuf)-off)
	}

	var segStarts [16]int
	var segEnds [16]int
	var matched int64
	var ck int64
	for rnd := 0; rnd < 500; rnd++ {
		for ri := 0; ri < 240; ri++ {
			rStart := reqOff[ri]
			rEnd := rStart + reqLen[ri]
			sp1 := rStart
			for reqBuf[sp1] != 32 {
				sp1++
			}
			mlen := sp1 - rStart
			var mc int64
			if mlen == 3 && reqBuf[rStart] == 71 {
				mc = 1
			} else if mlen == 4 && reqBuf[rStart] == 80 {
				mc = 2
			} else if mlen == 3 && reqBuf[rStart] == 80 {
				mc = 3
			} else if mlen == 6 && reqBuf[rStart] == 68 {
				mc = 4
			}
			tStart := sp1 + 1
			sp2 := tStart
			for reqBuf[sp2] != 32 {
				sp2++
			}
			crlf := sp2 + 1
			for !(reqBuf[crlf] == 13 && reqBuf[crlf+1] == 10) {
				crlf++
			}
			qpos := -1
			for p := tStart; p < sp2; p++ {
				if reqBuf[p] == 63 {
					qpos = p
					break
				}
			}
			pathEnd := sp2
			if qpos >= 0 {
				pathEnd = qpos
			}
			nSegs := 0
			sp := tStart
			for sp < pathEnd {
				for sp < pathEnd && reqBuf[sp] == 47 {
					sp++
				}
				if sp >= pathEnd {
					break
				}
				se := sp
				for se < pathEnd && reqBuf[se] != 47 {
					se++
				}
				segStarts[nSegs] = sp
				segEnds[nSegs] = se
				nSegs++
				sp = se
			}

			pos := crlf + 2
			var hdrCnt, contentLen, reqIDHash int64
			for pos < rEnd {
				lend := pos
				for lend+1 < rEnd && !(reqBuf[lend] == 13 && reqBuf[lend+1] == 10) {
					lend++
				}
				if lend == pos {
					break
				}
				col := pos
				for col < lend && reqBuf[col] != 58 {
					col++
				}
				vs := col + 1
				for vs < lend && (reqBuf[vs] == 32 || reqBuf[vs] == 9) {
					vs++
				}
				ve := lend
				for ve > vs && (reqBuf[ve-1] == 32 || reqBuf[ve-1] == 9) {
					ve--
				}
				hdrCnt++
				if matchLowerKey(reqBuf, pos, col, "content-length") {
					var v int64
					for vp := vs; vp < ve; vp++ {
						v = v*10 + (reqBuf[vp] - 48)
					}
					contentLen = v
				} else if matchLowerKey(reqBuf, pos, col, "x-request-id") {
					for vp := vs; vp < ve; vp++ {
						reqIDHash = (reqIDHash*31 + reqBuf[vp]) % modV
					}
				}
				pos = lend + 2
			}

			cur := 0
			var ph int64
			sj := 0
			dead := false
			for sj < nSegs {
				ss := segStarts[sj]
				sln := segEnds[sj] - ss
				e := rt.nodeEdgeHead[cur]
				nxt := -1
				for e >= 0 {
					if eqBufPool(reqBuf, ss, sln, rt.segPool, rt.edgeOff[e], rt.edgeLen[e]) {
						nxt = rt.edgeChild[e]
						break
					}
					e = rt.edgeNext[e]
				}
				if nxt >= 0 {
					cur = nxt
					sj++
				} else if rt.nodeParam[cur] >= 0 {
					ce := ss + sln
					for cp := ss; cp < ce; cp++ {
						ph = (ph*131 + reqBuf[cp]) % modV
					}
					cur = rt.nodeParam[cur]
					sj++
				} else if rt.nodeWild[cur] >= 0 {
					for sj < nSegs {
						ce := segEnds[sj]
						for cp := segStarts[sj]; cp < ce; cp++ {
							ph = (ph*131 + reqBuf[cp]) % modV
						}
						sj++
					}
					cur = rt.nodeWild[cur]
					break
				} else {
					dead = true
					break
				}
			}
			var routeID, paramHash int64
			if !dead {
				rid := int64(rt.nodeRoutes[cur*5+int(mc)])
				if rid > 0 {
					routeID = rid
					paramHash = ph
				}
			}
			var qHash int64
			if qpos >= 0 && qpos+1 < sp2 {
				qp := qpos + 1
				for qp < sp2 {
					qe := qp
					for qe < sp2 && reqBuf[qe] != 38 {
						qe++
					}
					eq := -1
					for qt := qp; qt < qe; qt++ {
						if reqBuf[qt] == 61 {
							eq = qt
							break
						}
					}
					if eq >= 0 {
						kh := decodePctHash(reqBuf, qp, eq)
						vh := decodePctHash(reqBuf, eq+1, qe)
						qHash = (qHash*257 + kh*17 + vh) % modV
					} else {
						qHash = (qHash*257 + decodePctHash(reqBuf, qp, qe)) % modV
					}
					qp = qe + 1
				}
			}
			if routeID > 0 {
				matched++
			}
			row := (routeID*1000003 + mc*97 + paramHash*7 + qHash*13 + contentLen*3 + hdrCnt*19 + reqIDHash) % modV
			ck = (ck*31 + row) % modV
		}
	}
	fmt.Println(matched)
	fmt.Println(ck)
}
