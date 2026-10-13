package main

import "fmt"

type Vec3 struct {
	x float64
	y float64
	z float64
}

func main() {
	v := make([]Vec3, 256)
	i := 0
	for i < 256 {
		v[i].x = float64(i & 7)
		v[i].y = float64((i * 3) & 7)
		v[i].z = float64((i * 5) & 7)
		i += 1
	}
	acc := 0.0
	t := 0
	for t < 40000 {
		i = 0
		for i < 256 {
			acc += v[i].x*v[i].x + v[i].y*v[i].y + v[i].z*v[i].z
			i += 1
		}
		t += 1
	}
	fmt.Println(int(acc))
}
