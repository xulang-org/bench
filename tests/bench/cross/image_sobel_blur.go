package main

import "fmt"

const modV int64 = 1000000007

func main() {
	const w = 512
	const h = 512
	const totalPx = w * h

	img := make([]int64, totalPx)
	blur := make([]int64, totalPx)
	edges := make([]int64, totalPx)

	var rng int64 = 51515151
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			v := int64(((x*3 + y*5) >> 3) & 255)
			dx := x - 256
			dy := y - 256
			if dx*dx+dy*dy < 16384 {
				v = (v + 110) & 255
			}
			if (x >= 80 && x < 200 && y >= 80 && y < 220) || (((x>>5)+(y>>5))%4) == 0 {
				v = (v ^ 96) & 255
			}
			img[y*w+x] = (v + (rng & 15)) & 255
		}
	}

	var edgeCnt int64
	for p := 0; p < 6; p++ {
		for x := 0; x < w; x++ {
			blur[x] = img[x]
			blur[(h-1)*w+x] = img[(h-1)*w+x]
		}
		for y := 1; y < h-1; y++ {
			row := y * w
			blur[row] = img[row]
			blur[row+w-1] = img[row+w-1]
			for x := 1; x < w-1; x++ {
				idx := row + x
				s := img[idx-w-1] + 2*img[idx-w] + img[idx-w+1] +
					2*img[idx-1] + 4*img[idx] + 2*img[idx+1] +
					img[idx+w-1] + 2*img[idx+w] + img[idx+w+1]
				blur[idx] = s >> 4
			}
		}
		for y := 1; y < h-1; y++ {
			row := y * w
			for x := 1; x < w-1; x++ {
				idx := row + x
				gx := -blur[idx-w-1] + blur[idx-w+1] - 2*blur[idx-1] + 2*blur[idx+1] - blur[idx+w-1] + blur[idx+w+1]
				gy := -blur[idx-w-1] - 2*blur[idx-w] - blur[idx-w+1] + blur[idx+w-1] + 2*blur[idx+w] + blur[idx+w+1]
				if gx < 0 {
					gx = -gx
				}
				if gy < 0 {
					gy = -gy
				}
				mag := gx + gy
				if mag > 255 {
					mag = 255
				}
				edges[idx] = mag
				if mag >= 64 {
					edgeCnt++
				}
			}
		}
		for i := 0; i < totalPx; i++ {
			img[i] = (blur[i]*3 + edges[i]) >> 2
		}
	}

	var ck int64
	for i := 0; i < totalPx; i++ {
		ck = (ck*131 + edges[i]) % modV
	}

	fmt.Printf("%d\n%d\n", edgeCnt, ck)
}
