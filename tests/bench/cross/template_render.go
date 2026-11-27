package main

import "fmt"

const modV int64 = 1000000007

func toBytes(s string) []int64 {
	b := make([]int64, len(s))
	for i := 0; i < len(s); i++ {
		b[i] = int64(s[i])
	}
	return b
}

func emitRaw(out *[]int64, s []int64, start, ln int) {
	for i := 0; i < ln; i++ {
		*out = append(*out, s[start+i])
	}
}

func emitEsc(out *[]int64, s []int64) {
	for i := 0; i < len(s); i++ {
		ch := s[i]
		if ch == 38 {
			*out = append(*out, 38, 97, 109, 112, 59)
		} else if ch == 60 {
			*out = append(*out, 38, 108, 116, 59)
		} else if ch == 62 {
			*out = append(*out, 38, 103, 116, 59)
		} else if ch == 34 {
			*out = append(*out, 38, 113, 117, 111, 116, 59)
		} else if ch == 39 {
			*out = append(*out, 38, 35, 51, 57, 59)
		} else {
			*out = append(*out, ch)
		}
	}
}

func matchBytes(src []int64, s, e int, pat string) bool {
	a, b := s, e
	for a < b && (src[a] == 32 || src[a] == 9) {
		a++
	}
	for b > a && (src[b-1] == 32 || src[b-1] == 9) {
		b--
	}
	if b-a != len(pat) {
		return false
	}
	for i := 0; i < len(pat); i++ {
		if src[a+i] != int64(pat[i]) {
			return false
		}
	}
	return true
}

func varID(src []int64, s, e int) int {
	if matchBytes(src, s, e, "title") {
		return 0
	}
	if matchBytes(src, s, e, "badge") {
		return 1
	}
	if matchBytes(src, s, e, "name") {
		return 2
	}
	if matchBytes(src, s, e, "desc") {
		return 3
	}
	return -1
}

func main() {
	tmpl := toBytes("<div class=\"card\"><h1>{{title}}</h1>{{{badge}}}<ul>{%for item%}<li class=\"{%if featured%}hot{%else%}std{%endif%}\"><span>{{name}}</span><em>{{desc}}</em></li>{%endfor%}</ul></div>")
	tlen := len(tmpl)

	titles := [][]int64{
		toBytes("Xu <Fast> & Safe"),
		toBytes("Bench \"Suite\" 'v1'"),
		toBytes("Release & Notes <2026>"),
		toBytes("Core / Engine"),
	}
	badges := [][]int64{
		toBytes("<b>PRO</b>"),
		toBytes("<i>LTS</i>"),
		toBytes("<span>NEW</span>"),
		toBytes("<b>OK</b>"),
	}
	names := [][]int64{
		toBytes("Item <alpha> & 1"),
		toBytes("Widget \"beta\""),
		toBytes("Node 'gamma' > 0"),
		toBytes("Cache & Pool"),
		toBytes("Router <v2>"),
		toBytes("Codec \"lz4\""),
		toBytes("Parser 'ast'"),
		toBytes("Engine <core>"),
	}
	descs := [][]int64{
		toBytes("a < b && c > d"),
		toBytes("quote \"here\" & 'there'"),
		toBytes("plain fast path"),
		toBytes("x & y < z"),
	}

	opKind := make([]int, 0, 64)
	opA := make([]int, 0, 64)
	opB := make([]int, 0, 64)
	var forStack, ifStack, elseStack [8]int
	out := make([]int64, 0, 2048)

	var totalBytes, ck int64
	for rnd := 0; rnd < 400; rnd++ {
		opKind = opKind[:0]
		opA = opA[:0]
		opB = opB[:0]
		forSP, ifSP := 0, 0
		pos := 0
		for pos < tlen {
			np := pos
			for np+1 < tlen && !(tmpl[np] == 123 && (tmpl[np+1] == 123 || tmpl[np+1] == 37)) {
				np++
			}
			if np+1 >= tlen {
				np = tlen
			}
			if np > pos {
				opKind = append(opKind, 0)
				opA = append(opA, pos)
				opB = append(opB, np-pos)
				pos = np
			}
			if pos >= tlen {
				break
			}
			if tmpl[pos+1] == 123 {
				if pos+2 < tlen && tmpl[pos+2] == 123 {
					end := pos + 3
					for !(tmpl[end] == 125 && tmpl[end+1] == 125 && tmpl[end+2] == 125) {
						end++
					}
					opKind = append(opKind, 2)
					opA = append(opA, varID(tmpl, pos+3, end))
					opB = append(opB, 0)
					pos = end + 3
				} else {
					end := pos + 2
					for !(tmpl[end] == 125 && tmpl[end+1] == 125) {
						end++
					}
					opKind = append(opKind, 1)
					opA = append(opA, varID(tmpl, pos+2, end))
					opB = append(opB, 0)
					pos = end + 2
				}
			} else {
				end := pos + 2
				for !(tmpl[end] == 37 && tmpl[end+1] == 125) {
					end++
				}
				ts := pos + 2
				if matchBytes(tmpl, ts, end, "for item") {
					forStack[forSP] = len(opKind)
					forSP++
					opKind = append(opKind, 3)
					opA = append(opA, 0)
					opB = append(opB, 0)
				} else if matchBytes(tmpl, ts, end, "endfor") {
					forSP--
					fidx := forStack[forSP]
					opKind = append(opKind, 4)
					opA = append(opA, fidx+1)
					opB = append(opB, 0)
					opA[fidx] = len(opKind)
				} else if matchBytes(tmpl, ts, end, "if featured") {
					ifStack[ifSP] = len(opKind)
					elseStack[ifSP] = -1
					ifSP++
					opKind = append(opKind, 5)
					opA = append(opA, 0)
					opB = append(opB, 0)
				} else if matchBytes(tmpl, ts, end, "else") {
					eidx := len(opKind)
					opKind = append(opKind, 6)
					opA = append(opA, 0)
					opB = append(opB, 0)
					iidx := ifStack[ifSP-1]
					opA[iidx] = eidx + 1
					elseStack[ifSP-1] = eidx
				} else if matchBytes(tmpl, ts, end, "endif") {
					ifSP--
					iidx := ifStack[ifSP]
					eidx := elseStack[ifSP]
					if eidx >= 0 {
						opA[eidx] = len(opKind)
					} else {
						opA[iidx] = len(opKind)
					}
					opKind = append(opKind, 7)
					opA = append(opA, 0)
					opB = append(opB, 0)
				}
				pos = end + 2
			}
		}

		nOps := len(opKind)
		for page := 0; page < 25; page++ {
			titleV := titles[(rnd+page)&3]
			badgeV := badges[(rnd*3+page)&3]
			out = out[:0]
			pc := 0
			itemIdx := 0
			itemCnt := 12
			for pc < nOps {
				op := opKind[pc]
				a := opA[pc]
				if op == 0 {
					emitRaw(&out, tmpl, a, opB[pc])
					pc++
				} else if op == 1 {
					if a == 0 {
						emitEsc(&out, titleV)
					} else if a == 2 {
						emitEsc(&out, names[(page+itemIdx+rnd)&7])
					} else if a == 3 {
						emitEsc(&out, descs[(page*3+itemIdx+rnd)&3])
					}
					pc++
				} else if op == 2 {
					if a == 1 {
						emitRaw(&out, badgeV, 0, len(badgeV))
					}
					pc++
				} else if op == 3 {
					if itemCnt == 0 {
						pc = a
					} else {
						itemIdx = 0
						pc++
					}
				} else if op == 4 {
					itemIdx++
					if itemIdx < itemCnt {
						pc = a
					} else {
						pc++
					}
				} else if op == 5 {
					if ((rnd + page + itemIdx) % 3) == 0 {
						pc++
					} else {
						pc = a
					}
				} else if op == 6 {
					pc = a
				} else {
					pc++
				}
			}
			totalBytes += int64(len(out))
			var h int64
			for oi := 0; oi < len(out); oi++ {
				h = (h*131 + out[oi]) % modV
			}
			ck = (ck*31 + h) % modV
		}
	}
	fmt.Println(totalBytes)
	fmt.Println(ck)
}
