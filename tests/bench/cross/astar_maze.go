package main

import "fmt"

type Heap struct {
	f   []int64
	n   []int64
	len int64
}

func heapPush(h *Heap, fval, node int64) {
	i := h.len
	h.f[i] = fval
	h.n[i] = node
	h.len++
	for i > 0 {
		p := (i - 1) / 2
		if h.f[p] > h.f[i] || (h.f[p] == h.f[i] && h.n[p] > h.n[i]) {
			h.f[p], h.f[i] = h.f[i], h.f[p]
			h.n[p], h.n[i] = h.n[i], h.n[p]
			i = p
		} else {
			break
		}
	}
}

func heapPop(h *Heap) int64 {
	top := h.n[0]
	h.len--
	sz := h.len
	if sz > 0 {
		h.f[0] = h.f[sz]
		h.n[0] = h.n[sz]
		var i int64
		for {
			l := 2*i + 1
			if l >= sz {
				break
			}
			r := l + 1
			best := l
			if r < sz && (h.f[r] < h.f[l] || (h.f[r] == h.f[l] && h.n[r] < h.n[l])) {
				best = r
			}
			if h.f[best] < h.f[i] || (h.f[best] == h.f[i] && h.n[best] < h.n[i]) {
				h.f[i], h.f[best] = h.f[best], h.f[i]
				h.n[i], h.n[best] = h.n[best], h.n[i]
				i = best
			} else {
				break
			}
		}
	}
	return top
}

func main() {
	const (
		W     int64 = 81
		H     int64 = 81
		N     int64 = 6561
		INF   int64 = 1000000000
		start int64 = 82
		goal  int64 = 79*81 + 79
		gx    int64 = 79
		gy    int64 = 79
	)

	grid := make([]int64, N)
	gScore := make([]int64, N)
	closed := make([]int64, N)
	stkX := make([]int64, N)
	stkY := make([]int64, N)
	h := Heap{
		f: make([]int64, 32768),
		n: make([]int64, 32768),
	}

	dx := [4]int64{0, 0, -2, 2}
	dy := [4]int64{-2, 2, 0, 0}
	var dirs [4]int64

	var sumD int64
	var polyD int64
	for m := int64(0); m < 60; m++ {
		rng := 100003 + m*9973
		for i := int64(0); i < N; i++ {
			grid[i] = 1
			gScore[i] = INF
			closed[i] = 0
		}
		grid[start] = 0
		sp := int64(1)
		stkX[0] = 1
		stkY[0] = 1
		for sp > 0 {
			cx := stkX[sp-1]
			cy := stkY[sp-1]
			var dc int64
			for d := 0; d < 4; d++ {
				nx := cx + dx[d]
				ny := cy + dy[d]
				if nx >= 1 && nx <= W-2 && ny >= 1 && ny <= H-2 && grid[ny*W+nx] == 1 {
					dirs[dc] = int64(d)
					dc++
				}
			}
			if dc == 0 {
				sp--
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				pick := dirs[rng%dc]
				nx := cx + dx[pick]
				ny := cy + dy[pick]
				mx := (cx + nx) / 2
				my := (cy + ny) / 2
				grid[my*W+mx] = 0
				grid[ny*W+nx] = 0
				stkX[sp] = nx
				stkY[sp] = ny
				sp++
			}
		}

		for y := int64(1); y < H-1; y++ {
			for x := int64(1); x < W-1; x++ {
				idx := y*W + x
				if grid[idx] == 1 {
					if (grid[idx-1] == 0 && grid[idx+1] == 0) || (grid[idx-W] == 0 && grid[idx+W] == 0) {
						rng = (rng*1103515245 + 12345) & 2147483647
						if (rng % 100) < 12 {
							grid[idx] = 0
						}
					}
				}
			}
		}

		gScore[start] = 0
		h.len = 0
		heapPush(&h, 156, start)
		var ans int64 = -1
		for h.len > 0 {
			u := heapPop(&h)
			if closed[u] != 0 {
				continue
			}
			closed[u] = 1
			if u == goal {
				ans = gScore[u]
				break
			}
			gu := gScore[u] + 1
			ux := u % W
			uy := u / W

			if uy > 0 {
				v := u - W
				if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
					gScore[v] = gu
					dhx := gx - ux
					if dhx < 0 { dhx = -dhx }
					dhy := gy - (uy - 1)
					if dhy < 0 { dhy = -dhy }
					heapPush(&h, gu+dhx+dhy, v)
				}
			}
			if uy+1 < H {
				v := u + W
				if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
					gScore[v] = gu
					dhx := gx - ux
					if dhx < 0 { dhx = -dhx }
					dhy := gy - (uy + 1)
					if dhy < 0 { dhy = -dhy }
					heapPush(&h, gu+dhx+dhy, v)
				}
			}
			if ux > 0 {
				v := u - 1
				if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
					gScore[v] = gu
					dhx := gx - (ux - 1)
					if dhx < 0 { dhx = -dhx }
					dhy := gy - uy
					if dhy < 0 { dhy = -dhy }
					heapPush(&h, gu+dhx+dhy, v)
				}
			}
			if ux+1 < W {
				v := u + 1
				if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
					gScore[v] = gu
					dhx := gx - (ux + 1)
					if dhx < 0 { dhx = -dhx }
					dhy := gy - uy
					if dhy < 0 { dhy = -dhy }
					heapPush(&h, gu+dhx+dhy, v)
				}
			}
		}
		sumD += ans
		polyD = (polyD*1000003 + ans) % 1000000007
	}
	fmt.Println(sumD)
	fmt.Println(polyD)
}
