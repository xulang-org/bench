package main

import "fmt"

func skynet(ch chan int64, num int64, size int64, div int64) {
	if size == 1 {
		ch <- num
		return
	}
	subSize := size / div
	sub := make(chan int64, div)
	var i int64 = 0
	for i < div {
		go skynet(sub, num+i*subSize, subSize, div)
		i++
	}
	var sum int64 = 0
	i = 0
	for i < div {
		sum += <-sub
		i++
	}
	ch <- sum
}

func main() {
	var total int64 = 0
	for r := 0; r < 2; r++ {
		ch := make(chan int64, 1)
		go skynet(ch, 0, 1000, 10)
		total += <-ch
	}
	fmt.Println(total)
}
