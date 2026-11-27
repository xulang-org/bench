package main

import "fmt"

const modV int64 = 1000000007

func isqrt64(n int64) int64 {
	if n <= 0 {
		return 0
	}
	x := n
	y := (x + 1) >> 1
	for y < x {
		x = y
		y = (x + n/x) >> 1
	}
	return x
}

func sdiv(num, den int64) int64 {
	if num >= 0 {
		return num / den
	}
	return -((-num) / den)
}

func main() {
	const n = 512
	const arena int64 = 65536
	var rng int64 = 62626262

	px := make([]int64, n)
	py := make([]int64, n)
	vx := make([]int64, n)
	vy := make([]int64, n)
	rad := make([]int64, n)
	nxtB := make([]int, n)
	for i := 0; i < n; i++ {
		row := int64(i / 32)
		col := int64(i % 32)
		rng = (rng*1103515245 + 12345) & 2147483647
		px[i] = 1024 + col*2000 + (rng % 200)
		rng = (rng*1103515245 + 12345) & 2147483647
		py[i] = 1024 + row*4000 + (rng % 200)
		rng = (rng*1103515245 + 12345) & 2147483647
		vx[i] = (rng % 321) - 160
		rng = (rng*1103515245 + 12345) & 2147483647
		vy[i] = (rng % 321) - 160
		rng = (rng*1103515245 + 12345) & 2147483647
		rad[i] = 384 + (rng % 257)
		nxtB[i] = -1
	}

	head := make([]int, 256)
	var collisions int64

	for step := 0; step < 500; step++ {
		for c := 0; c < 256; c++ {
			head[c] = -1
		}
		for i := 0; i < n; i++ {
			x := px[i] + vx[i]
			y := py[i] + vy[i]
			r := rad[i]
			if x < r {
				x = r
				vx[i] = -vx[i]
			} else if x > arena-r {
				x = arena - r
				vx[i] = -vx[i]
			}
			if y < r {
				y = r
				vy[i] = -vy[i]
			} else if y > arena-r {
				y = arena - r
				vy[i] = -vy[i]
			}
			px[i] = x
			py[i] = y
			cx := int(x >> 12)
			cy := int(y >> 12)
			if cx > 15 {
				cx = 15
			}
			if cy > 15 {
				cy = 15
			}
			cell := (cy << 4) | cx
			nxtB[i] = head[cell]
			head[cell] = i
		}

		for i := 0; i < n; i++ {
			cx := int(px[i] >> 12)
			cy := int(py[i] >> 12)
			if cx > 15 {
				cx = 15
			}
			if cy > 15 {
				cy = 15
			}
			y0 := cy - 1
			if y0 < 0 {
				y0 = 0
			}
			y1 := cy + 1
			if y1 > 15 {
				y1 = 15
			}
			x0 := cx - 1
			if x0 < 0 {
				x0 = 0
			}
			x1 := cx + 1
			if x1 > 15 {
				x1 = 15
			}
			for ny := y0; ny <= y1; ny++ {
				for nx := x0; nx <= x1; nx++ {
					j := head[(ny<<4)|nx]
					for j != -1 {
						if j > i {
							dx := px[j] - px[i]
							dy := py[j] - py[i]
							rsum := rad[i] + rad[j]
							dist2 := dx*dx + dy*dy
							if dist2 < rsum*rsum && dist2 > 0 {
								collisions++
								dist := isqrt64(dist2)
								if dist < 1 {
									dist = 1
								}
								half := (rsum - dist + 1) >> 1
								sx := sdiv(dx*half, dist)
								sy := sdiv(dy*half, dist)
								px[i] -= sx
								py[i] -= sy
								px[j] += sx
								py[j] += sy
								vn := (vx[j]-vx[i])*dx + (vy[j]-vy[i])*dy
								if vn < 0 {
									ix := sdiv(vn*dx, dist2)
									iy := sdiv(vn*dy, dist2)
									vx[i] += ix
									vy[i] += iy
									vx[j] -= ix
									vy[j] -= iy
								}
							}
						}
						j = nxtB[j]
					}
				}
			}
		}
	}

	var ck int64
	for i := 0; i < n; i++ {
		v := (px[i]+100000)*7 + (py[i]+100000)*13 + (vx[i]+100000)*17 + (vy[i]+100000)
		ck = (ck*31 + (v % modV)) % modV
	}

	fmt.Printf("%d\n%d\n", collisions, ck)
}
