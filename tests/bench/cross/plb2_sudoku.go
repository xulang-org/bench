package main

import "fmt"

type SudokuAux struct {
	rTbl [2916]int
	cTbl [2916]int
}

func newSudokuAux() SudokuAux {
	var aux SudokuAux
	var nr [324]int
	for row := 0; row < 9; row++ {
		for col := 0; col < 9; col++ {
			for k := 0; k < 9; k++ {
				r := (row*9+col)*9 + k
				c0 := row*9 + col
				c1 := 81 + row*9 + k
				c2 := 162 + col*9 + k
				c3 := 243 + ((row/3)*3+(col/3))*9 + k
				base := r * 4
				aux.cTbl[base] = c0
				aux.cTbl[base+1] = c1
				aux.cTbl[base+2] = c2
				aux.cTbl[base+3] = c3
				aux.rTbl[c0*9+nr[c0]] = r
				nr[c0]++
				aux.rTbl[c1*9+nr[c1]] = r
				nr[c1]++
				aux.rTbl[c2*9+nr[c2]] = r
				nr[c2]++
				aux.rTbl[c3*9+nr[c3]] = r
				nr[c3]++
			}
		}
	}
	return aux
}

func sdUpdate(aux *SudokuAux, sr []int, sc []int, r int, v int) int {
	minSc := 10
	minC := 0
	rBase := r * 4
	for c2 := 0; c2 < 4; c2++ {
		sc[aux.cTbl[rBase+c2]] += v << 7
	}
	for c2 := 0; c2 < 4; c2++ {
		c := aux.cTbl[rBase+c2]
		rcBase := c * 9
		if v > 0 {
			for j := 0; j < 9; j++ {
				rr := aux.rTbl[rcBase+j]
				sr[rr]++
				if sr[rr] == 1 {
					rrBase := rr * 4
					for k := 0; k < 4; k++ {
						cc := aux.cTbl[rrBase+k]
						sc[cc]--
						if sc[cc] < minSc {
							minSc = sc[cc]
							minC = cc
						}
					}
				}
			}
		} else {
			for j := 0; j < 9; j++ {
				rr := aux.rTbl[rcBase+j]
				sr[rr]--
				if sr[rr] == 0 {
					rrBase := rr * 4
					for k := 0; k < 4; k++ {
						cc := aux.cTbl[rrBase+k]
						sc[cc]++
					}
				}
			}
		}
	}
	return (minSc << 16) | minC
}

func sdSolve(aux *SudokuAux, puzzle string) int64 {
	var sr [729]int
	var sc [324]int
	var cr [81]int
	var cc [81]int
	var out [81]int64
	for i := 0; i < 324; i++ {
		sc[i] = 9
	}
	for i := 0; i < 81; i++ {
		cr[i] = -1
		cc[i] = -1
	}

	hints := 0
	for i := 0; i < 81; i++ {
		ch := puzzle[i]
		if ch >= '1' && ch <= '9' {
			a := int(ch - '1')
			r := i*9 + a
			sdUpdate(aux, sr[:], sc[:], r, 1)
			out[i] = int64(a + 1)
			hints++
		}
	}

	depth := 0
	dir := 1
	limit := 81 - hints
	for depth >= 0 && depth < limit {
		if dir == 1 {
			m := 10
			minC := 0
			for c := 0; c < 324; c++ {
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
					for c2 := 0; c2 < 324; c2++ {
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
					depth--
					dir = -1
					continue
				}
			}
			cc[depth] = minC
			cr[depth] = -1
		}
		c := cc[depth]
		if dir == -1 && cr[depth] >= 0 {
			sdUpdate(aux, sr[:], sc[:], aux.rTbl[c*9+cr[depth]], -1)
		}
		j := cr[depth] + 1
		rcBase := c * 9
		for j < 9 {
			if sr[aux.rTbl[rcBase+j]] == 0 {
				break
			}
			j++
		}
		if j < 9 {
			cr[depth] = j
			r := aux.rTbl[rcBase+j]
			ret := sdUpdate(aux, sr[:], sc[:], r, 1)
			if (ret >> 16) == 0 {
				sdUpdate(aux, sr[:], sc[:], r, -1)
				dir = 0
			} else {
				depth++
				dir = 1
			}
		} else {
			cr[depth] = -1
			depth--
			dir = -1
		}
	}

	for j := 0; j < depth; j++ {
		c := cc[j]
		r := aux.rTbl[c*9+cr[j]]
		out[r/9] = int64((r % 9) + 1)
	}

	var chk int64 = 0
	for i := 0; i < 81; i++ {
		chk = (chk*31 + out[i]) % 1000000007
	}
	return chk
}

func main() {
	aux := newSudokuAux()
	puzzles := [10]string{
		"8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
		"..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3..",
		"4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......",
		"52...6.........7.13...........4..8..6......5...........418.........3..2...87.....",
		"6.....8.3.4.7.................5.4.7.3..2.....1.6.......2.....5.....8.6......1....",
		"48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5....",
		"....14....3....2...7..........9...3.6.1.............8.2.....1.4....5.6.....7.8...",
		"......52..8.4......3...9...5.1...6..2..7........3.....6...1..........7.4.......3.",
		"6.2.5.........3.4..........43...8....1....2........7..5..27...........81...6.....",
		"1....7.9..3..2...8..96..5....53..9...1..8...26....4...3......1..4......7..7...3..",
	}

	var pow31 int64 = 1
	for k := 0; k < 81; k++ {
		pow31 = (pow31 * 31) % 1000000007
	}

	var total int64 = 0
	for round := 0; round < 20; round++ {
		for pIdx := 0; pIdx < 10; pIdx++ {
			c := sdSolve(&aux, puzzles[pIdx])
			total = (total*pow31 + c) % 1000000007
		}
	}
	fmt.Println(total)
}
