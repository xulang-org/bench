package main

import "fmt"

const modV int64 = 1000000007

func ilog2X1000(x int64, lut []int64) int64 {
	var b int64
	t := x
	for t >= 2 {
		t >>= 1
		b++
	}
	frac := ((x - (int64(1) << b)) << 4) >> b
	return b*1000 + lut[frac]
}

func main() {
	const nDocs = 6000
	const vocab = 2048
	var rng int64 = 777654321

	lut := []int64{0, 87, 170, 248, 322, 392, 459, 524, 585, 644, 700, 755, 807, 858, 907, 954}
	docLen := make([]int64, nDocs)
	scores := make([]int64, nDocs)
	stamp := make([]int64, nDocs)
	touched := make([]int, nDocs)

	df := make([]int64, vocab)
	postOff := make([]int, vocab+1)
	cur := make([]int, vocab)
	idf := make([]int64, vocab)

	rawD := make([]int, 0, nDocs*40)
	rawT := make([]int, 0, nDocs*40)
	rawF := make([]int64, 0, nDocs*40)
	tmp := make([]int, 64)

	var totalLen int64
	for d := 0; d < nDocs; d++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		dl := int(24 + (rng % 32))
		docLen[d] = int64(dl)
		totalLen += int64(dl)
		for j := 0; j < dl; j++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			var term int
			if (rng % 3) == 0 {
				rng = (rng*1103515245 + 12345) & 2147483647
				term = int(rng % 64)
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				term = 64 + int(rng%(vocab-64))
			}
			tmp[j] = term
		}
		for j := 1; j < dl; j++ {
			key := tmp[j]
			p := j - 1
			for p >= 0 && tmp[p] > key {
				tmp[p+1] = tmp[p]
				p--
			}
			tmp[p+1] = key
		}
		j := 0
		for j < dl {
			term := tmp[j]
			cnt := 1
			for j+cnt < dl && tmp[j+cnt] == term {
				cnt++
			}
			df[term]++
			rawD = append(rawD, d)
			rawT = append(rawT, term)
			rawF = append(rawF, int64(cnt))
			j += cnt
		}
	}

	for t := 0; t < vocab; t++ {
		postOff[t+1] = postOff[t] + int(df[t])
		cur[t] = postOff[t]
	}
	totalP := postOff[vocab]
	postDoc := make([]int, totalP)
	postTf := make([]int64, totalP)
	for i := 0; i < len(rawD); i++ {
		term := rawT[i]
		idx := cur[term]
		postDoc[idx] = rawD[i]
		postTf[idx] = rawF[i]
		cur[term] = idx + 1
	}

	for t := 0; t < vocab; t++ {
		if df[t] > 0 {
			ratioX1024 := (((int64(nDocs)-df[t])*2+1)*1024)/(df[t]*2+1) + 1024
			idf[t] = ilog2X1000(ratioX1024, lut) - 10000
		}
	}

	avgdlX100 := (totalLen * 100) / int64(nDocs)
	dlNorm := make([]int64, nDocs)
	for d := 0; d < nDocs; d++ {
		dlNorm[d] = 250 + (750*docLen[d]*100)/avgdlX100
	}

	qterms := make([]int, 5)
	topD := make([]int, 10)
	topS := make([]int64, 10)

	var totalHits int64
	var ck int64
	for q := int64(1); q <= 2000; q++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		qn := 3 + int(rng%3)
		rng = (rng*1103515245 + 12345) & 2147483647
		qterms[0] = int(rng % 64)
		for j := 1; j < qn; j++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			qterms[j] = 64 + int(rng%(vocab-64))
		}
		tCnt := 0
		for j := 0; j < qn; j++ {
			term := qterms[j]
			it := idf[term]
			if it > 0 {
				pend := postOff[term+1]
				for p := postOff[term]; p < pend; p++ {
					docI := postDoc[p]
					tf := postTf[p]
					sc := (it * tf * 2200) / (tf*1000 + (12*dlNorm[docI])/10)
					if stamp[docI] != q {
						stamp[docI] = q
						scores[docI] = sc
						touched[tCnt] = docI
						tCnt++
					} else {
						scores[docI] += sc
					}
				}
			}
		}
		kFound := 0
		for i := 0; i < tCnt; i++ {
			docI := touched[i]
			s := scores[docI]
			if kFound < 10 || s > topS[9] || (s == topS[9] && docI < topD[9]) {
				pos := 9
				if kFound < 10 {
					pos = kFound
					kFound++
				}
				for pos > 0 && (s > topS[pos-1] || (s == topS[pos-1] && docI < topD[pos-1])) {
					topS[pos] = topS[pos-1]
					topD[pos] = topD[pos-1]
					pos--
				}
				topS[pos] = s
				topD[pos] = docI
			}
		}
		totalHits += int64(kFound)
		for r := 0; r < kFound; r++ {
			ck = (ck*31 + int64(topD[r])*10007 + topS[r]) % modV
		}
	}

	fmt.Printf("%d\n%d\n", totalHits, ck)
}
