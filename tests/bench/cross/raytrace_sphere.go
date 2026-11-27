package main

import (
	"fmt"
	"math"
)

func main() {
	var cx, cy, cz, cr, sr, sg, sb, refl [16]float64
	cx[0] = 0.0
	cy[0] = -1001.5
	cz[0] = -6.0
	cr[0] = 1000.0
	sr[0] = 0.45
	sg[0] = 0.48
	sb[0] = 0.52
	refl[0] = 0.25

	var rng int64 = 44556677
	for i := 1; i < 16; i++ {
		row := (i - 1) / 5
		col := (i - 1) % 5
		rng = (rng*1103515245 + 12345) & 2147483647
		cx[i] = -3.2 + float64(col)*1.6 + float64((rng%41)-20)/128.0
		rng = (rng*1103515245 + 12345) & 2147483647
		cy[i] = -0.7 + float64(row)*1.1 + float64((rng%33)-16)/128.0
		rng = (rng*1103515245 + 12345) & 2147483647
		cz[i] = -4.2 - float64(row)*1.8 - float64(rng%33)/64.0
		rng = (rng*1103515245 + 12345) & 2147483647
		cr[i] = 0.45 + float64(rng%17)/64.0
		rng = (rng*1103515245 + 12345) & 2147483647
		sr[i] = 0.25 + float64(rng%48)/64.0
		rng = (rng*1103515245 + 12345) & 2147483647
		sg[i] = 0.25 + float64(rng%48)/64.0
		rng = (rng*1103515245 + 12345) & 2147483647
		sb[i] = 0.25 + float64(rng%48)/64.0
		refl[i] = 0.2 + float64(i%4)*0.15
	}

	const lx = 0.5773502691896258
	const ly = 0.5773502691896258
	const lz = 0.5773502691896258
	const w = 320
	const h = 240
	var hitCount int64
	totalLum := 0.0

	for py := 0; py < h; py++ {
		v := (0.5 - (float64(py)+0.5)/240.0) * 1.5
		for px := 0; px < w; px++ {
			u := ((float64(px)+0.5)/320.0 - 0.5) * 2.0
			invL := 1.0 / math.Sqrt(u*u+v*v+1.0)
			ox, oy, oz := 0.0, 0.2, 0.0
			dx, dy, dz := u*invL, v*invL, -1.0*invL
			att := 1.0
			pr, pg, pb := 0.0, 0.0, 0.0

			for depth := 0; depth < 3; depth++ {
				bestT := 1.0e18
				bestI := -1
				for i := 0; i < 16; i++ {
					ocx := ox - cx[i]
					ocy := oy - cy[i]
					ocz := oz - cz[i]
					b := ocx*dx + ocy*dy + ocz*dz
					c := ocx*ocx + ocy*ocy + ocz*ocz - cr[i]*cr[i]
					disc := b*b - c
					if disc > 0.0 {
						t := -b - math.Sqrt(disc)
						if t > 0.0005 && t < bestT {
							bestT = t
							bestI = i
						}
					}
				}
				if bestI == -1 {
					sky := 0.5 * (dy + 1.0)
					pr += att * (0.2 + 0.4*sky)
					pg += att * (0.3 + 0.4*sky)
					pb += att * (0.5 + 0.4*sky)
					break
				}
				hitCount++
				hx := ox + dx*bestT
				hy := oy + dy*bestT
				hz := oz + dz*bestT
				invR := 1.0 / cr[bestI]
				nx := (hx - cx[bestI]) * invR
				ny := (hy - cy[bestI]) * invR
				nz := (hz - cz[bestI]) * invR

				sox := hx + nx*0.002
				soy := hy + ny*0.002
				soz := hz + nz*0.002
				inShadow := false
				for j := 0; j < 16; j++ {
					ocx := sox - cx[j]
					ocy := soy - cy[j]
					ocz := soz - cz[j]
					b := ocx*lx + ocy*ly + ocz*lz
					c := ocx*ocx + ocy*ocy + ocz*ocz - cr[j]*cr[j]
					disc := b*b - c
					if disc > 0.0 {
						st := -b - math.Sqrt(disc)
						if st > 0.0005 {
							inShadow = true
							break
						}
					}
				}

				diff := 0.0
				spec := 0.0
				if !inShadow {
					ndotl := nx*lx + ny*ly + nz*lz
					if ndotl > 0.0 {
						diff = ndotl
						hx2 := lx - dx
						hy2 := ly - dy
						hz2 := lz - dz
						hinv := 1.0 / math.Sqrt(hx2*hx2+hy2*hy2+hz2*hz2)
						ndoth := (nx*hx2 + ny*hy2 + nz*hz2) * hinv
						if ndoth > 0.0 {
							s2 := ndoth * ndoth
							s4 := s2 * s2
							spec = s4 * s4 * 0.5
						}
					}
				}
				shade := 0.1 + 0.75*diff
				kr := refl[bestI]
				pr += att * (1.0 - kr) * (sr[bestI]*shade + spec)
				pg += att * (1.0 - kr) * (sg[bestI]*shade + spec)
				pb += att * (1.0 - kr) * (sb[bestI]*shade + spec)
				att *= kr
				if att < 0.02 {
					break
				}
				dot2 := 2.0 * (dx*nx + dy*ny + dz*nz)
				dx -= dot2 * nx
				dy -= dot2 * ny
				dz -= dot2 * nz
				ox, oy, oz = sox, soy, soz
			}
			totalLum += pr + pg + pb
		}
	}

	fmt.Printf("%d\n%d\n", hitCount, int64(math.Floor(totalLum*10.0+0.5)))
}
