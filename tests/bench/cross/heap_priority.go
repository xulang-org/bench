package main

import (
	"container/heap"
	"fmt"
)

type IntHeap []int64

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)        { *h = append(*h, x.(int64)) }
func (h *IntHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

func main() {
	h := &IntHeap{}
	heap.Init(h)
	var seed int64 = 123456789
	var checksum int64 = 0

	for i := 0; i < 200000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		heap.Push(h, seed)
	}

	for i := 0; i < 100000; i++ {
		v := heap.Pop(h).(int64)
		checksum = (checksum*31 + v) % 1000000007
	}

	for i := 0; i < 100000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		heap.Push(h, seed)
	}

	for h.Len() > 0 {
		v := heap.Pop(h).(int64)
		checksum = (checksum*31 + v) % 1000000007
	}

	fmt.Println(checksum)
}
