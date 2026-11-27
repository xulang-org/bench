let modV = 1000000007

func run() {
    let w = 512
    let h = 512
    let totalPx = w * h

    var img = [Int](repeating: 0, count: totalPx)
    var blur = [Int](repeating: 0, count: totalPx)
    var edges = [Int](repeating: 0, count: totalPx)

    var rng = 51515151
    for y in 0..<h {
        for x in 0..<w {
            rng = (rng * 1103515245 + 12345) & 2147483647
            var v = ((x * 3 + y * 5) >> 3) & 255
            let dx = x - 256
            let dy = y - 256
            if dx * dx + dy * dy < 16384 {
                v = (v + 110) & 255
            }
            if (x >= 80 && x < 200 && y >= 80 && y < 220) || (((x >> 5) + (y >> 5)) % 4) == 0 {
                v = (v ^ 96) & 255
            }
            img[y * w + x] = (v + (rng & 15)) & 255
        }
    }

    var edgeCnt = 0
    for _ in 0..<6 {
        for x in 0..<w {
            blur[x] = img[x]
            blur[(h - 1) * w + x] = img[(h - 1) * w + x]
        }
        for y in 1..<(h - 1) {
            let row = y * w
            blur[row] = img[row]
            blur[row + w - 1] = img[row + w - 1]
            for x in 1..<(w - 1) {
                let idx = row + x
                let s = img[idx - w - 1] + 2 * img[idx - w] + img[idx - w + 1]
                    + 2 * img[idx - 1] + 4 * img[idx] + 2 * img[idx + 1]
                    + img[idx + w - 1] + 2 * img[idx + w] + img[idx + w + 1]
                blur[idx] = s >> 4
            }
        }
        for y in 1..<(h - 1) {
            let row = y * w
            for x in 1..<(w - 1) {
                let idx = row + x
                var gx = -blur[idx - w - 1] + blur[idx - w + 1]
                    - 2 * blur[idx - 1] + 2 * blur[idx + 1]
                    - blur[idx + w - 1] + blur[idx + w + 1]
                var gy = -blur[idx - w - 1] - 2 * blur[idx - w] - blur[idx - w + 1]
                    + blur[idx + w - 1] + 2 * blur[idx + w] + blur[idx + w + 1]
                if gx < 0 { gx = -gx }
                if gy < 0 { gy = -gy }
                var mag = gx + gy
                if mag > 255 { mag = 255 }
                edges[idx] = mag
                if mag >= 64 {
                    edgeCnt += 1
                }
            }
        }
        for i in 0..<totalPx {
            img[i] = (blur[i] * 3 + edges[i]) >> 2
        }
    }

    var ck = 0
    for i in 0..<totalPx {
        ck = (ck * 131 + edges[i]) % modV
    }

    print("\(edgeCnt)\n\(ck)")
}

run()
