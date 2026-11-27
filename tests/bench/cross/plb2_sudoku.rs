struct SudokuAux {
    r_tbl: [usize; 2916],
    c_tbl: [usize; 2916],
}

fn new_sudoku_aux() -> SudokuAux {
    let mut r_tbl = [0usize; 2916];
    let mut c_tbl = [0usize; 2916];
    let mut nr = [0usize; 324];
    for row in 0..9 {
        for col in 0..9 {
            for k in 0..9 {
                let r = (row * 9 + col) * 9 + k;
                let c0 = row * 9 + col;
                let c1 = 81 + row * 9 + k;
                let c2 = 162 + col * 9 + k;
                let c3 = 243 + ((row / 3) * 3 + (col / 3)) * 9 + k;
                let base = r * 4;
                c_tbl[base] = c0;
                c_tbl[base + 1] = c1;
                c_tbl[base + 2] = c2;
                c_tbl[base + 3] = c3;
                r_tbl[c0 * 9 + nr[c0]] = r;
                nr[c0] += 1;
                r_tbl[c1 * 9 + nr[c1]] = r;
                nr[c1] += 1;
                r_tbl[c2 * 9 + nr[c2]] = r;
                nr[c2] += 1;
                r_tbl[c3 * 9 + nr[c3]] = r;
                nr[c3] += 1;
            }
        }
    }
    SudokuAux { r_tbl, c_tbl }
}

fn sd_update(aux: &SudokuAux, sr: &mut [i32], sc: &mut [i32], r: usize, v: i32) -> i32 {
    let mut min_sc = 10i32;
    let mut min_c = 0i32;
    let r_base = r * 4;
    for c2 in 0..4 {
        sc[aux.c_tbl[r_base + c2]] += v << 7;
    }
    for c2 in 0..4 {
        let c = aux.c_tbl[r_base + c2];
        let rc_base = c * 9;
        if v > 0 {
            for j in 0..9 {
                let rr = aux.r_tbl[rc_base + j];
                sr[rr] += 1;
                if sr[rr] == 1 {
                    let rr_base = rr * 4;
                    for k in 0..4 {
                        let cc = aux.c_tbl[rr_base + k];
                        sc[cc] -= 1;
                        if sc[cc] < min_sc {
                            min_sc = sc[cc];
                            min_c = cc as i32;
                        }
                    }
                }
            }
        } else {
            for j in 0..9 {
                let rr = aux.r_tbl[rc_base + j];
                sr[rr] -= 1;
                if sr[rr] == 0 {
                    let rr_base = rr * 4;
                    for k in 0..4 {
                        let cc = aux.c_tbl[rr_base + k];
                        sc[cc] += 1;
                    }
                }
            }
        }
    }
    (min_sc << 16) | min_c
}

fn sd_solve(aux: &SudokuAux, puzzle: &[u8]) -> i64 {
    let mut sr = [0i32; 729];
    let mut sc = [9i32; 324];
    let mut cr = [-1i32; 81];
    let mut cc = [0usize; 81];
    let mut out = [0i64; 81];

    let mut hints = 0usize;
    for i in 0..81 {
        let ch = puzzle[i];
        if ch >= b'1' && ch <= b'9' {
            let a = (ch - b'1') as usize;
            let r = i * 9 + a;
            sd_update(aux, &mut sr, &mut sc, r, 1);
            out[i] = (a + 1) as i64;
            hints += 1;
        }
    }

    let mut depth: isize = 0;
    let mut dir: i32 = 1;
    let limit = (81 - hints) as isize;
    while depth >= 0 && depth < limit {
        let du = depth as usize;
        if dir == 1 {
            let mut m = 10i32;
            let mut min_c = 0usize;
            for c in 0..324 {
                if sc[c] < m {
                    m = sc[c];
                    min_c = c;
                    if m < 2 {
                        break;
                    }
                }
            }
            if m == 0 || m == 10 {
                if m == 10 {
                    for c2 in 0..324 {
                        if sc[c2] < 128 {
                            m = 0;
                            break;
                        }
                    }
                    if m == 10 {
                        break;
                    }
                }
                if m == 0 {
                    cr[du] = -1;
                    depth -= 1;
                    dir = -1;
                    continue;
                }
            }
            cc[du] = min_c;
            cr[du] = -1;
        }
        let c = cc[du];
        if dir == -1 && cr[du] >= 0 {
            sd_update(aux, &mut sr, &mut sc, aux.r_tbl[c * 9 + cr[du] as usize], -1);
        }
        let mut j = (cr[du] + 1) as usize;
        let rc_base = c * 9;
        while j < 9 {
            if sr[aux.r_tbl[rc_base + j]] == 0 {
                break;
            }
            j += 1;
        }
        if j < 9 {
            cr[du] = j as i32;
            let r = aux.r_tbl[rc_base + j];
            let ret = sd_update(aux, &mut sr, &mut sc, r, 1);
            if (ret >> 16) == 0 {
                sd_update(aux, &mut sr, &mut sc, r, -1);
                dir = 0;
            } else {
                depth += 1;
                dir = 1;
            }
        } else {
            cr[du] = -1;
            depth -= 1;
            dir = -1;
        }
    }

    for j in 0..(depth as usize) {
        let c = cc[j];
        let r = aux.r_tbl[c * 9 + cr[j] as usize];
        out[r / 9] = ((r % 9) + 1) as i64;
    }

    let mut chk: i64 = 0;
    for i in 0..81 {
        chk = (chk * 31 + out[i]) % 1000000007;
    }
    chk
}

fn main() {
    let aux = new_sudoku_aux();
    let puzzles: [&[u8]; 10] = [
        b"8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
        b"..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3..",
        b"4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......",
        b"52...6.........7.13...........4..8..6......5...........418.........3..2...87.....",
        b"6.....8.3.4.7.................5.4.7.3..2.....1.6.......2.....5.....8.6......1....",
        b"48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5....",
        b"....14....3....2...7..........9...3.6.1.............8.2.....1.4....5.6.....7.8...",
        b"......52..8.4......3...9...5.1...6..2..7........3.....6...1..........7.4.......3.",
        b"6.2.5.........3.4..........43...8....1....2........7..5..27...........81...6.....",
        b"1....7.9..3..2...8..96..5....53..9...1..8...26....4...3......1..4......7..7...3..",
    ];

    let mut pow31: i64 = 1;
    for _ in 0..81 {
        pow31 = (pow31 * 31) % 1000000007;
    }

    let mut total: i64 = 0;
    for _ in 0..20 {
        for p in puzzles.iter() {
            let c = sd_solve(&aux, p);
            total = (total * pow31 + c) % 1000000007;
        }
    }
    println!("{}", total);
}
