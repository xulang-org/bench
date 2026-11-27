package main

import "fmt"

func node(id int, inCh chan int, outCh chan int, done chan int) {
	for {
		v := <-inCh
		if v < 0 {
			outCh <- -1
			return
		}
		if v == 0 {
			done <- id
			outCh <- -1
			return
		}
		outCh <- v - 1
	}
}

func main() {
	const n = 503
	chs := make([]chan int, n)
	for i := 0; i < n; i++ {
		chs[i] = make(chan int, 1)
	}
	done := make(chan int, 1)
	for i := 0; i < n; i++ {
		nxt := (i + 1) % n
		go node(i+1, chs[i], chs[nxt], done)
	}
	chs[0] <- 100000
	winner := <-done
	fmt.Println(winner)
}
