package main

import "fmt"

type HeapItem struct {
	freq int32
	nid  int32
}

type MinHeap struct {
	items [256]HeapItem
	size  int
}

func heapLess(a, b HeapItem) bool {
	if a.freq != b.freq {
		return a.freq < b.freq
	}
	return a.nid < b.nid
}

func (h *MinHeap) push(freq, nid int32) {
	i := h.size
	h.size++
	item := HeapItem{freq: freq, nid: nid}
	for i > 0 {
		p := (i - 1) / 2
		if heapLess(item, h.items[p]) {
			h.items[i] = h.items[p]
			i = p
		} else {
			break
		}
	}
	h.items[i] = item
}

func (h *MinHeap) pop() HeapItem {
	top := h.items[0]
	h.size--
	last := h.items[h.size]
	if h.size == 0 {
		return top
	}
	i := 0
	for i*2+1 < h.size {
		left := i*2 + 1
		right := left + 1
		best := left
		if right < h.size && heapLess(h.items[right], h.items[left]) {
			best = right
		}
		if heapLess(h.items[best], last) {
			h.items[i] = h.items[best]
			i = best
		} else {
			break
		}
	}
	h.items[i] = last
	return top
}

type HuffmanTree struct {
	nodesFreq  [256]int32
	nodesCh    [256]int32
	nodesLeft  [256]int32
	nodesRight [256]int32
	codes      [64]int32
	codeLens   [64]int32
}

func (t *HuffmanTree) getCodes(nid int, currCode, currLen int32) {
	if t.nodesLeft[nid] == -1 && t.nodesRight[nid] == -1 {
		ch := t.nodesCh[nid]
		t.codes[ch] = currCode
		t.codeLens[ch] = currLen
		return
	}
	t.getCodes(int(t.nodesLeft[nid]), (currCode<<1)|0, currLen+1)
	t.getCodes(int(t.nodesRight[nid]), (currCode<<1)|1, currLen+1)
}

func isqrt(n int64) int64 {
	if n <= 0 {
		return 0
	}
	x := n
	y := (x + 1) / 2
	for y < x {
		x = y
		y = (x + n/x) / 2
	}
	return x
}

func main() {
	var raw [20000]int32
	var freqs [64]int32
	var seed int64 = 123456789
	for i := 0; i < 20000; i++ {
		seed = (seed*1103515245 + 12345) & 0x7fffffff
		c := int32(isqrt(seed % 4096))
		raw[i] = c
		freqs[c]++
	}

	var tree HuffmanTree
	for i := 0; i < 256; i++ {
		tree.nodesLeft[i] = -1
		tree.nodesRight[i] = -1
	}

	var heap MinHeap
	nodeCount := 0

	for ch := 0; ch < 64; ch++ {
		if freqs[ch] > 0 {
			nid := int32(nodeCount)
			nodeCount++
			tree.nodesFreq[nid] = freqs[ch]
			tree.nodesCh[nid] = int32(ch)
			heap.push(freqs[ch], nid)
		}
	}

	for heap.size > 1 {
		item1 := heap.pop()
		item2 := heap.pop()
		pid := int32(nodeCount)
		nodeCount++
		tree.nodesFreq[pid] = item1.freq + item2.freq
		tree.nodesCh[pid] = -1
		tree.nodesLeft[pid] = item1.nid
		tree.nodesRight[pid] = item2.nid
		heap.push(tree.nodesFreq[pid], pid)
	}

	root := int(heap.pop().nid)
	tree.getCodes(root, 0, 0)

	var bitBuf []uint32
	bitCount := 0
	var currWord uint32 = 0
	currBits := 0

	for _, b := range raw {
		c := tree.codes[b]
		l := tree.codeLens[b]
		for bitIdx := l - 1; bitIdx >= 0; bitIdx-- {
			bit := uint32((c >> bitIdx) & 1)
			currWord = (currWord << 1) | bit
			currBits++
			if currBits == 32 {
				bitBuf = append(bitBuf, currWord)
				currWord = 0
				currBits = 0
			}
			bitCount++
		}
	}
	if currBits > 0 {
		currWord = currWord << (32 - currBits)
		bitBuf = append(bitBuf, currWord)
	}

	var totalChecksum int64 = 0
	for round := 0; round < 50; round++ {
		curNode := root
		var decodedSum int64 = 0
		for i := 0; i < bitCount; i++ {
			wordIdx := i / 32
			bitPos := 31 - (i % 32)
			bit := (bitBuf[wordIdx] >> bitPos) & 1
			if bit == 0 {
				curNode = int(tree.nodesLeft[curNode])
			} else {
				curNode = int(tree.nodesRight[curNode])
			}
			if tree.nodesLeft[curNode] == -1 && tree.nodesRight[curNode] == -1 {
				ch := int64(tree.nodesCh[curNode])
				decodedSum = (decodedSum*33 + ch) & 0x7fffffff
				curNode = root
			}
		}
		totalChecksum = (totalChecksum + decodedSum) & 0x7fffffff
	}

	fmt.Println(totalChecksum)
}
