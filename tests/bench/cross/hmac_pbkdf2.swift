let mask32 = 4294967295

@inline(__always)
func rotr32(_ x: Int, _ n: Int) -> Int {
    return ((x >> n) | ((x << (32 - n)) & mask32)) & mask32
}

func sha256Block(_ state: inout [Int], _ blk: [Int], _ off: Int, _ w: inout [Int], _ kv: [Int]) {
    for t in 0..<16 {
        let j = off + t * 4
        w[t] = (blk[j] << 24) | (blk[j + 1] << 16) | (blk[j + 2] << 8) | blk[j + 3]
    }
    for t in 16..<64 {
        let w15 = w[t - 15]
        let w2 = w[t - 2]
        let s0 = rotr32(w15, 7) ^ rotr32(w15, 18) ^ (w15 >> 3)
        let s1 = rotr32(w2, 17) ^ rotr32(w2, 19) ^ (w2 >> 10)
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) & mask32
    }
    var a = state[0], b = state[1], c = state[2], d = state[3]
    var e = state[4], f = state[5], g = state[6], h = state[7]
    for t in 0..<64 {
        let bs1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25)
        let ch = (e & f) ^ ((e ^ mask32) & g)
        let temp1 = (h + bs1 + ch + kv[t] + w[t]) & mask32
        let bs0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22)
        let maj = (a & b) ^ (a & c) ^ (b & c)
        let temp2 = (bs0 + maj) & mask32
        h = g; g = f; f = e; e = (d + temp1) & mask32
        d = c; c = b; b = a; a = (temp1 + temp2) & mask32
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

func sha256Compute(
    _ msg: [Int], _ mlen: Int, _ state: inout [Int], _ pad: inout [Int],
    _ w: inout [Int], _ kv: [Int], _ iv: [Int], _ out: inout [Int]
) {
    for i in 0..<8 { state[i] = iv[i] }
    var pos = 0
    while pos + 64 <= mlen {
        sha256Block(&state, msg, pos, &w, kv)
        pos += 64
    }
    let rem = mlen - pos
    for pi in 0..<rem { pad[pi] = msg[pos + pi] }
    pad[rem] = 128
    let totalLen = rem >= 56 ? 128 : 64
    for pi in (rem + 1)..<(totalLen - 8) { pad[pi] = 0 }
    let bitlen = mlen * 8
    for bi in 0..<8 { pad[totalLen - 8 + bi] = (bitlen >> ((7 - bi) * 8)) & 255 }
    sha256Block(&state, pad, 0, &w, kv)
    if totalLen == 128 { sha256Block(&state, pad, 64, &w, kv) }
    for i in 0..<8 {
        let sv = state[i]
        out[i * 4] = (sv >> 24) & 255
        out[i * 4 + 1] = (sv >> 16) & 255
        out[i * 4 + 2] = (sv >> 8) & 255
        out[i * 4 + 3] = sv & 255
    }
}

func hmacSha256(
    _ key: [Int], _ klen: Int, _ msg: [Int], _ mlen: Int,
    _ ipad: inout [Int], _ opad: inout [Int], _ innerBuf: inout [Int], _ outerBuf: inout [Int],
    _ innerHash: inout [Int], _ state: inout [Int], _ pad: inout [Int], _ w: inout [Int],
    _ kv: [Int], _ iv: [Int], _ out: inout [Int]
) {
    for i in 0..<64 {
        let kb = i < klen ? key[i] : 0
        ipad[i] = kb ^ 54
        opad[i] = kb ^ 92
        innerBuf[i] = ipad[i]
        outerBuf[i] = opad[i]
    }
    for i in 0..<mlen { innerBuf[64 + i] = msg[i] }
    sha256Compute(innerBuf, 64 + mlen, &state, &pad, &w, kv, iv, &innerHash)
    for i in 0..<32 { outerBuf[64 + i] = innerHash[i] }
    sha256Compute(outerBuf, 96, &state, &pad, &w, kv, iv, &out)
}

func pushLit(_ buf: inout [Int], _ s: String) {
    for b in s.utf8 { buf.append(Int(b)) }
}

func pushNd(_ buf: inout [Int], _ v: Int, _ digits: Int) {
    var tmp = [Int](repeating: 0, count: 8)
    var x = v
    var i = digits - 1
    while i >= 0 {
        tmp[i] = 48 + (x % 10)
        x /= 10
        i -= 1
    }
    for j in 0..<digits { buf.append(tmp[j]) }
}

func mainFunc() {
    let iv = [
        1779033703, 3144134277, 1013904242, 2773480762,
        1359893119, 2600822924, 528734635, 1541459225,
    ]
    let kv = [
        1116352408, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221,
        3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
        3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986,
        2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895,
        666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
        2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344,
        430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779,
        1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298,
    ]

    var state = [Int](repeating: 0, count: 8)
    var w = [Int](repeating: 0, count: 64)
    var pad = [Int](repeating: 0, count: 128)
    var ipad = [Int](repeating: 0, count: 64)
    var opad = [Int](repeating: 0, count: 64)
    var innerBuf = [Int](repeating: 0, count: 256)
    var outerBuf = [Int](repeating: 0, count: 256)
    var innerHash = [Int](repeating: 0, count: 32)
    var dk = [Int](repeating: 0, count: 32)
    var uBuf = [Int](repeating: 0, count: 32)
    var acc = [Int](repeating: 0, count: 32)

    var pw: [Int] = []
    var salt: [Int] = []
    var key: [Int] = []
    var msg: [Int] = []
    var ops = 0

    for i in 0..<80 {
        pw.removeAll(keepingCapacity: true)
        pushLit(&pw, "xu-pass-")
        pushNd(&pw, i, 3)
        pushLit(&pw, "-secret")

        salt.removeAll(keepingCapacity: true)
        pushLit(&salt, "salt-")
        pushNd(&salt, i * 7, 4)
        pushLit(&salt, "-v1")
        salt.append(contentsOf: [0, 0, 0, 1])

        hmacSha256(pw, pw.count, salt, salt.count, &ipad, &opad, &innerBuf, &outerBuf, &innerHash, &state, &pad, &w, kv, iv, &uBuf)
        for bi in 0..<32 { dk[bi] = uBuf[bi] }
        for _ in 1..<1000 {
            let uCopy = uBuf
            hmacSha256(pw, pw.count, uCopy, 32, &ipad, &opad, &innerBuf, &outerBuf, &innerHash, &state, &pad, &w, kv, iv, &uBuf)
            for bi in 0..<32 { dk[bi] ^= uBuf[bi] }
        }
        for bi in 0..<32 { acc[bi] ^= dk[bi] }
        ops += 1
    }

    for i in 0..<200 {
        key.removeAll(keepingCapacity: true)
        pushLit(&key, "jwt-hmac-key-")
        pushNd(&key, i % 16, 2)

        msg.removeAll(keepingCapacity: true)
        pushLit(&msg, "eyJhbGciOiJIUzI1NiJ9.sub=user_")
        pushNd(&msg, i, 4)
        pushLit(&msg, "&seq=")
        pushNd(&msg, i * 37, 5)

        hmacSha256(key, key.count, msg, msg.count, &ipad, &opad, &innerBuf, &outerBuf, &innerHash, &state, &pad, &w, kv, iv, &uBuf)
        for bi in 0..<32 { acc[bi] ^= uBuf[bi] }
        ops += 1
    }

    print(ops)
    let hexDigits: [Character] = ["0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f"]
    var s = ""
    s.reserveCapacity(64)
    for v in acc {
        s.append(hexDigits[(v >> 4) & 15])
        s.append(hexDigits[v & 15])
    }
    print(s)
}

mainFunc()
