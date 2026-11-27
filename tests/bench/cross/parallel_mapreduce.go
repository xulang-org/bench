package main

import "fmt"

const modV int64 = 1000000007

func worker(jobCh chan int64, resCh chan int64) {
	var hist [256]int64
	for {
		tid := <-jobCh
		if tid < 0 {
			return
		}
		for b := 0; b < 256; b++ {
			hist[b] = 0
		}
		rng := (tid+1)*1000003 + 98765
		for i := 0; i < 131072; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			bkt := (rng >> 8) & 255
			val := 1 + ((rng >> 16) & 1023)
			hist[bkt] += val
		}
		lh := tid + 1
		for b := 0; b < 256; b++ {
			lh = (lh*131 + hist[b]) % modV
		}
		resCh <- (lh*128 + tid)
	}
}

func main() {
	const nWorkers = 8
	const nTasks = 64

	jobChs := make([]chan int64, nWorkers)
	for w := 0; w < nWorkers; w++ {
		jobChs[w] = make(chan int64, 16)
	}
	resCh := make(chan int64, 64)

	for w := 0; w < nWorkers; w++ {
		go worker(jobChs[w], resCh)
	}

	for tid := int64(0); tid < nTasks; tid++ {
		jobChs[tid&7] <- tid
	}
	for w := 0; w < nWorkers; w++ {
		jobChs[w] <- -1
	}

	var slotHash [nTasks]int64
	for doneCnt := 0; doneCnt < nTasks; doneCnt++ {
		packed := <-resCh
		rtid := packed & 127
		rlh := packed >> 7
		slotHash[rtid] = rlh
	}

	var ck int64
	for tid := 0; tid < nTasks; tid++ {
		ck = (ck*31 + slotHash[tid]) % modV
	}

	fmt.Printf("%d\n%d\n", int64(nTasks*131072), ck)
}
