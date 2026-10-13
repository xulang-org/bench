package main

import (
	"fmt"
)

type Deque struct {
	buf   []int64
	head  int
	tail  int
	count int
	mask  int
}

func newDeque() *Deque {
	return &Deque{
		buf:   make([]int64, 16),
		head:  0,
		tail:  0,
		count: 0,
		mask:  15,
	}
}

func (d *Deque) grow() {
	oldCap := len(d.buf)
	oldMask := d.mask
	newCap := oldCap * 2
	newBuf := make([]int64, newCap)
	for j := 0; j < d.count; j++ {
		newBuf[j] = d.buf[(d.head+j)&oldMask]
	}
	d.buf = newBuf
	d.head = 0
	d.tail = d.count
	d.mask = newCap - 1
}

func (d *Deque) pushBack(val int64) {
	if d.count == len(d.buf) {
		d.grow()
	}
	d.buf[d.tail] = val
	d.tail = (d.tail + 1) & d.mask
	d.count++
}

func (d *Deque) pushFront(val int64) {
	if d.count == len(d.buf) {
		d.grow()
	}
	d.head = (d.head - 1) & d.mask
	d.buf[d.head] = val
	d.count++
}

func (d *Deque) popFront() int64 {
	if d.count == 0 {
		return 0
	}
	val := d.buf[d.head]
	d.head = (d.head + 1) & d.mask
	d.count--
	return val
}

func (d *Deque) popBack() int64 {
	if d.count == 0 {
		return 0
	}
	d.tail = (d.tail - 1) & d.mask
	val := d.buf[d.tail]
	d.count--
	return val
}

func main() {
	q := newDeque()
	var seed int64 = 123456789
	var checksum int64 = 0

	for i := 0; i < 5000000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		op := seed % 4
		if op == 0 {
			q.pushBack(seed)
		} else if op == 1 {
			q.pushFront(seed)
		} else if op == 2 {
			v := q.popFront()
			checksum = (checksum*33 + v) % 1000000007
		} else {
			v := q.popBack()
			checksum = (checksum*33 + v) % 1000000007
		}
	}

	for q.count > 0 {
		v := q.popFront()
		checksum = (checksum*33 + v) % 1000000007
	}

	fmt.Println(checksum)
}
