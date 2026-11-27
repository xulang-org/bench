func run() {
    var cx = [Double](repeating: 0.0, count: 16)
    var cy = [Double](repeating: 0.0, count: 16)
    var cz = [Double](repeating: 0.0, count: 16)
    var cr = [Double](repeating: 0.0, count: 16)
    var sr = [Double](repeating: 0.0, count: 16)
    var sg = [Double](repeating: 0.0, count: 16)
    var sb = [Double](repeating: 0.0, count: 16)
    var refl = [Double](repeating: 0.0, count: 16)

    cx[0] = 0.0
    cy[0] = -1001.5
    cz[0] = -6.0
    cr[0] = 1000.0
    sr[0] = 0.45
    sg[0] = 0.48
    sb[0] = 0.52
    refl[0] = 0.25

    var rng = 44556677
    for i in 1..<16 {
        let row = (i - 1) / 5
        let col = (i - 1) % 5
        rng = (rng * 1103515245 + 12345) & 2147483647
        cx[i] = -3.2 + Double(col) * 1.6 + Double((rng % 41) - 20) / 128.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        cy[i] = -0.7 + Double(row) * 1.1 + Double((rng % 33) - 16) / 128.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        cz[i] = -4.2 - Double(row) * 1.8 - Double(rng % 33) / 64.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        cr[i] = 0.45 + Double(rng % 17) / 64.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        sr[i] = 0.25 + Double(rng % 48) / 64.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        sg[i] = 0.25 + Double(rng % 48) / 64.0
        rng = (rng * 1103515245 + 12345) & 2147483647
        sb[i] = 0.25 + Double(rng % 48) / 64.0
        refl[i] = 0.2 + Double(i % 4) * 0.15
    }

    let lx = 0.5773502691896258
    let ly = 0.5773502691896258
    let lz = 0.5773502691896258
    let w = 320
    let h = 240
    var hitCount = 0
    var totalLum = 0.0

    for py in 0..<h {
        let v = (0.5 - (Double(py) + 0.5) / 240.0) * 1.5
        for px in 0..<w {
            let u = ((Double(px) + 0.5) / 320.0 - 0.5) * 2.0
            let invL = 1.0 / (u * u + v * v + 1.0).squareRoot()
            var ox = 0.0
            var oy = 0.2
            var oz = 0.0
            var dx = u * invL
            var dy = v * invL
            var dz = -1.0 * invL
            var att = 1.0
            var pr = 0.0
            var pg = 0.0
            var pb = 0.0

            for _ in 0..<3 {
                var bestT = 1.0e18
                var bestI = -1
                for i in 0..<16 {
                    let ocx = ox - cx[i]
                    let ocy = oy - cy[i]
                    let ocz = oz - cz[i]
                    let b = ocx * dx + ocy * dy + ocz * dz
                    let c = ocx * ocx + ocy * ocy + ocz * ocz - cr[i] * cr[i]
                    let disc = b * b - c
                    if disc > 0.0 {
                        let t = -b - disc.squareRoot()
                        if t > 0.0005 && t < bestT {
                            bestT = t
                            bestI = i
                        }
                    }
                }
                if bestI == -1 {
                    let sky = 0.5 * (dy + 1.0)
                    pr += att * (0.2 + 0.4 * sky)
                    pg += att * (0.3 + 0.4 * sky)
                    pb += att * (0.5 + 0.4 * sky)
                    break
                }
                hitCount += 1
                let hx = ox + dx * bestT
                let hy = oy + dy * bestT
                let hz = oz + dz * bestT
                let invR = 1.0 / cr[bestI]
                let nx = (hx - cx[bestI]) * invR
                let ny = (hy - cy[bestI]) * invR
                let nz = (hz - cz[bestI]) * invR

                let sox = hx + nx * 0.002
                let soy = hy + ny * 0.002
                let soz = hz + nz * 0.002
                var inShadow = false
                for j in 0..<16 {
                    let ocx = sox - cx[j]
                    let ocy = soy - cy[j]
                    let ocz = soz - cz[j]
                    let b = ocx * lx + ocy * ly + ocz * lz
                    let c = ocx * ocx + ocy * ocy + ocz * ocz - cr[j] * cr[j]
                    let disc = b * b - c
                    if disc > 0.0 {
                        let st = -b - disc.squareRoot()
                        if st > 0.0005 {
                            inShadow = true
                            break
                        }
                    }
                }

                var diff = 0.0
                var spec = 0.0
                if !inShadow {
                    let ndotl = nx * lx + ny * ly + nz * lz
                    if ndotl > 0.0 {
                        diff = ndotl
                        let hx2 = lx - dx
                        let hy2 = ly - dy
                        let hz2 = lz - dz
                        let hinv = 1.0 / (hx2 * hx2 + hy2 * hy2 + hz2 * hz2).squareRoot()
                        let ndoth = (nx * hx2 + ny * hy2 + nz * hz2) * hinv
                        if ndoth > 0.0 {
                            let s2 = ndoth * ndoth
                            let s4 = s2 * s2
                            spec = s4 * s4 * 0.5
                        }
                    }
                }
                let shade = 0.1 + 0.75 * diff
                let kr = refl[bestI]
                pr += att * (1.0 - kr) * (sr[bestI] * shade + spec)
                pg += att * (1.0 - kr) * (sg[bestI] * shade + spec)
                pb += att * (1.0 - kr) * (sb[bestI] * shade + spec)
                att *= kr
                if att < 0.02 {
                    break
                }
                let dot2 = 2.0 * (dx * nx + dy * ny + dz * nz)
                dx -= dot2 * nx
                dy -= dot2 * ny
                dz -= dot2 * nz
                ox = sox
                oy = soy
                oz = soz
            }
            totalLum += pr + pg + pb
        }
    }

    print("\(hitCount)\n\(Int((totalLum * 10.0 + 0.5).rounded(.down)))")
}

run()
