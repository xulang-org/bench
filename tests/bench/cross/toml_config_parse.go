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
	var digs [16]int64
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

func push2d(buf *[]int64, v int64) {
	*buf = append(*buf, 48+(v/10), 48+(v%10))
}

func parseVal(doc []int64, start, n int) (int64, int) {
	p := start
	if doc[p] == 34 {
		p++
		var vh int64 = 17
		for p < n && doc[p] != 34 {
			ch := doc[p]
			if ch == 92 && p+1 < n {
				p++
				e := doc[p]
				if e == 110 {
					ch = 10
				} else if e == 116 {
					ch = 9
				} else if e == 34 {
					ch = 34
				} else if e == 92 {
					ch = 92
				} else {
					ch = e
				}
			}
			vh = (vh*131 + ch) % modV
			p++
		}
		if p < n {
			p++
		}
		return vh, p
	} else if doc[p] == 91 {
		p++
		var ah int64 = 29
		for p < n {
			for p < n && (doc[p] == 32 || doc[p] == 9 || doc[p] == 44) {
				p++
			}
			if p >= n || doc[p] == 93 {
				if p < n {
					p++
				}
				break
			}
			ev, np := parseVal(doc, p, n)
			ah = (ah*257 + ev) % modV
			p = np
		}
		return ah, p
	} else if doc[p] == 116 {
		return 1, p + 4
	} else if doc[p] == 102 {
		return 0, p + 5
	}
	neg := false
	if doc[p] == 45 {
		neg = true
		p++
	}
	var v int64
	for p < n && ((doc[p] >= 48 && doc[p] <= 57) || doc[p] == 95) {
		if doc[p] != 95 {
			v = v*10 + (doc[p] - 48)
		}
		p++
	}
	if neg {
		v = -v
	}
	v %= modV
	if v < 0 {
		v += modV
	}
	return v, p
}

func main() {
	doc := make([]int64, 0, 16384)
	pushStr(&doc, "# Auto-generated microservice configuration\n")
	for s := int64(0); s < 48; s++ {
		pushStr(&doc, "\n[svc_")
		push2d(&doc, s)
		pushStr(&doc, "]\n")
		pushStr(&doc, "name = \"worker-")
		push2d(&doc, s)
		pushStr(&doc, "\\tprod\\n\\\"v")
		pushInt(&doc, s%5)
		pushStr(&doc, "\\\"\" # inline comment\n")
		pushStr(&doc, "port = ")
		pushInt(&doc, 8000+s*10)
		doc = append(doc, 10)
		pushStr(&doc, "max_conn = ")
		pushInt(&doc, 1000+(s%7)*500)
		doc = append(doc, 95)
		pushInt(&doc, 100+s)
		doc = append(doc, 10)
		if (s & 1) == 0 {
			pushStr(&doc, "enabled = true\n")
		} else {
			pushStr(&doc, "enabled = false\n")
		}
		if (s % 9) == 0 {
			pushStr(&doc, "timeout_ms = -")
			pushInt(&doc, 50+s*3)
			doc = append(doc, 10)
		} else {
			pushStr(&doc, "timeout_ms = ")
			pushInt(&doc, 250+s*15)
			doc = append(doc, 10)
		}
		pushStr(&doc, "retries = [")
		pushInt(&doc, 1+(s%3))
		pushStr(&doc, ", ")
		pushInt(&doc, 2+(s%5))
		pushStr(&doc, ", ")
		pushInt(&doc, 4+(s%7))
		pushStr(&doc, ", ")
		pushInt(&doc, 8+(s%11))
		pushStr(&doc, "]\n")
		pushStr(&doc, "endpoints = [\"/v1/s")
		pushInt(&doc, s)
		pushStr(&doc, "\", \"/health\\t")
		pushInt(&doc, s)
		pushStr(&doc, "\", \"/metrics\"]\n")
	}

	n := len(doc)
	var totalEntries, ck int64
	for rnd := int64(0); rnd < 1000; rnd++ {
		pos := 0
		var secHash, entries, roundCk int64
		for pos < n {
			for pos < n && (doc[pos] == 32 || doc[pos] == 9 || doc[pos] == 10 || doc[pos] == 13) {
				pos++
			}
			if pos >= n {
				break
			}
			c := doc[pos]
			if c == 35 {
				for pos < n && doc[pos] != 10 {
					pos++
				}
				continue
			}
			if c == 91 {
				pos++
				var sh int64
				for pos < n && doc[pos] != 93 {
					sh = (sh*131 + doc[pos]) % modV
					pos++
				}
				if pos < n {
					pos++
				}
				secHash = sh
				for pos < n && doc[pos] != 10 {
					pos++
				}
				continue
			}
			kh := secHash
			for pos < n && doc[pos] != 61 && doc[pos] != 32 && doc[pos] != 9 && doc[pos] != 10 {
				kh = (kh*131 + doc[pos]) % modV
				pos++
			}
			for pos < n && (doc[pos] == 32 || doc[pos] == 9) {
				pos++
			}
			if pos < n && doc[pos] == 61 {
				pos++
			}
			for pos < n && (doc[pos] == 32 || doc[pos] == 9) {
				pos++
			}
			vh, np := parseVal(doc, pos, n)
			pos = np
			for pos < n && doc[pos] != 10 {
				pos++
			}
			entries++
			roundCk = (roundCk*31 + (kh*7+vh+rnd)%modV) % modV
		}
		totalEntries += entries
		ck = (ck*37 + roundCk) % modV
	}
	fmt.Println(totalEntries)
	fmt.Println(ck)
}
