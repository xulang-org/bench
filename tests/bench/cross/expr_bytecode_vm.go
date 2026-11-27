package main

import "fmt"

const (
	modV   int64 = 1000000007
	mask30 int64 = 1073741823
	base30 int64 = 1073741824
)

type compiler struct {
	tk   []int
	tv   []int64
	pos  int
	code []int
	imm  []int64
}

func lexExpr(c *compiler, s string) {
	c.tk = c.tk[:0]
	c.tv = c.tv[:0]
	i := 0
	n := len(s)
	for i < n {
		b := s[i]
		if b == 32 {
			i++
		} else if b >= 48 && b <= 57 {
			var v int64
			for i < n && s[i] >= 48 && s[i] <= 57 {
				v = (v*10 + int64(s[i]-48)) & mask30
				i++
			}
			c.tk = append(c.tk, 1)
			c.tv = append(c.tv, v)
		} else if b == 120 {
			c.tk = append(c.tk, 2)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 121 {
			c.tk = append(c.tk, 3)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 122 {
			c.tk = append(c.tk, 4)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 43 {
			c.tk = append(c.tk, 5)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 45 {
			c.tk = append(c.tk, 6)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 42 {
			c.tk = append(c.tk, 7)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 47 {
			c.tk = append(c.tk, 8)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 37 {
			c.tk = append(c.tk, 9)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 38 {
			c.tk = append(c.tk, 10)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 124 {
			c.tk = append(c.tk, 11)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 94 {
			c.tk = append(c.tk, 12)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 126 {
			c.tk = append(c.tk, 13)
			c.tv = append(c.tv, 0)
			i++
		} else if b == 40 {
			c.tk = append(c.tk, 14)
			c.tv = append(c.tv, 0)
			i++
		} else {
			c.tk = append(c.tk, 15)
			c.tv = append(c.tv, 0)
			i++
		}
	}
	c.tk = append(c.tk, 0)
	c.tv = append(c.tv, 0)
	c.pos = 0
	c.code = c.code[:0]
	c.imm = c.imm[:0]
}

func parsePrim(c *compiler) {
	t := c.tk[c.pos]
	if t == 1 {
		c.code = append(c.code, 1)
		c.imm = append(c.imm, c.tv[c.pos])
		c.pos++
	} else if t == 2 || t == 3 || t == 4 {
		c.code = append(c.code, t)
		c.imm = append(c.imm, 0)
		c.pos++
	} else {
		c.pos++
		parseOr(c)
		c.pos++
	}
}

func parseUnary(c *compiler) {
	t := c.tk[c.pos]
	if t == 6 {
		c.pos++
		parseUnary(c)
		c.code = append(c.code, 13)
		c.imm = append(c.imm, 0)
	} else if t == 13 {
		c.pos++
		parseUnary(c)
		c.code = append(c.code, 14)
		c.imm = append(c.imm, 0)
	} else {
		parsePrim(c)
	}
}

func parseMul(c *compiler) {
	parseUnary(c)
	for c.tk[c.pos] == 7 || c.tk[c.pos] == 8 || c.tk[c.pos] == 9 {
		op := c.tk[c.pos]
		c.pos++
		parseUnary(c)
		c.code = append(c.code, op)
		c.imm = append(c.imm, 0)
	}
}

func parseAdd(c *compiler) {
	parseMul(c)
	for c.tk[c.pos] == 5 || c.tk[c.pos] == 6 {
		op := c.tk[c.pos]
		c.pos++
		parseMul(c)
		c.code = append(c.code, op)
		c.imm = append(c.imm, 0)
	}
}

func parseAnd(c *compiler) {
	parseAdd(c)
	for c.tk[c.pos] == 10 {
		c.pos++
		parseAdd(c)
		c.code = append(c.code, 10)
		c.imm = append(c.imm, 0)
	}
}

func parseXor(c *compiler) {
	parseAnd(c)
	for c.tk[c.pos] == 12 {
		c.pos++
		parseAnd(c)
		c.code = append(c.code, 12)
		c.imm = append(c.imm, 0)
	}
}

func parseOr(c *compiler) {
	parseXor(c)
	for c.tk[c.pos] == 11 {
		c.pos++
		parseXor(c)
		c.code = append(c.code, 11)
		c.imm = append(c.imm, 0)
	}
}

func main() {
	exprs := []string{
		"((x + y) * (z + 7) - (x ^ y)) / ((z & 15) + 1) + (x % 97)",
		"(~x & 65535) + ((y * 13 + z) ^ (x + y + z)) - (y / 3)",
		"((x * 3 + y * 5 + z * 7) ^ (x * 11 - y)) + ((z | 255) & (x + 1023))",
		"-(x - y) + (z * (x & 255) + (y % 31)) ^ (~z & 4095)",
		"(((x + 17) * (y + 29)) % 65521) + ((z ^ (x + y)) / ((x & 7) + 1))",
		"((x | y) & (y | z) & (z | x)) + ((x ^ y ^ z) * 19) - (z % 17)",
		"(x + (y + (z + (x * 3 + (y * 5 - z))))) & 1048575",
		"((x / 5 + y / 7 + z / 11) * (x % 13 + y % 17 + 1)) ^ (x + z)",
		"((~x & 1023) * (~y & 1023) + (~z & 1023)) % 1000003",
		"(((x ^ 12345) + (y ^ 6789)) * 7) / ((z % 23) + 2) + (y & 511)",
		"(x * (y & 63) - y * (z & 63) + z * (x & 63)) ^ ((x + y) | z)",
		"((x + y + z) * (x + y + z)) / (x % 29 + y % 31 + 3) + (~(x & y) & 8191)",
		"(((x & 4095) + 1) * ((y & 4095) + 3) + ((z & 4095) + 5)) ^ (x * 17)",
		"((x - (y - (z - x))) + (y * 9 - z * 5)) % 99991 + (x & z)",
		"((x | 85) ^ (y | 170) ^ (z | 51)) + ((x + y) * 23) / ((y & 31) + 1)",
		"((((x + 3) * 5 - y) ^ (z + 11)) + ((y + 7) * (z & 127))) % 524287",
	}

	comp := &compiler{}
	st := make([]int64, 32)
	var totalInsts int64
	var ck int64
	var rng int64 = 112233445

	for rnd := 0; rnd < 160; rnd++ {
		for ei := 0; ei < 16; ei++ {
			lexExpr(comp, exprs[ei])
			parseOr(comp)
			comp.code = append(comp.code, 0)
			comp.imm = append(comp.imm, 0)

			for runI := 0; runI < 100; runI++ {
				rng = (rng*1103515245 + 12345) & 2147483647
				x := rng & 65535
				rng = (rng*1103515245 + 12345) & 2147483647
				y := rng & 65535
				rng = (rng*1103515245 + 12345) & 2147483647
				z := rng & 65535

				sp := 0
				ip := 0
				var steps int64
				for {
					op := comp.code[ip]
					if op == 0 {
						break
					}
					steps++
					if op == 1 {
						st[sp] = comp.imm[ip]
						sp++
					} else if op == 2 {
						st[sp] = x
						sp++
					} else if op == 3 {
						st[sp] = y
						sp++
					} else if op == 4 {
						st[sp] = z
						sp++
					} else if op == 5 {
						sp--
						st[sp-1] = (st[sp-1] + st[sp]) & mask30
					} else if op == 6 {
						sp--
						st[sp-1] = (st[sp-1] - st[sp] + base30) & mask30
					} else if op == 7 {
						sp--
						st[sp-1] = ((st[sp-1] & 32767) * (st[sp] & 32767)) & mask30
					} else if op == 8 {
						sp--
						st[sp-1] = st[sp-1] / (st[sp] + 1)
					} else if op == 9 {
						sp--
						st[sp-1] = st[sp-1] % (st[sp] + 1)
					} else if op == 10 {
						sp--
						st[sp-1] = st[sp-1] & st[sp]
					} else if op == 11 {
						sp--
						st[sp-1] = st[sp-1] | st[sp]
					} else if op == 12 {
						sp--
						st[sp-1] = st[sp-1] ^ st[sp]
					} else if op == 13 {
						st[sp-1] = (base30 - st[sp-1]) & mask30
					} else {
						st[sp-1] = st[sp-1] ^ mask30
					}
					ip++
				}
				totalInsts += steps
				ck = (ck*31 + st[sp-1]) % modV
			}
		}
	}

	fmt.Printf("%d\n%d\n", totalInsts, ck)
}
