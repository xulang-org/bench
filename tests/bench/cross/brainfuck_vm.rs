fn main() {
    let prog = ",+++++++++++++[>+++++++++++++++++++++++++++++++++++++[>+++++++++++++++++++++++++++++++[>+++++++++++++++++++[>+++>+++++<<-]<-]<-]>>>.>.<<<<<[>>>>+>>+<<<<<<-]>>>>>>[<<<<<<+>>>>>>-]<<.<<<<-]";
    let mut ops: Vec<i64> = Vec::with_capacity(prog.len());
    for b in prog.bytes() {
        let c = b as i64;
        if c == 62 || c == 60 || c == 43 || c == 45 || c == 46 || c == 44 || c == 91 || c == 93 {
            ops.push(c);
        }
    }
    let n = ops.len();
    let mut jmp = vec![0usize; n];
    let mut st = vec![0usize; n];
    let mut sp = 0usize;
    for i in 0..n {
        if ops[i] == 91 {
            st[sp] = i;
            sp += 1;
        } else if ops[i] == 93 {
            sp -= 1;
            let j = st[sp];
            jmp[j] = i;
            jmp[i] = j;
        }
    }

    let mut tape = vec![0i64; 30000];
    let mut out_cnt: i64 = 0;
    let mut s1: i64 = 0;
    let mut s2: i64 = 0;
    for seed in 1i64..=4 {
        for v in tape.iter_mut() {
            *v = 0;
        }
        let mut pc = 0usize;
        let mut dp = 0usize;
        let mut ip = 0i64;
        while pc < n {
            let op = ops[pc];
            if op == 62 {
                dp += 1;
            } else if op == 60 {
                dp -= 1;
            } else if op == 43 {
                tape[dp] = (tape[dp] + 1) & 255;
            } else if op == 45 {
                tape[dp] = (tape[dp] + 255) & 255;
            } else if op == 46 {
                let b = tape[dp];
                out_cnt += 1;
                s1 = (s1 + b) % 255;
                s2 = (s2 + s1) % 255;
            } else if op == 44 {
                if ip == 0 {
                    tape[dp] = seed;
                    ip = 1;
                } else {
                    tape[dp] = 0;
                }
            } else if op == 91 {
                if tape[dp] == 0 {
                    pc = jmp[pc];
                }
            } else if op == 93 {
                if tape[dp] != 0 {
                    pc = jmp[pc];
                }
            }
            pc += 1;
        }
    }
    println!("{}\n{}", out_cnt, (s2 << 8) | s1);
}
