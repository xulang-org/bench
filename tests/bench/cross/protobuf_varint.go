package main

import "fmt"

const modV int64 = 1000000007

func putUvarint(buf *[]int64, val int64) {
	v := val
	for v >= 128 {
		*buf = append(*buf, (v&127)|128)
		v >>= 7
	}
	*buf = append(*buf, v&127)
}

func zigzagEnc(v int64) int64 {
	if v >= 0 {
		return v << 1
	}
	return ((-v) << 1) - 1
}

func zigzagDec(u int64) int64 {
	if (u & 1) == 0 {
		return u >> 1
	}
	return -((u >> 1) + 1)
}

func pushStrBytes(buf *[]int64, s string) {
	for i := 0; i < len(s); i++ {
		*buf = append(*buf, int64(s[i]))
	}
}

func main() {
	symbols := []string{"BTC-USD", "ETH-EUR", "SOL-JPY", "XU-USD", "NVDA", "AAPL", "GOOG", "MSFT"}
	tags := []string{"fast", "batch", "edge", "core", "prod", "canary", "blue", "green"}

	buf := make([]int64, 0, 32768)
	meta := make([]int64, 0, 64)
	packed := make([]int64, 0, 32)
	msg := make([]int64, 0, 128)
	var qs [8]int64

	var rng int64 = 314159265
	var totalWire int64
	var ck int64
	for batch := int64(0); batch < 400; batch++ {
		buf = buf[:0]
		for i := int64(0); i < 500; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			orderID := (batch*500+i+1)*131 + (rng & 1023)
			rng = (rng*1103515245 + 12345) & 2147483647
			priceDelta := (rng % 200001) - 100000
			rng = (rng*1103515245 + 12345) & 2147483647
			sym := symbols[rng&7]
			rng = (rng*1103515245 + 12345) & 2147483647
			qcnt := int(4 + (rng & 3))
			for qi := 0; qi < qcnt; qi++ {
				rng = (rng*1103515245 + 12345) & 2147483647
				qs[qi] = 1 + (rng % 5000)
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			regID := 1 + (rng & 31)
			rng = (rng*1103515245 + 12345) & 2147483647
			latUS := (rng % 10001) - 5000
			rng = (rng*1103515245 + 12345) & 2147483647
			tag := tags[rng&7]

			meta = meta[:0]
			putUvarint(&meta, (1<<3)|0)
			putUvarint(&meta, regID)
			putUvarint(&meta, (2<<3)|0)
			putUvarint(&meta, zigzagEnc(latUS))
			putUvarint(&meta, (3<<3)|2)
			putUvarint(&meta, int64(len(tag)))
			pushStrBytes(&meta, tag)

			packed = packed[:0]
			for qi := 0; qi < qcnt; qi++ {
				putUvarint(&packed, qs[qi])
			}

			msg = msg[:0]
			putUvarint(&msg, (1<<3)|0)
			putUvarint(&msg, orderID)
			putUvarint(&msg, (2<<3)|0)
			putUvarint(&msg, zigzagEnc(priceDelta))
			putUvarint(&msg, (3<<3)|2)
			putUvarint(&msg, int64(len(sym)))
			pushStrBytes(&msg, sym)
			putUvarint(&msg, (4<<3)|2)
			putUvarint(&msg, int64(len(packed)))
			msg = append(msg, packed...)
			putUvarint(&msg, (5<<3)|2)
			putUvarint(&msg, int64(len(meta)))
			msg = append(msg, meta...)

			putUvarint(&buf, int64(len(msg)))
			buf = append(buf, msg...)
		}

		totalWire += int64(len(buf))
		pos := 0
		blen := len(buf)
		for pos < blen {
			var mlen int64
			var sh uint
			for {
				b := buf[pos]
				pos++
				mlen |= (b & 127) << sh
				if (b & 128) == 0 {
					break
				}
				sh += 7
			}
			end := pos + int(mlen)
			var oid, pdelta, symSum, qSum, reg, lat, tlen int64
			for pos < end {
				var tagW int64
				sh = 0
				for {
					b := buf[pos]
					pos++
					tagW |= (b & 127) << sh
					if (b & 128) == 0 {
						break
					}
					sh += 7
				}
				fnum := tagW >> 3
				wtype := tagW & 7
				if wtype == 0 {
					var val int64
					sh = 0
					for {
						b := buf[pos]
						pos++
						val |= (b & 127) << sh
						if (b & 128) == 0 {
							break
						}
						sh += 7
					}
					if fnum == 1 {
						oid = val
					} else if fnum == 2 {
						pdelta = zigzagDec(val)
					}
				} else if wtype == 2 {
					var ln int64
					sh = 0
					for {
						b := buf[pos]
						pos++
						ln |= (b & 127) << sh
						if (b & 128) == 0 {
							break
						}
						sh += 7
					}
					subEnd := pos + int(ln)
					if fnum == 3 {
						for pos < subEnd {
							symSum += buf[pos]
							pos++
						}
					} else if fnum == 4 {
						for pos < subEnd {
							var qv int64
							sh = 0
							for {
								b := buf[pos]
								pos++
								qv |= (b & 127) << sh
								if (b & 128) == 0 {
									break
								}
								sh += 7
							}
							qSum += qv
						}
					} else if fnum == 5 {
						for pos < subEnd {
							var mtag int64
							sh = 0
							for {
								b := buf[pos]
								pos++
								mtag |= (b & 127) << sh
								if (b & 128) == 0 {
									break
								}
								sh += 7
							}
							mf := mtag >> 3
							mw := mtag & 7
							if mw == 0 {
								var mv int64
								sh = 0
								for {
									b := buf[pos]
									pos++
									mv |= (b & 127) << sh
									if (b & 128) == 0 {
										break
									}
									sh += 7
								}
								if mf == 1 {
									reg = mv
								} else if mf == 2 {
									lat = zigzagDec(mv)
								}
							} else if mw == 2 {
								var sln int64
								sh = 0
								for {
									b := buf[pos]
									pos++
									sln |= (b & 127) << sh
									if (b & 128) == 0 {
										break
									}
									sh += 7
								}
								if mf == 3 {
									tlen = sln
								}
								pos += int(sln)
							}
						}
					} else {
						pos = subEnd
					}
				}
			}
			row := (oid + pdelta + symSum + qSum + reg*13 + lat + tlen*7) % modV
			if row < 0 {
				row += modV
			}
			ck = (ck*31 + row) % modV
		}
	}
	fmt.Println(totalWire)
	fmt.Println(ck)
}
