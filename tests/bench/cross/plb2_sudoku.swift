struct SudokuAux {
    var rTbl: [Int]
    var cTbl: [Int]

    init() {
        var rTbl = [Int](repeating: 0, count: 2916)
        var cTbl = [Int](repeating: 0, count: 2916)
        var nr = [Int](repeating: 0, count: 324)
        for row in 0..<9 {
            for col in 0..<9 {
                for k in 0..<9 {
                    let r = (row * 9 + col) * 9 + k
                    let c0 = row * 9 + col
                    let c1 = 81 + row * 9 + k
                    let c2 = 162 + col * 9 + k
                    let c3 = 243 + ((row / 3) * 3 + (col / 3)) * 9 + k
                    let base = r * 4
                    cTbl[base] = c0
                    cTbl[base + 1] = c1
                    cTbl[base + 2] = c2
                    cTbl[base + 3] = c3
                    rTbl[c0 * 9 + nr[c0]] = r
                    nr[c0] += 1
                    rTbl[c1 * 9 + nr[c1]] = r
                    nr[c1] += 1
                    rTbl[c2 * 9 + nr[c2]] = r
                    nr[c2] += 1
                    rTbl[c3 * 9 + nr[c3]] = r
                    nr[c3] += 1
                }
            }
        }
        self.rTbl = rTbl
        self.cTbl = cTbl
    }
}

func sdUpdate(_ aux: SudokuAux, _ sr: inout [Int], _ sc: inout [Int], _ r: Int, _ v: Int) -> Int {
    var minSc = 10
    var minC = 0
    let rBase = r * 4
    for c2 in 0..<4 {
        sc[aux.cTbl[rBase + c2]] += v * 128
    }
    for c2 in 0..<4 {
        let c = aux.cTbl[rBase + c2]
        let rcBase = c * 9
        if v > 0 {
            for j in 0..<9 {
                let rr = aux.rTbl[rcBase + j]
                sr[rr] += 1
                if sr[rr] == 1 {
                    let rrBase = rr * 4
                    for k in 0..<4 {
                        let cc = aux.cTbl[rrBase + k]
                        sc[cc] -= 1
                        if sc[cc] < minSc {
                            minSc = sc[cc]
                            minC = cc
                        }
                    }
                }
            }
        } else {
            for j in 0..<9 {
                let rr = aux.rTbl[rcBase + j]
                sr[rr] -= 1
                if sr[rr] == 0 {
                    let rrBase = rr * 4
                    for k in 0..<4 {
                        let cc = aux.cTbl[rrBase + k]
                        sc[cc] += 1
                    }
                }
            }
        }
    }
    return (minSc << 16) | minC
}

func sdSolve(_ aux: SudokuAux, _ puzzle: [UInt8]) -> Int64 {
    var sr = [Int](repeating: 0, count: 729)
    var sc = [Int](repeating: 9, count: 324)
    var cr = [Int](repeating: -1, count: 81)
    var cc = [Int](repeating: -1, count: 81)
    var out = [Int64](repeating: 0, count: 81)

    var hints = 0
    for i in 0..<81 {
        let ch = puzzle[i]
        if ch >= 49 && ch <= 57 {
            let a = Int(ch - 49)
            let r = i * 9 + a
            _ = sdUpdate(aux, &sr, &sc, r, 1)
            out[i] = Int64(a + 1)
            hints += 1
        }
    }

    var depth = 0
    var dir = 1
    let limit = 81 - hints
    while depth >= 0 && depth < limit {
        if dir == 1 {
            var m = 10
            var minC = 0
            for c in 0..<324 {
                if sc[c] < m {
                    m = sc[c]
                    minC = c
                    if m < 2 {
                        break
                    }
                }
            }
            if m == 0 || m == 10 {
                if m == 10 {
                    for c2 in 0..<324 {
                        if sc[c2] < 128 {
                            m = 0
                            break
                        }
                    }
                    if m == 10 {
                        break
                    }
                }
                if m == 0 {
                    cr[depth] = -1
                    depth -= 1
                    dir = -1
                    continue
                }
            }
            cc[depth] = minC
            cr[depth] = -1
        }
        let c = cc[depth]
        if dir == -1 && cr[depth] >= 0 {
            _ = sdUpdate(aux, &sr, &sc, aux.rTbl[c * 9 + cr[depth]], -1)
        }
        var j = cr[depth] + 1
        let rcBase = c * 9
        while j < 9 {
            if sr[aux.rTbl[rcBase + j]] == 0 {
                break
            }
            j += 1
        }
        if j < 9 {
            cr[depth] = j
            let r = aux.rTbl[rcBase + j]
            let ret = sdUpdate(aux, &sr, &sc, r, 1)
            if (ret >> 16) == 0 {
                _ = sdUpdate(aux, &sr, &sc, r, -1)
                dir = 0
            } else {
                depth += 1
                dir = 1
            }
        } else {
            cr[depth] = -1
            depth -= 1
            dir = -1
        }
    }

    for j in 0..<depth {
        let c = cc[j]
        let r = aux.rTbl[c * 9 + cr[j]]
        out[r / 9] = Int64((r % 9) + 1)
    }

    var chk: Int64 = 0
    for i in 0..<81 {
        chk = (chk &* 31 &+ out[i]) % 1000000007
    }
    return chk
}

func main() {
    let aux = SudokuAux()
    let puzzles: [[UInt8]] = [
        Array("8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..".utf8),
        Array("..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3..".utf8),
        Array("4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......".utf8),
        Array("52...6.........7.13...........4..8..6......5...........418.........3..2...87.....".utf8),
        Array("6.....8.3.4.7.................5.4.7.3..2.....1.6.......2.....5.....8.6......1....".utf8),
        Array("48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5....".utf8),
        Array("....14....3....2...7..........9...3.6.1.............8.2.....1.4....5.6.....7.8...".utf8),
        Array("......52..8.4......3...9...5.1...6..2..7........3.....6...1..........7.4.......3.".utf8),
        Array("6.2.5.........3.4..........43...8....1....2........7..5..27...........81...6.....".utf8),
        Array("1....7.9..3..2...8..96..5....53..9...1..8...26....4...3......1..4......7..7...3..".utf8),
    ]

    var pow31: Int64 = 1
    for _ in 0..<81 {
        pow31 = (pow31 &* 31) % 1000000007
    }

    var total: Int64 = 0
    for _ in 0..<20 {
        for p in puzzles {
            let c = sdSolve(aux, p)
            total = (total &* pow31 &+ c) % 1000000007
        }
    }
    print(total)
}

main()
