package main

import (
	"fmt"
)

type Node struct {
	key  int64
	val  int64
	prev int32
	next int32
}

type LRU struct {
	nodes []Node
	table []int32
	head  int32
	tail  int32
	cap   int32
	count int32
}

func newLRU(cap, tableSize int) *LRU {
	nodes := make([]Node, cap)
	for i := 0; i < cap; i++ {
		nodes[i] = Node{key: -1, val: 0, prev: -1, next: -1}
	}
	table := make([]int32, tableSize)
	for i := 0; i < tableSize; i++ {
		table[i] = -1
	}
	return &LRU{
		nodes: nodes,
		table: table,
		head:  -1,
		tail:  -1,
		cap:   int32(cap),
		count: 0,
	}
}

func (l *LRU) removeNode(idx int32) {
	p := l.nodes[idx].prev
	n := l.nodes[idx].next
	if p >= 0 {
		l.nodes[p].next = n
	} else {
		l.head = n
	}
	if n >= 0 {
		l.nodes[n].prev = p
	} else {
		l.tail = p
	}
}

func (l *LRU) pushFront(idx int32) {
	l.nodes[idx].prev = -1
	l.nodes[idx].next = l.head
	if l.head >= 0 {
		l.nodes[l.head].prev = idx
	}
	l.head = idx
	if l.tail < 0 {
		l.tail = idx
	}
}

func (l *LRU) put(key, val int64) int64 {
	oldIdx := l.table[key]
	if oldIdx >= 0 {
		l.nodes[oldIdx].val = val
		l.removeNode(oldIdx)
		l.pushFront(oldIdx)
		return val
	}
	var idx int32
	if l.count < l.cap {
		idx = l.count
		l.count++
	} else {
		idx = l.tail
		oldKey := l.nodes[idx].key
		l.table[oldKey] = -1
		l.removeNode(idx)
	}
	l.nodes[idx].key = key
	l.nodes[idx].val = val
	l.table[key] = idx
	l.pushFront(idx)
	return val
}

func (l *LRU) get(key int64) int64 {
	idx := l.table[key]
	if idx < 0 {
		return -1
	}
	l.removeNode(idx)
	l.pushFront(idx)
	return l.nodes[idx].val
}

func main() {
	lru := newLRU(1000, 3000)
	var seed int64 = 123456789
	var checksum int64 = 0

	for i := 0; i < 2500000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		key := seed % 3000
		val := seed % 1000000
		if (seed & 1) == 0 {
			res := lru.put(key, val)
			checksum = (checksum*33 + res) % 1000000007
		} else {
			res := lru.get(key)
			checksum = (checksum*33 + res) % 1000000007
		}
	}

	fmt.Println(checksum)
}
