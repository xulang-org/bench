let lzwClear: UInt32 = 256
let lzwEof: UInt32 = 257
let lzwMaxWidth: Int = 12
let lzwMaxCode: UInt32 = 4095
let lzwInvalid: UInt32 = 65535

@inline(__always)
func emitLsb(
    _ out: inout [UInt8],
    _ code: UInt32,
    _ width: Int,
    _ bits: inout UInt32,
    _ nbits: inout Int
) {
    bits |= code << nbits
    nbits += width
    while nbits >= 8 {
        out.append(UInt8(bits & 0xff))
        bits >>= 8
        nbits -= 8
    }
}

func lzwEncode(_ src: [UInt8]) -> [UInt8] {
    var out = [UInt8]()
    out.reserveCapacity(src.count + 64)

    var width = 9
    var hi: UInt32 = lzwEof
    var overflow: UInt32 = 1 << width
    var bits: UInt32 = 0
    var nbits = 0

    var head = [Int](repeating: 0, count: 4096)
    var keys = [UInt32]()
    var vals = [UInt16]()
    var next = [Int]()
    keys.reserveCapacity(512)
    vals.reserveCapacity(512)
    next.reserveCapacity(512)

    var saved: UInt32 = lzwInvalid
    var i = 0
    if !src.isEmpty {
        emitLsb(&out, lzwClear, width, &bits, &nbits)
        saved = UInt32(src[0])
        i = 1
    }

    while i < src.count {
        let lit = UInt32(src[i])
        let key = (saved << 8) | lit
        let h = Int((key &* 31) & 4095)
        var found = -1
        var cur = head[h]
        while cur > 0 {
            let idx = cur - 1
            if keys[idx] == key {
                found = idx
                break
            }
            cur = next[idx]
        }
        if found >= 0 {
            saved = UInt32(vals[found])
            i += 1
            continue
        }
        emitLsb(&out, saved, width, &bits, &nbits)
        saved = lit
        hi += 1
        var outOf = false
        if hi == overflow {
            width += 1
            overflow <<= 1
        }
        if hi == lzwMaxCode {
            emitLsb(&out, lzwClear, width, &bits, &nbits)
            width = 9
            hi = lzwEof
            overflow = lzwClear * 2
            keys.removeAll(keepingCapacity: true)
            vals.removeAll(keepingCapacity: true)
            next.removeAll(keepingCapacity: true)
            for j in 0..<4096 {
                head[j] = 0
            }
            outOf = true
        }
        if !outOf {
            keys.append(key)
            vals.append(UInt16(hi))
            next.append(head[h])
            head[h] = keys.count
        }
        i += 1
    }

    if saved != lzwInvalid {
        emitLsb(&out, saved, width, &bits, &nbits)
        hi += 1
        if hi == overflow {
            width += 1
            overflow <<= 1
        }
        if hi == lzwMaxCode {
            emitLsb(&out, lzwClear, width, &bits, &nbits)
            width = 9
        }
    } else {
        emitLsb(&out, lzwClear, width, &bits, &nbits)
    }

    emitLsb(&out, lzwEof, width, &bits, &nbits)
    if nbits > 0 {
        out.append(UInt8(bits & 0xff))
    }
    return out
}

func lzwDecode(_ src: [UInt8]) -> [UInt8] {
    var out = [UInt8]()
    out.reserveCapacity(src.count * 4 + 64)

    var width = 9
    var hi: UInt32 = lzwEof
    var overflow: UInt32 = 1 << width
    var last: UInt32 = lzwInvalid
    var bits: UInt32 = 0
    var nbits = 0
    var pos = 0

    var prefix = [UInt16](repeating: 0, count: 4096)
    var suffix = [UInt8](repeating: 0, count: 4096)
    var stack = [UInt8]()
    stack.reserveCapacity(64)

    while true {
        while nbits < width {
            bits |= UInt32(src[pos]) << nbits
            pos += 1
            nbits += 8
        }
        let code = bits & ((1 << width) - 1)
        bits >>= width
        nbits -= width

        if code < lzwClear {
            out.append(UInt8(code))
            if last != lzwInvalid {
                let hu = Int(hi)
                suffix[hu] = UInt8(code)
                prefix[hu] = UInt16(last)
            }
        } else {
            if code == lzwClear {
                width = 9
                hi = lzwEof
                overflow = 1 << width
                last = lzwInvalid
                continue
            }
            if code == lzwEof {
                break
            }
            if code > hi {
                fatalError("lzw: invalid code")
            }
            stack.removeAll(keepingCapacity: true)
            var c = code
            if code == hi && last != lzwInvalid {
                c = last
                while c >= lzwClear {
                    c = UInt32(prefix[Int(c)])
                }
                stack.append(UInt8(c))
                c = last
            }
            while c >= lzwClear {
                let cu = Int(c)
                stack.append(suffix[cu])
                c = UInt32(prefix[cu])
            }
            stack.append(UInt8(c))

            let firstByte = stack[stack.count - 1]
            var k = stack.count - 1
            while k >= 0 {
                out.append(stack[k])
                k -= 1
            }
            if last != lzwInvalid {
                let hu = Int(hi)
                suffix[hu] = firstByte
                prefix[hu] = UInt16(last)
            }
        }

        last = code
        hi += 1
        if hi >= overflow {
            if width == lzwMaxWidth {
                last = lzwInvalid
                hi -= 1
            } else {
                width += 1
                overflow <<= 1
            }
        }
    }
    return out
}

func main() {
    let base = Array("TOBEORNOTTOBEORTOBEORNOT#".utf8)
    var payload = [UInt8]()
    payload.reserveCapacity(base.count * 16)
    for _ in 0..<16 {
        payload.append(contentsOf: base)
    }

    var total: Int64 = 0
    for i in 0..<2500 {
        let enc = lzwEncode(payload)
        let dec = lzwDecode(enc)
        total += Int64(enc.count + dec.count)
        if i == 0 {
            total += Int64(dec[0]) + Int64(dec[dec.count - 1])
        }
    }
    print(total)
}

main()
