let modV = 1000000007

func isqrt64(_ n: Int) -> Int {
    if n <= 0 {
        return 0
    }
    var x = n
    var y = (x + 1) >> 1
    while y < x {
        x = y
        y = (x + n / x) >> 1
    }
    return x
}

func sdiv(_ num: Int, _ den: Int) -> Int {
    if num >= 0 {
        return num / den
    }
    return -((-num) / den)
}

func run() {
    let n = 512
    let arena = 65536
    var rng = 62626262

    var px = [Int](repeating: 0, count: n)
    var py = [Int](repeating: 0, count: n)
    var vx = [Int](repeating: 0, count: n)
    var vy = [Int](repeating: 0, count: n)
    var rad = [Int](repeating: 0, count: n)
    var nxtB = [Int](repeating: -1, count: n)

    for i in 0..<n {
        let row = i / 32
        let col = i % 32
        rng = (rng * 1103515245 + 12345) & 2147483647
        px[i] = 1024 + col * 2000 + (rng % 200)
        rng = (rng * 1103515245 + 12345) & 2147483647
        py[i] = 1024 + row * 4000 + (rng % 200)
        rng = (rng * 1103515245 + 12345) & 2147483647
        vx[i] = (rng % 321) - 160
        rng = (rng * 1103515245 + 12345) & 2147483647
        vy[i] = (rng % 321) - 160
        rng = (rng * 1103515245 + 12345) & 2147483647
        rad[i] = 384 + (rng % 257)
    }

    var head = [Int](repeating: -1, count: 256)
    var collisions = 0

    for _ in 0..<500 {
        for c in 0..<256 {
            head[c] = -1
        }
        for i in 0..<n {
            var x = px[i] + vx[i]
            var y = py[i] + vy[i]
            let r = rad[i]
            if x < r {
                x = r
                vx[i] = -vx[i]
            } else if x > arena - r {
                x = arena - r
                vx[i] = -vx[i]
            }
            if y < r {
                y = r
                vy[i] = -vy[i]
            } else if y > arena - r {
                y = arena - r
                vy[i] = -vy[i]
            }
            px[i] = x
            py[i] = y
            var cx = x >> 12
            var cy = y >> 12
            if cx > 15 { cx = 15 }
            if cy > 15 { cy = 15 }
            let cell = (cy << 4) | cx
            nxtB[i] = head[cell]
            head[cell] = i
        }

        for i in 0..<n {
            var cx = px[i] >> 12
            var cy = py[i] >> 12
            if cx > 15 { cx = 15 }
            if cy > 15 { cy = 15 }
            let y0 = cy > 0 ? cy - 1 : 0
            let y1 = cy < 15 ? cy + 1 : 15
            let x0 = cx > 0 ? cx - 1 : 0
            let x1 = cx < 15 ? cx + 1 : 15
            for ny in y0...y1 {
                for nx in x0...x1 {
                    var j = head[(ny << 4) | nx]
                    while j != -1 {
                        if j > i {
                            let dx = px[j] - px[i]
                            let dy = py[j] - py[i]
                            let rsum = rad[i] + rad[j]
                            let dist2 = dx * dx + dy * dy
                            if dist2 < rsum * rsum && dist2 > 0 {
                                collisions += 1
                                var dist = isqrt64(dist2)
                                if dist < 1 { dist = 1 }
                                let half = (rsum - dist + 1) >> 1
                                let sx = sdiv(dx * half, dist)
                                let sy = sdiv(dy * half, dist)
                                px[i] -= sx
                                py[i] -= sy
                                px[j] += sx
                                py[j] += sy
                                let vn = (vx[j] - vx[i]) * dx + (vy[j] - vy[i]) * dy
                                if vn < 0 {
                                    let ix = sdiv(vn * dx, dist2)
                                    let iy = sdiv(vn * dy, dist2)
                                    vx[i] += ix
                                    vy[i] += iy
                                    vx[j] -= ix
                                    vy[j] -= iy
                                }
                            }
                        }
                        j = nxtB[j]
                    }
                }
            }
        }
    }

    var ck = 0
    for i in 0..<n {
        let v = (px[i] + 100000) * 7 + (py[i] + 100000) * 13 + (vx[i] + 100000) * 17 + (vy[i] + 100000)
        ck = (ck * 31 + (v % modV)) % modV
    }

    print("\(collisions)\n\(ck)")
}

run()
