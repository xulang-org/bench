package main

import "fmt"

const modV int64 = 1000000007

func encCp(out *[]int64, cp int64) {
	if cp < 128 {
		*out = append(*out, cp)
	} else if cp < 2048 {
		*out = append(*out, 192|(cp>>6))
		*out = append(*out, 128|(cp&63))
	} else if cp < 65536 {
		*out = append(*out, 224|(cp>>12))
		*out = append(*out, 128|((cp>>6)&63))
		*out = append(*out, 128|(cp&63))
	} else {
		*out = append(*out, 240|(cp>>18))
		*out = append(*out, 128|((cp>>12)&63))
		*out = append(*out, 128|((cp>>6)&63))
		*out = append(*out, 128|(cp&63))
	}
}

func main() {
	var rng int64 = 246801357
	src := make([]int64, 0, 65600)

	for len(src) < 65520 {
		rng = (rng*1103515245 + 12345) & 2147483647
		r := rng % 100
		if r < 38 {
			rng = (rng*1103515245 + 12345) & 2147483647
			k := rng % 62
			var cp int64
			if k < 26 {
				cp = 65 + k
			} else if k < 52 {
				cp = 97 + (k - 26)
			} else {
				cp = 48 + (k - 52)
			}
			encCp(&src, cp)
		} else if r < 52 {
			rng = (rng*1103515245 + 12345) & 2147483647
			w := rng % 6
			if w == 0 {
				encCp(&src, 32)
			} else if w == 1 {
				encCp(&src, 9)
			} else if w == 2 {
				encCp(&src, 10)
			} else if w == 3 {
				encCp(&src, 13)
			} else if w == 4 {
				encCp(&src, 160)
			} else {
				encCp(&src, 12288)
			}
		} else if r < 64 {
			rng = (rng*1103515245 + 12345) & 2147483647
			g := rng % 3
			var cp int64
			if g == 0 {
				rng = (rng*1103515245 + 12345) & 2147483647
				cp = 192 + (rng % 62)
			} else if g == 1 {
				rng = (rng*1103515245 + 12345) & 2147483647
				cp = 913 + (rng % 40)
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				cp = 1040 + (rng % 64)
			}
			encCp(&src, cp)
		} else if r < 78 {
			rng = (rng*1103515245 + 12345) & 2147483647
			var cp int64
			if (rng & 3) == 0 {
				rng = (rng*1103515245 + 12345) & 2147483647
				qi := rng & 3
				if qi == 0 {
					cp = 8216
				} else if qi == 1 {
					cp = 8217
				} else if qi == 2 {
					cp = 8220
				} else {
					cp = 8221
				}
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				cp = 65281 + (rng % 94)
			}
			encCp(&src, cp)
		} else if r < 90 {
			rng = (rng*1103515245 + 12345) & 2147483647
			encCp(&src, 19968+(rng%512))
		} else if r < 97 {
			rng = (rng*1103515245 + 12345) & 2147483647
			encCp(&src, 128512+(rng%64))
		} else {
			rng = (rng*1103515245 + 12345) & 2147483647
			inv := rng % 4
			if inv == 0 {
				rng = (rng*1103515245 + 12345) & 2147483647
				src = append(src, 128+(rng%64))
			} else if inv == 1 {
				src = append(src, 192, 175)
			} else if inv == 2 {
				src = append(src, 237, 160, 128)
			} else {
				src = append(src, 244, 144, 128, 128)
			}
		}
	}

	n := len(src)
	outBuf := make([]int64, n*3)
	var totalOut int64
	var ck int64

	for rnd := 0; rnd < 40; rnd++ {
		i := 0
		olen := 0
		inWs := 1
		for i < n {
			b0 := src[i]
			var cp int64 = 65533
			adv := 1
			if b0 < 128 {
				cp = b0
				adv = 1
			} else if b0 >= 194 && b0 <= 223 {
				if i+1 < n && (src[i+1]&192) == 128 {
					cp = ((b0 & 31) << 6) | (src[i+1] & 63)
					adv = 2
				}
			} else if b0 >= 224 && b0 <= 239 {
				if i+2 < n && (src[i+1]&192) == 128 && (src[i+2]&192) == 128 {
					c := ((b0 & 15) << 12) | ((src[i+1] & 63) << 6) | (src[i+2] & 63)
					if c >= 2048 && (c < 55296 || c > 57343) {
						cp = c
						adv = 3
					}
				}
			} else if b0 >= 240 && b0 <= 244 {
				if i+3 < n && (src[i+1]&192) == 128 && (src[i+2]&192) == 128 && (src[i+3]&192) == 128 {
					c := ((b0 & 7) << 18) | ((src[i+1] & 63) << 12) | ((src[i+2] & 63) << 6) | (src[i+3] & 63)
					if c >= 65536 && c <= 1114111 {
						cp = c
						adv = 4
					}
				}
			}
			i += adv

			if cp == 32 || cp == 9 || cp == 10 || cp == 13 || cp == 160 || cp == 12288 {
				if inWs == 0 {
					outBuf[olen] = 32
					olen++
					inWs = 1
				}
				continue
			}
			inWs = 0
			if cp >= 65281 && cp <= 65374 {
				cp -= 65248
			}
			if cp >= 65 && cp <= 90 {
				cp += 32
			} else if (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) {
				cp += 32
			} else if (cp >= 913 && cp <= 929) || (cp >= 931 && cp <= 939) {
				cp += 32
			} else if cp >= 1040 && cp <= 1071 {
				cp += 32
			} else if cp == 8216 || cp == 8217 {
				cp = 39
			} else if cp == 8220 || cp == 8221 {
				cp = 34
			}

			if cp < 128 {
				outBuf[olen] = cp
				olen++
			} else if cp < 2048 {
				outBuf[olen] = 192 | (cp >> 6)
				outBuf[olen+1] = 128 | (cp & 63)
				olen += 2
			} else if cp < 65536 {
				outBuf[olen] = 224 | (cp >> 12)
				outBuf[olen+1] = 128 | ((cp >> 6) & 63)
				outBuf[olen+2] = 128 | (cp & 63)
				olen += 3
			} else {
				outBuf[olen] = 240 | (cp >> 18)
				outBuf[olen+1] = 128 | ((cp >> 12) & 63)
				outBuf[olen+2] = 128 | ((cp >> 6) & 63)
				outBuf[olen+3] = 128 | (cp & 63)
				olen += 4
			}
		}

		h := int64(olen)
		for j := 0; j < olen; j++ {
			h = (h*131 + outBuf[j]) % modV
		}
		totalOut += int64(olen)
		ck = (ck*31 + h) % modV
	}

	fmt.Printf("%d\n%d\n", totalOut, ck)
}
