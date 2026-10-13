package main

import "fmt"

func worker(ch chan int, n int) {
	i := 0
	for i < n {
		ch <- i
		i += 1
	}
}

func main() {
	ch := make(chan int, 64)
	go worker(ch, 500000)
	s := 0
	i := 0
	for i < 500000 {
		s += <-ch
		i += 1
	}
	fmt.Println(s)
}
