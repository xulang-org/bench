package main

import "fmt"

func main() {
	prog := ",+++++++++++++[>+++++++++++++++++++++++++++++++++++++[>+++++++++++++++++++++++++++++++[>+++++++++++++++++++[>+++>+++++<<-]<-]<-]>>>.>.<<<<<[>>>>+>>+<<<<<<-]>>>>>>[<<<<<<+>>>>>>-]<<.<<<<-]"
	ops := make([]int64, 0, len(prog))
	for i := 0; i < len(prog); i++ {
		c := int64(prog[i])
		if c == 62 || c == 60 || c == 43 || c == 45 || c == 46 || c == 44 || c == 91 || c == 93 {
			ops = append(ops, c)
		}
	}
	n := int64(len(ops))
	jmp := make([]int64, n)
	st := make([]int64, n)
	sp := 0
	for i := int64(0); i < n; i++ {
		if ops[i] == 91 {
			st[sp] = i
			sp++
		} else if ops[i] == 93 {
			sp--
			j := st[sp]
			jmp[j] = i
			jmp[i] = j
		}
	}

	tape := make([]int64, 30000)
	var outCnt int64
	var s1 int64
	var s2 int64
	for seed := int64(1); seed <= 4; seed++ {
		for j := 0; j < 30000; j++ {
			tape[j] = 0
		}
		var pc int64
		var dp int64
		var ip int64
		for pc < n {
			op := ops[pc]
			if op == 62 {
				dp++
			} else if op == 60 {
				dp--
			} else if op == 43 {
				tape[dp] = (tape[dp] + 1) & 255
			} else if op == 45 {
				tape[dp] = (tape[dp] + 255) & 255
			} else if op == 46 {
				b := tape[dp]
				outCnt++
				s1 = (s1 + b) % 255
				s2 = (s2 + s1) % 255
			} else if op == 44 {
				if ip == 0 {
					tape[dp] = seed
					ip = 1
				} else {
					tape[dp] = 0
				}
			} else if op == 91 {
				if tape[dp] == 0 {
					pc = jmp[pc]
				}
			} else if op == 93 {
				if tape[dp] != 0 {
					pc = jmp[pc]
				}
			}
			pc++
		}
	}
	fmt.Println(outCnt)
	fmt.Println((s2 << 8) | s1)
}
