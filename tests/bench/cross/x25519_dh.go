package main

import "fmt"

func car25519(o *[16]int64) {
	for i := 0; i < 16; i++ {
		c := o[i] >> 16
		o[i] &= 65535
		if i < 15 {
			o[i+1] += c
		} else {
			o[0] += c * 38
		}
	}
}

func fadd(o, a, b *[16]int64) {
	for i := 0; i < 16; i++ {
		o[i] = a[i] + b[i]
	}
}

func fsub(o, a, b *[16]int64) {
	o[0] = a[0] + 130996 - b[0]
	for i := 1; i < 16; i++ {
		o[i] = a[i] + 131070 - b[i]
	}
	car25519(o)
}

func fmul(o, a, b *[16]int64) {
	var t [32]int64
	for i := 0; i < 16; i++ {
		ai := a[i]
		for j := 0; j < 16; j++ {
			t[i+j] += ai * b[j]
		}
	}
	for i := 0; i < 16; i++ {
		o[i] = t[i] + 38*t[i+16]
	}
	car25519(o)
	car25519(o)
}

func cswap(p, q *[16]int64, bit int64) {
	if bit != 0 {
		for i := 0; i < 16; i++ {
			p[i], q[i] = q[i], p[i]
		}
	}
}

func finv(o, inV *[16]int64) {
	c := *inV
	for a := 253; a >= 0; a-- {
		fmul(&c, &c, &c)
		if a != 2 && a != 4 {
			fmul(&c, &c, inV)
		}
	}
	*o = c
}

func pack25519(o *[32]int64, nIn *[16]int64) {
	t := *nIn
	car25519(&t)
	car25519(&t)
	car25519(&t)
	var m [16]int64
	for pass := 0; pass < 2; pass++ {
		m[0] = t[0] - 65517
		var borrow int64
		if m[0] < 0 {
			m[0] += 65536
			borrow = 1
		}
		for i := 1; i < 15; i++ {
			m[i] = t[i] - 65535 - borrow
			if m[i] < 0 {
				m[i] += 65536
				borrow = 1
			} else {
				borrow = 0
			}
		}
		m[15] = t[15] - 32767 - borrow
		if m[15] >= 0 {
			t = m
		}
	}
	for i := 0; i < 16; i++ {
		o[2*i] = t[i] & 255
		o[2*i+1] = (t[i] >> 8) & 255
	}
}

func x25519(q, nBytes, pBytes *[32]int64, a24 *[16]int64) {
	z := *nBytes
	z[0] &= 248
	z[31] = (z[31] & 127) | 64
	var x, a, b, c, d, e, f [16]int64
	for i := 0; i < 16; i++ {
		x[i] = pBytes[2*i] | (pBytes[2*i+1] << 8)
	}
	x[15] &= 32767
	a[0] = 1
	b = x
	d[0] = 1

	for bitI := 254; bitI >= 0; bitI-- {
		r := (z[bitI>>3] >> uint(bitI&7)) & 1
		cswap(&a, &b, r)
		cswap(&c, &d, r)
		fadd(&e, &a, &c)
		fsub(&a, &a, &c)
		fadd(&c, &b, &d)
		fsub(&b, &b, &d)
		fmul(&d, &e, &e)
		fmul(&f, &a, &a)
		fmul(&a, &c, &a)
		fmul(&c, &b, &e)
		fadd(&e, &a, &c)
		fsub(&a, &a, &c)
		fmul(&b, &a, &a)
		fsub(&c, &d, &f)
		fmul(&a, &c, a24)
		fadd(&a, &a, &d)
		fmul(&c, &c, &a)
		fmul(&a, &d, &f)
		fmul(&d, &b, &x)
		fmul(&b, &e, &e)
		cswap(&a, &b, r)
		cswap(&c, &d, r)
	}
	e = c
	finv(&c, &e)
	fmul(&a, &a, &c)
	pack25519(q, &a)
}

func main() {
	var a24 [16]int64
	a24[0] = 56129
	a24[1] = 1

	var k, u, out [32]int64
	k[0] = 9
	u[0] = 9

	for step := 0; step < 100; step++ {
		x25519(&out, &k, &u, &a24)
		u = k
		k = out
	}

	fmt.Println(100)
	for i := 0; i < 32; i++ {
		fmt.Printf("%02x", k[i])
	}
	fmt.Println()
}
