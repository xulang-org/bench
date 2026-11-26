package main

import "fmt"

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
	var digs [32]int64
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

func buildJsonPayload() []int64 {
	buf := make([]int64, 0, 8192)
	pushStr(&buf, "{\"meta\":{\"id\":1000,\"active\":true,\"deleted\":false,\"note\":null,\"ratio\":-12.375e2},\"records\":[")
	for r := int64(0); r < 48; r++ {
		if r > 0 {
			buf = append(buf, 44)
		}
		v0 := (r*37+11)%997 - 400
		v1 := (r*53 + 7) % 503
		v2 := -(r*19 + 3)
		v3 := r*7 + 1
		pushStr(&buf, "{\"id\":")
		pushInt(&buf, r)
		pushStr(&buf, ",\"name\":\"item_")
		pushInt(&buf, r)
		buf = append(buf, 92, 34, 118, 92, 92, 110, 34)
		if r%2 == 0 {
			pushStr(&buf, ",\"ok\":true,\"err\":null,\"vals\":[")
		} else {
			pushStr(&buf, ",\"ok\":false,\"err\":null,\"vals\":[")
		}
		pushInt(&buf, v0)
		buf = append(buf, 44)
		pushInt(&buf, v1)
		buf = append(buf, 46, 48+(r%10), 44)
		pushInt(&buf, v2)
		pushStr(&buf, "e1,")
		pushInt(&buf, v3)
		pushStr(&buf, "],\"cfg\":{\"a\":")
		pushInt(&buf, r*3+1)
		pushStr(&buf, ",\"b\":\"tag_")
		buf = append(buf, 48+(r%7))
		pushStr(&buf, "\",\"c\":[true,false,null]}}")
	}
	pushStr(&buf, "]}")
	return buf
}

type JsonParser struct {
	buf        []int64
	pos        int64
	n          int64
	kind       []int64
	val        []int64
	firstChild []int64
	nextSib    []int64
}

func (p *JsonParser) newNode(k, v int64) int64 {
	idx := int64(len(p.kind))
	p.kind = append(p.kind, k)
	p.val = append(p.val, v)
	p.firstChild = append(p.firstChild, -1)
	p.nextSib = append(p.nextSib, -1)
	return idx
}

func (p *JsonParser) skipWs() {
	for p.pos < p.n {
		c := p.buf[p.pos]
		if c == 32 || c == 9 || c == 10 || c == 13 {
			p.pos++
		} else {
			break
		}
	}
}

func (p *JsonParser) parseStringHash() int64 {
	p.pos++
	var h int64
	for p.pos < p.n {
		c := p.buf[p.pos]
		p.pos++
		if c == 34 {
			return h
		}
		if c == 92 {
			if p.pos < p.n {
				ec := p.buf[p.pos]
				p.pos++
				h = (h*131 + ec + 256) % 1000000007
			}
		} else {
			h = (h*131 + c) % 1000000007
		}
	}
	return h
}

func (p *JsonParser) parseNumberHash() int64 {
	var h int64
	if p.pos < p.n && p.buf[p.pos] == 45 {
		h = 45
		p.pos++
	}
	for p.pos < p.n && p.buf[p.pos] >= 48 && p.buf[p.pos] <= 57 {
		h = (h*131 + p.buf[p.pos]) % 1000000007
		p.pos++
	}
	if p.pos < p.n && p.buf[p.pos] == 46 {
		h = (h*131 + 46) % 1000000007
		p.pos++
		for p.pos < p.n && p.buf[p.pos] >= 48 && p.buf[p.pos] <= 57 {
			h = (h*131 + p.buf[p.pos]) % 1000000007
			p.pos++
		}
	}
	if p.pos < p.n && (p.buf[p.pos] == 101 || p.buf[p.pos] == 69) {
		h = (h*131 + 101) % 1000000007
		p.pos++
		if p.pos < p.n && (p.buf[p.pos] == 43 || p.buf[p.pos] == 45) {
			h = (h*131 + p.buf[p.pos]) % 1000000007
			p.pos++
		}
		for p.pos < p.n && p.buf[p.pos] >= 48 && p.buf[p.pos] <= 57 {
			h = (h*131 + p.buf[p.pos]) % 1000000007
			p.pos++
		}
	}
	return h
}

func (p *JsonParser) parseVal() int64 {
	p.skipWs()
	c := p.buf[p.pos]
	if c == 123 {
		p.pos++
		node := p.newNode(6, 0)
		p.skipWs()
		if p.pos < p.n && p.buf[p.pos] == 125 {
			p.pos++
			return node
		}
		var tail int64 = -1
		var cnt int64
		for p.pos < p.n {
			p.skipWs()
			kh := p.parseStringHash()
			p.skipWs()
			p.pos++
			child := p.parseVal()
			p.val[node] = (p.val[node]*31 + kh) % 1000000007
			if tail == -1 {
				p.firstChild[node] = child
			} else {
				p.nextSib[tail] = child
			}
			tail = child
			cnt++
			p.skipWs()
			if p.pos < p.n && p.buf[p.pos] == 44 {
				p.pos++
			} else {
				p.pos++
				break
			}
		}
		p.val[node] = (p.val[node]*31 + cnt) % 1000000007
		return node
	} else if c == 91 {
		p.pos++
		node := p.newNode(5, 0)
		p.skipWs()
		if p.pos < p.n && p.buf[p.pos] == 93 {
			p.pos++
			return node
		}
		var tail int64 = -1
		var cnt int64
		for p.pos < p.n {
			child := p.parseVal()
			if tail == -1 {
				p.firstChild[node] = child
			} else {
				p.nextSib[tail] = child
			}
			tail = child
			cnt++
			p.skipWs()
			if p.pos < p.n && p.buf[p.pos] == 44 {
				p.pos++
			} else {
				p.pos++
				break
			}
		}
		p.val[node] = cnt
		return node
	} else if c == 34 {
		return p.newNode(4, p.parseStringHash())
	} else if c == 116 {
		p.pos += 4
		return p.newNode(2, 1)
	} else if c == 102 {
		p.pos += 5
		return p.newNode(2, 0)
	} else if c == 110 {
		p.pos += 4
		return p.newNode(1, 0)
	}
	return p.newNode(3, p.parseNumberHash())
}

func (p *JsonParser) walk(u int64) int64 {
	h := (p.kind[u]*1000003 + p.val[u]) % 1000000007
	ch := p.firstChild[u]
	for ch != -1 {
		h = (h*31 + p.walk(ch)) % 1000000007
		ch = p.nextSib[ch]
	}
	return h
}

func main() {
	buf := buildJsonPayload()
	n := int64(len(buf))
	var totNodes int64
	var totHash int64
	for r := int64(0); r < 400; r++ {
		v := 1000 + r
		buf[14] = 48 + (v/1000)%10
		buf[15] = 48 + (v/100)%10
		buf[16] = 48 + (v/10)%10
		buf[17] = 48 + v%10
		p := JsonParser{
			buf:        buf,
			pos:        0,
			n:          n,
			kind:       make([]int64, 0, 1024),
			val:        make([]int64, 0, 1024),
			firstChild: make([]int64, 0, 1024),
			nextSib:    make([]int64, 0, 1024),
		}
		root := p.parseVal()
		totNodes += int64(len(p.kind))
		totHash = (totHash + p.walk(root)) % 1000000007
	}
	fmt.Println(totNodes)
	fmt.Println(totHash)
}
