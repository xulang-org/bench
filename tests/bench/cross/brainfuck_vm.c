#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const char *prog = ",+++++++++++++[>+++++++++++++++++++++++++++++++++++++[>+++++++++++++++++++++++++++++++[>+++++++++++++++++++[>+++>+++++<<-]<-]<-]>>>.>.<<<<<[>>>>+>>+<<<<<<-]>>>>>>[<<<<<<+>>>>>>-]<<.<<<<-]";
    int64_t ops[256];
    int64_t jmp[256];
    int64_t st[256];
    int64_t n = 0;
    for (int64_t i = 0; prog[i] != '\0'; i++) {
        int64_t c = (int64_t)(unsigned char)prog[i];
        if (c == 62 || c == 60 || c == 43 || c == 45 || c == 46 || c == 44 || c == 91 || c == 93) {
            ops[n] = c;
            jmp[n] = 0;
            n += 1;
        }
    }
    int64_t sp = 0;
    for (int64_t i = 0; i < n; i++) {
        if (ops[i] == 91) {
            st[sp++] = i;
        } else if (ops[i] == 93) {
            int64_t j = st[--sp];
            jmp[j] = i;
            jmp[i] = j;
        }
    }

    int64_t *tape = (int64_t *)malloc(30000 * sizeof(int64_t));
    int64_t out_cnt = 0;
    int64_t s1 = 0;
    int64_t s2 = 0;
    for (int64_t seed = 1; seed <= 4; seed++) {
        for (int64_t j = 0; j < 30000; j++) {
            tape[j] = 0;
        }
        int64_t pc = 0;
        int64_t dp = 0;
        int64_t ip = 0;
        while (pc < n) {
            int64_t op = ops[pc];
            if (op == 62) {
                dp += 1;
            } else if (op == 60) {
                dp -= 1;
            } else if (op == 43) {
                tape[dp] = (tape[dp] + 1) & 255;
            } else if (op == 45) {
                tape[dp] = (tape[dp] + 255) & 255;
            } else if (op == 46) {
                int64_t b = tape[dp];
                out_cnt += 1;
                s1 = (s1 + b) % 255;
                s2 = (s2 + s1) % 255;
            } else if (op == 44) {
                if (ip == 0) {
                    tape[dp] = seed;
                    ip = 1;
                } else {
                    tape[dp] = 0;
                }
            } else if (op == 91) {
                if (tape[dp] == 0) {
                    pc = jmp[pc];
                }
            } else if (op == 93) {
                if (tape[dp] != 0) {
                    pc = jmp[pc];
                }
            }
            pc += 1;
        }
    }
    free(tape);
    printf("%" PRId64 "\n%" PRId64 "\n", out_cnt, (s2 << 8) | s1);
    return 0;
}
