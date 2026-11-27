package main

import "fmt"

const mask32 int64 = 4294967295

func rotr32(x, n int64) int64 {
	return ((x >> n) | ((x << (32 - n)) & mask32)) & mask32
}

func sha256Block(state []int64, blk []int64, off int, w []int64, kv []int64) {
	for t := 0; t < 16; t++ {
		j := off + t*4
		w[t] = (blk[j] << 24) | (blk[j+1] << 16) | (blk[j+2] << 8) | blk[j+3]
	}
	for t := 16; t < 64; t++ {
		w15 := w[t-15]
		w2 := w[t-2]
		s0 := rotr32(w15, 7) ^ rotr32(w15, 18) ^ (w15 >> 3)
		s1 := rotr32(w2, 17) ^ rotr32(w2, 19) ^ (w2 >> 10)
		w[t] = (w[t-16] + s0 + w[t-7] + s1) & mask32
	}
	a, b, c, d, e, f, g, h := state[0], state[1], state[2], state[3], state[4], state[5], state[6], state[7]
	for t := 0; t < 64; t++ {
		bs1 := rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25)
		ch := (e & f) ^ ((e ^ mask32) & g)
		temp1 := (h + bs1 + ch + kv[t] + w[t]) & mask32
		bs0 := rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22)
		maj := (a & b) ^ (a & c) ^ (b & c)
		temp2 := (bs0 + maj) & mask32
		h = g
		g = f
		f = e
		e = (d + temp1) & mask32
		d = c
		c = b
		b = a
		a = (temp1 + temp2) & mask32
	}
	state[0] = (state[0] + a) & mask32
	state[1] = (state[1] + b) & mask32
	state[2] = (state[2] + c) & mask32
	state[3] = (state[3] + d) & mask32
	state[4] = (state[4] + e) & mask32
	state[5] = (state[5] + f) & mask32
	state[6] = (state[6] + g) & mask32
	state[7] = (state[7] + h) & mask32
}

func sha256Compute(msg []int64, mlen int, state, pad, w, kv, iv, out []int64) {
	for i := 0; i < 8; i++ {
		state[i] = iv[i]
	}
	pos := 0
	for pos+64 <= mlen {
		sha256Block(state, msg, pos, w, kv)
		pos += 64
	}
	rem := mlen - pos
	for pi := 0; pi < rem; pi++ {
		pad[pi] = msg[pos+pi]
	}
	pad[rem] = 128
	totalLen := 64
	if rem >= 56 {
		totalLen = 128
	}
	for pi := rem + 1; pi < totalLen-8; pi++ {
		pad[pi] = 0
	}
	bitlen := int64(mlen) * 8
	for bi := 0; bi < 8; bi++ {
		pad[totalLen-8+bi] = (bitlen >> ((7 - bi) * 8)) & 255
	}
	sha256Block(state, pad, 0, w, kv)
	if totalLen == 128 {
		sha256Block(state, pad, 64, w, kv)
	}
	for i := 0; i < 8; i++ {
		sv := state[i]
		out[i*4] = (sv >> 24) & 255
		out[i*4+1] = (sv >> 16) & 255
		out[i*4+2] = (sv >> 8) & 255
		out[i*4+3] = sv & 255
	}
}

func hmacSha256(key []int64, klen int, msg []int64, mlen int, ipad, opad, innerBuf, outerBuf, innerHash, state, pad, w, kv, iv, out []int64) {
	for i := 0; i < 64; i++ {
		var kb int64
		if i < klen {
			kb = key[i]
		}
		ipad[i] = kb ^ 54
		opad[i] = kb ^ 92
		innerBuf[i] = ipad[i]
		outerBuf[i] = opad[i]
	}
	for i := 0; i < mlen; i++ {
		innerBuf[64+i] = msg[i]
	}
	sha256Compute(innerBuf, 64+mlen, state, pad, w, kv, iv, innerHash)
	for i := 0; i < 32; i++ {
		outerBuf[64+i] = innerHash[i]
	}
	sha256Compute(outerBuf, 96, state, pad, w, kv, iv, out)
}

func pushLit(buf *[]int64, s string) {
	for i := 0; i < len(s); i++ {
		*buf = append(*buf, int64(s[i]))
	}
}

func pushNd(buf *[]int64, v int64, digits int) {
	var tmp [8]int64
	x := v
	for i := digits - 1; i >= 0; i-- {
		tmp[i] = 48 + (x % 10)
		x /= 10
	}
	for i := 0; i < digits; i++ {
		*buf = append(*buf, tmp[i])
	}
}

func main() {
	iv := []int64{
		1779033703, 3144134277, 1013904242, 2773480762,
		1359893119, 2600822924, 528734635, 1541459225,
	}
	kv := []int64{
		1116352408, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221,
		3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
		3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986,
		2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895,
		666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
		2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344,
		430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779,
		1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298,
	}

	state := make([]int64, 8)
	w := make([]int64, 64)
	pad := make([]int64, 128)
	ipad := make([]int64, 64)
	opad := make([]int64, 64)
	innerBuf := make([]int64, 256)
	outerBuf := make([]int64, 256)
	innerHash := make([]int64, 32)
	dk := make([]int64, 32)
	uBuf := make([]int64, 32)
	acc := make([]int64, 32)
	pw := make([]int64, 0, 64)
	salt := make([]int64, 0, 64)
	key := make([]int64, 0, 64)
	msg := make([]int64, 0, 128)

	ops := 0
	for i := int64(0); i < 80; i++ {
		pw = pw[:0]
		pushLit(&pw, "xu-pass-")
		pushNd(&pw, i, 3)
		pushLit(&pw, "-secret")

		salt = salt[:0]
		pushLit(&salt, "salt-")
		pushNd(&salt, i*7, 4)
		pushLit(&salt, "-v1")
		salt = append(salt, 0, 0, 0, 1)

		hmacSha256(pw, len(pw), salt, len(salt), ipad, opad, innerBuf, outerBuf, innerHash, state, pad, w, kv, iv, uBuf)
		for bi := 0; bi < 32; bi++ {
			dk[bi] = uBuf[bi]
		}
		for it := 1; it < 1000; it++ {
			hmacSha256(pw, len(pw), uBuf, 32, ipad, opad, innerBuf, outerBuf, innerHash, state, pad, w, kv, iv, uBuf)
			for bi := 0; bi < 32; bi++ {
				dk[bi] ^= uBuf[bi]
			}
		}
		for bi := 0; bi < 32; bi++ {
			acc[bi] ^= dk[bi]
		}
		ops++
	}

	for i := int64(0); i < 200; i++ {
		key = key[:0]
		pushLit(&key, "jwt-hmac-key-")
		pushNd(&key, i%16, 2)

		msg = msg[:0]
		pushLit(&msg, "eyJhbGciOiJIUzI1NiJ9.sub=user_")
		pushNd(&msg, i, 4)
		pushLit(&msg, "&seq=")
		pushNd(&msg, i*37, 5)

		hmacSha256(key, len(key), msg, len(msg), ipad, opad, innerBuf, outerBuf, innerHash, state, pad, w, kv, iv, uBuf)
		for bi := 0; bi < 32; bi++ {
			acc[bi] ^= uBuf[bi]
		}
		ops++
	}

	fmt.Println(ops)
	outHex := make([]byte, 64)
	const hexChars = "0123456789abcdef"
	for hi := 0; hi < 32; hi++ {
		v := acc[hi]
		outHex[hi*2] = hexChars[(v>>4)&15]
		outHex[hi*2+1] = hexChars[v&15]
	}
	fmt.Println(string(outHex))
}
