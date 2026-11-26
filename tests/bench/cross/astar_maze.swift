final class Heap {
    var f = [Int](repeating: 0, count: 32768)
    var n = [Int](repeating: 0, count: 32768)
    var len = 0

    func push(_ fval: Int, _ node: Int) {
        var i = len
        f[i] = fval
        n[i] = node
        len += 1
        while i > 0 {
            let p = (i - 1) / 2
            if f[p] > f[i] || (f[p] == f[i] && n[p] > n[i]) {
                let tf = f[p]; f[p] = f[i]; f[i] = tf
                let tn = n[p]; n[p] = n[i]; n[i] = tn
                i = p
            } else {
                break
            }
        }
    }

    func pop() -> Int {
        let top = n[0]
        len -= 1
        let sz = len
        if sz > 0 {
            f[0] = f[sz]
            n[0] = n[sz]
            var i = 0
            while true {
                let l = 2 * i + 1
                if l >= sz { break }
                let r = l + 1
                var best = l
                if r < sz && (f[r] < f[l] || (f[r] == f[l] && n[r] < n[l])) {
                    best = r
                }
                if f[best] < f[i] || (f[best] == f[i] && n[best] < n[i]) {
                    let tf = f[i]; f[i] = f[best]; f[best] = tf
                    let tn = n[i]; n[i] = n[best]; n[best] = tn
                    i = best
                } else {
                    break
                }
            }
        }
        return top
    }
}

func main() {
    let W = 81
    let H = 81
    let N = 6561
    let INF = 1000000000
    let start = 82
    let goal = 79 * 81 + 79
    let gx = 79
    let gy = 79

    var grid = [Int](repeating: 1, count: N)
    var gScore = [Int](repeating: INF, count: N)
    var closed = [Int](repeating: 0, count: N)
    var stkX = [Int](repeating: 0, count: N)
    var stkY = [Int](repeating: 0, count: N)
    let h = Heap()

    let dx = [0, 0, -2, 2]
    let dy = [-2, 2, 0, 0]
    var dirs = [0, 0, 0, 0]

    var sumD = 0
    var polyD = 0
    for m in 0..<60 {
        var rng = 100003 + m * 9973
        for i in 0..<N {
            grid[i] = 1
            gScore[i] = INF
            closed[i] = 0
        }
        grid[start] = 0
        var sp = 1
        stkX[0] = 1
        stkY[0] = 1
        while sp > 0 {
            let cx = stkX[sp - 1]
            let cy = stkY[sp - 1]
            var dc = 0
            for d in 0..<4 {
                let nx = cx + dx[d]
                let ny = cy + dy[d]
                if nx >= 1 && nx <= W - 2 && ny >= 1 && ny <= H - 2 && grid[ny * W + nx] == 1 {
                    dirs[dc] = d
                    dc += 1
                }
            }
            if dc == 0 {
                sp -= 1
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let pick = dirs[rng % dc]
                let nx = cx + dx[pick]
                let ny = cy + dy[pick]
                let mx = (cx + nx) / 2
                let my = (cy + ny) / 2
                grid[my * W + mx] = 0
                grid[ny * W + nx] = 0
                stkX[sp] = nx
                stkY[sp] = ny
                sp += 1
            }
        }

        for y in 1..<(H - 1) {
            for x in 1..<(W - 1) {
                let idx = y * W + x
                if grid[idx] == 1 {
                    if (grid[idx - 1] == 0 && grid[idx + 1] == 0) || (grid[idx - W] == 0 && grid[idx + W] == 0) {
                        rng = (rng * 1103515245 + 12345) & 2147483647
                        if (rng % 100) < 12 {
                            grid[idx] = 0
                        }
                    }
                }
            }
        }

        gScore[start] = 0
        h.len = 0
        h.push(156, start)
        var ans = -1
        while h.len > 0 {
            let u = h.pop()
            if closed[u] != 0 { continue }
            closed[u] = 1
            if u == goal {
                ans = gScore[u]
                break
            }
            let gu = gScore[u] + 1
            let ux = u % W
            let uy = u / W

            if uy > 0 {
                let v = u - W
                if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
                    gScore[v] = gu
                    let dhx = abs(gx - ux)
                    let dhy = abs(gy - (uy - 1))
                    h.push(gu + dhx + dhy, v)
                }
            }
            if uy + 1 < H {
                let v = u + W
                if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
                    gScore[v] = gu
                    let dhx = abs(gx - ux)
                    let dhy = abs(gy - (uy + 1))
                    h.push(gu + dhx + dhy, v)
                }
            }
            if ux > 0 {
                let v = u - 1
                if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
                    gScore[v] = gu
                    let dhx = abs(gx - (ux - 1))
                    let dhy = abs(gy - uy)
                    h.push(gu + dhx + dhy, v)
                }
            }
            if ux + 1 < W {
                let v = u + 1
                if grid[v] == 0 && closed[v] == 0 && gu < gScore[v] {
                    gScore[v] = gu
                    let dhx = abs(gx - (ux + 1))
                    let dhy = abs(gy - uy)
                    h.push(gu + dhx + dhy, v)
                }
            }
        }
        sumD += ans
        polyD = (polyD * 1000003 + ans) % 1000000007
    }
    print(sumD)
    print(polyD)
}

main()
