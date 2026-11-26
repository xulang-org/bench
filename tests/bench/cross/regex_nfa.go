package main

import "fmt"

type NfaPool struct {
	stKind  []int64
	stOut1  []int64
	stOut2  []int64
	pSt     []int64
	pWh     []int64
	pNext   []int64
	startSt []int64
	matchSt []int64
}

func prec(op int64) int64 {
	if op == -3 {
		return 1
	}
	if op == -2 {
		return 2
	}
	if op == -4 || op == -5 || op == -6 {
		return 3
	}
	return 0
}

func (nfa *NfaPool) addSt(k, o1, o2 int64) int64 {
	idx := int64(len(nfa.stKind))
	nfa.stKind = append(nfa.stKind, k)
	nfa.stOut1 = append(nfa.stOut1, o1)
	nfa.stOut2 = append(nfa.stOut2, o2)
	return idx
}

func (nfa *NfaPool) newPatch(si, wh int64) int64 {
	idx := int64(len(nfa.pSt))
	nfa.pSt = append(nfa.pSt, si)
	nfa.pWh = append(nfa.pWh, wh)
	nfa.pNext = append(nfa.pNext, -1)
	return idx
}

func (nfa *NfaPool) appendPatch(h1, t1, h2 int64) int64 {
	if h1 == -1 {
		return h2
	}
	if h2 == -1 {
		return h1
	}
	nfa.pNext[t1] = h2
	return h1
}

func (nfa *NfaPool) applyPatch(head, target int64) {
	cur := head
	for cur != -1 {
		if nfa.pWh[cur] == 1 {
			nfa.stOut1[nfa.pSt[cur]] = target
		} else {
			nfa.stOut2[nfa.pSt[cur]] = target
		}
		cur = nfa.pNext[cur]
	}
}

func (nfa *NfaPool) compilePattern(pat string) {
	toks := make([]int64, 0, len(pat)*2)
	prevAtom := false
	for i := 0; i < len(pat); i++ {
		c := int64(pat[i])
		if c == 40 {
			if prevAtom {
				toks = append(toks, -2)
			}
			toks = append(toks, -10)
			prevAtom = false
		} else if c == 41 {
			toks = append(toks, -11)
			prevAtom = true
		} else if c == 124 {
			toks = append(toks, -3)
			prevAtom = false
		} else if c == 42 {
			toks = append(toks, -4)
			prevAtom = true
		} else if c == 43 {
			toks = append(toks, -5)
			prevAtom = true
		} else if c == 63 {
			toks = append(toks, -6)
			prevAtom = true
		} else {
			if prevAtom {
				toks = append(toks, -2)
			}
			if c == 46 {
				toks = append(toks, -1)
			} else {
				toks = append(toks, c)
			}
			prevAtom = true
		}
	}

	post := make([]int64, 0, len(toks))
	ops := make([]int64, 0, len(toks))
	for i := 0; i < len(toks); i++ {
		t := toks[i]
		if t >= 0 || t == -1 {
			post = append(post, t)
		} else if t == -10 {
			ops = append(ops, t)
		} else if t == -11 {
			for len(ops) > 0 && ops[len(ops)-1] != -10 {
				post = append(post, ops[len(ops)-1])
				ops = ops[:len(ops)-1]
			}
			if len(ops) > 0 {
				ops = ops[:len(ops)-1]
			}
		} else {
			pt := prec(t)
			for len(ops) > 0 && ops[len(ops)-1] != -10 && prec(ops[len(ops)-1]) >= pt {
				post = append(post, ops[len(ops)-1])
				ops = ops[:len(ops)-1]
			}
			ops = append(ops, t)
		}
	}
	for len(ops) > 0 {
		post = append(post, ops[len(ops)-1])
		ops = ops[:len(ops)-1]
	}

	fs := make([]int64, 0, len(post))
	fh := make([]int64, 0, len(post))
	ft := make([]int64, 0, len(post))
	for i := 0; i < len(post); i++ {
		t := post[i]
		if t >= 0 || t == -1 {
			s := nfa.addSt(t, -1, -1)
			p := nfa.newPatch(s, 1)
			fs = append(fs, s)
			fh = append(fh, p)
			ft = append(ft, p)
		} else if t == -2 {
			n := len(fs)
			s2, h2, t2 := fs[n-1], fh[n-1], ft[n-1]
			s1, h1 := fs[n-2], fh[n-2]
			fs, fh, ft = fs[:n-2], fh[:n-2], ft[:n-2]
			nfa.applyPatch(h1, s2)
			fs = append(fs, s1)
			fh = append(fh, h2)
			ft = append(ft, t2)
		} else if t == -3 {
			n := len(fs)
			s2, h2, t2 := fs[n-1], fh[n-1], ft[n-1]
			s1, h1, t1 := fs[n-2], fh[n-2], ft[n-2]
			fs, fh, ft = fs[:n-2], fh[:n-2], ft[:n-2]
			s := nfa.addSt(-2, s1, s2)
			hn := nfa.appendPatch(h1, t1, h2)
			fs = append(fs, s)
			fh = append(fh, hn)
			ft = append(ft, t2)
		} else if t == -6 {
			n := len(fs)
			s1, h1, t1 := fs[n-1], fh[n-1], ft[n-1]
			fs, fh, ft = fs[:n-1], fh[:n-1], ft[:n-1]
			s := nfa.addSt(-2, s1, -1)
			p := nfa.newPatch(s, 2)
			hn := nfa.appendPatch(h1, t1, p)
			fs = append(fs, s)
			fh = append(fh, hn)
			ft = append(ft, p)
		} else if t == -4 {
			n := len(fs)
			s1, h1 := fs[n-1], fh[n-1]
			fs, fh, ft = fs[:n-1], fh[:n-1], ft[:n-1]
			s := nfa.addSt(-2, s1, -1)
			nfa.applyPatch(h1, s)
			p := nfa.newPatch(s, 2)
			fs = append(fs, s)
			fh = append(fh, p)
			ft = append(ft, p)
		} else if t == -5 {
			n := len(fs)
			s1, h1 := fs[n-1], fh[n-1]
			fs, fh, ft = fs[:n-1], fh[:n-1], ft[:n-1]
			s := nfa.addSt(-2, s1, -1)
			nfa.applyPatch(h1, s)
			p := nfa.newPatch(s, 2)
			fs = append(fs, s1)
			fh = append(fh, p)
			ft = append(ft, p)
		}
	}
	m := nfa.addSt(-3, -1, -1)
	nfa.applyPatch(fh[len(fh)-1], m)
	nfa.startSt = append(nfa.startSt, fs[len(fs)-1])
	nfa.matchSt = append(nfa.matchSt, m)
}

func addState(nfa *NfaPool, vis, lst []int64, lstLen *int64, stk []int64, s, gen int64) {
	sp := 0
	stk[sp] = s
	sp++
	for sp > 0 {
		sp--
		u := stk[sp]
		if u < 0 || vis[u] == gen {
			continue
		}
		vis[u] = gen
		if nfa.stKind[u] == -2 {
			stk[sp] = nfa.stOut2[u]
			sp++
			stk[sp] = nfa.stOut1[u]
			sp++
		} else {
			lst[*lstLen] = u
			*lstLen++
		}
	}
}

func nfaSearch(nfa *NfaPool, start, matchSt int64, text []int64, tlen int64, vis []int64, genBox *int64, cur, nxt, stk []int64) bool {
	gen := *genBox + 1
	var curLen int64
	addState(nfa, vis, cur, &curLen, stk, start, gen)
	if vis[matchSt] == gen {
		*genBox = gen
		return true
	}
	for i := int64(0); i < tlen; i++ {
		c := text[i]
		gen++
		var nxtLen int64
		for j := int64(0); j < curLen; j++ {
			u := cur[j]
			k := nfa.stKind[u]
			if k == c || k == -1 {
				addState(nfa, vis, nxt, &nxtLen, stk, nfa.stOut1[u], gen)
			}
		}
		addState(nfa, vis, nxt, &nxtLen, stk, start, gen)
		if vis[matchSt] == gen {
			*genBox = gen
			return true
		}
		for k := int64(0); k < nxtLen; k++ {
			cur[k] = nxt[k]
		}
		curLen = nxtLen
	}
	*genBox = gen
	return false
}

func main() {
	var nfa NfaPool
	patterns := []string{"ab+c", "(a|ab)*cd", "x..y*z", "(foo|bar)+baz", "a(b|c)+d?", "k(m|n)*p+q"}
	for i := 0; i < len(patterns); i++ {
		nfa.compilePattern(patterns[i])
	}
	tokens := []string{
		"ab", "bc", "cd", "foo", "bar", "baz", "xyz", "x12y", "yz", "kmpq",
		"knppq", "abc", "abbc", "abd", "acd", "a", "b", "c", "d", "x",
		"y", "z", "k", "m", "n", "p", "q", "0", "_", "-",
	}

	nSt := len(nfa.stKind)
	vis := make([]int64, nSt)
	cur := make([]int64, nSt)
	nxt := make([]int64, nSt)
	stk := make([]int64, nSt*2)
	var genBox int64
	line := make([]int64, 256)

	var rng int64 = 2463534242
	var matches int64
	var weighted int64
	for li := int64(0); li < 6000; li++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		nTok := 8 + (rng % 10)
		var tlen int64
		for ti := int64(0); ti < nTok; ti++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			tok := tokens[rng%30]
			for ci := 0; ci < len(tok); ci++ {
				line[tlen] = int64(tok[ci])
				tlen++
			}
		}
		for pi := 0; pi < 6; pi++ {
			if nfaSearch(&nfa, nfa.startSt[pi], nfa.matchSt[pi], line, tlen, vis, &genBox, cur, nxt, stk) {
				matches++
				weighted = (weighted + (li+1)*int64(pi+1)) % 1000000007
			}
		}
	}
	fmt.Println(matches)
	fmt.Println(weighted)
}
