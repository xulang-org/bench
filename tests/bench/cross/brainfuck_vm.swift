func main() {
    let prog = ",+++++++++++++[>+++++++++++++++++++++++++++++++++++++[>+++++++++++++++++++++++++++++++[>+++++++++++++++++++[>+++>+++++<<-]<-]<-]>>>.>.<<<<<[>>>>+>>+<<<<<<-]>>>>>>[<<<<<<+>>>>>>-]<<.<<<<-]"
    var ops: [Int] = []
    for b in prog.utf8 {
        let c = Int(b)
        if c == 62 || c == 60 || c == 43 || c == 45 || c == 46 || c == 44 || c == 91 || c == 93 {
            ops.append(c)
        }
    }
    let n = ops.count
    var jmp = [Int](repeating: 0, count: n)
    var st = [Int](repeating: 0, count: n)
    var sp = 0
    for i in 0..<n {
        if ops[i] == 91 {
            st[sp] = i
            sp += 1
        } else if ops[i] == 93 {
            sp -= 1
            let j = st[sp]
            jmp[j] = i
            jmp[i] = j
        }
    }

    var tape = [Int](repeating: 0, count: 30000)
    var outCnt = 0
    var s1 = 0
    var s2 = 0
    for seed in 1...4 {
        for j in 0..<30000 {
            tape[j] = 0
        }
        var pc = 0
        var dp = 0
        var ip = 0
        while pc < n {
            let op = ops[pc]
            if op == 62 {
                dp += 1
            } else if op == 60 {
                dp -= 1
            } else if op == 43 {
                tape[dp] = (tape[dp] + 1) & 255
            } else if op == 45 {
                tape[dp] = (tape[dp] + 255) & 255
            } else if op == 46 {
                let b = tape[dp]
                outCnt += 1
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
            pc += 1
        }
    }
    print(outCnt)
    print((s2 << 8) | s1)
}

main()
