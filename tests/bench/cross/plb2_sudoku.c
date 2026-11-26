#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    int r_tbl[2916];
    int c_tbl[2916];
} SudokuAux;

static void init_sudoku_aux(SudokuAux *aux) {
    int nr[324] = {0};
    for (int row = 0; row < 9; row++) {
        for (int col = 0; col < 9; col++) {
            for (int k = 0; k < 9; k++) {
                int r = (row * 9 + col) * 9 + k;
                int c0 = row * 9 + col;
                int c1 = 81 + row * 9 + k;
                int c2 = 162 + col * 9 + k;
                int c3 = 243 + ((row / 3) * 3 + (col / 3)) * 9 + k;
                int base = r * 4;
                aux->c_tbl[base] = c0;
                aux->c_tbl[base + 1] = c1;
                aux->c_tbl[base + 2] = c2;
                aux->c_tbl[base + 3] = c3;
                aux->r_tbl[c0 * 9 + nr[c0]++] = r;
                aux->r_tbl[c1 * 9 + nr[c1]++] = r;
                aux->r_tbl[c2 * 9 + nr[c2]++] = r;
                aux->r_tbl[c3 * 9 + nr[c3]++] = r;
            }
        }
    }
}

static int sd_update(const SudokuAux *aux, int *sr, int *sc, int r, int v) {
    int min_sc = 10;
    int min_c = 0;
    int r_base = r * 4;
    for (int c2 = 0; c2 < 4; c2++) {
        sc[aux->c_tbl[r_base + c2]] += v << 7;
    }
    for (int c2 = 0; c2 < 4; c2++) {
        int c = aux->c_tbl[r_base + c2];
        int rc_base = c * 9;
        if (v > 0) {
            for (int j = 0; j < 9; j++) {
                int rr = aux->r_tbl[rc_base + j];
                sr[rr]++;
                if (sr[rr] == 1) {
                    int rr_base = rr * 4;
                    for (int k = 0; k < 4; k++) {
                        int cc = aux->c_tbl[rr_base + k];
                        sc[cc]--;
                        if (sc[cc] < min_sc) {
                            min_sc = sc[cc];
                            min_c = cc;
                        }
                    }
                }
            }
        } else {
            for (int j = 0; j < 9; j++) {
                int rr = aux->r_tbl[rc_base + j];
                sr[rr]--;
                if (sr[rr] == 0) {
                    int rr_base = rr * 4;
                    for (int k = 0; k < 4; k++) {
                        int cc = aux->c_tbl[rr_base + k];
                        sc[cc]++;
                    }
                }
            }
        }
    }
    return (min_sc << 16) | min_c;
}

static int64_t sd_solve(const SudokuAux *aux, const char *puzzle) {
    int sr[729] = {0};
    int sc[324];
    int cr[81];
    int cc[81];
    int64_t out[81] = {0};
    for (int i = 0; i < 324; i++) sc[i] = 9;
    for (int i = 0; i < 81; i++) {
        cr[i] = -1;
        cc[i] = -1;
    }

    int hints = 0;
    for (int i = 0; i < 81; i++) {
        char ch = puzzle[i];
        if (ch >= '1' && ch <= '9') {
            int a = ch - '1';
            int r = i * 9 + a;
            sd_update(aux, sr, sc, r, 1);
            out[i] = a + 1;
            hints++;
        }
    }

    int depth = 0;
    int dir = 1;
    int limit = 81 - hints;
    while (depth >= 0 && depth < limit) {
        if (dir == 1) {
            int m = 10;
            int min_c = 0;
            for (int c = 0; c < 324; c++) {
                if (sc[c] < m) {
                    m = sc[c];
                    min_c = c;
                    if (m < 2) break;
                }
            }
            if (m == 0 || m == 10) {
                if (m == 10) {
                    for (int c2 = 0; c2 < 324; c2++) {
                        if (sc[c2] < 128) {
                            m = 0;
                            break;
                        }
                    }
                    if (m == 10) break;
                }
                if (m == 0) {
                    cr[depth] = -1;
                    depth--;
                    dir = -1;
                    continue;
                }
            }
            cc[depth] = min_c;
            cr[depth] = -1;
        }
        int c = cc[depth];
        if (dir == -1 && cr[depth] >= 0) {
            sd_update(aux, sr, sc, aux->r_tbl[c * 9 + cr[depth]], -1);
        }
        int j = cr[depth] + 1;
        int rc_base = c * 9;
        while (j < 9) {
            if (sr[aux->r_tbl[rc_base + j]] == 0) break;
            j++;
        }
        if (j < 9) {
            cr[depth] = j;
            int r = aux->r_tbl[rc_base + j];
            int ret = sd_update(aux, sr, sc, r, 1);
            if ((ret >> 16) == 0) {
                sd_update(aux, sr, sc, r, -1);
                dir = 0;
            } else {
                depth++;
                dir = 1;
            }
        } else {
            cr[depth] = -1;
            depth--;
            dir = -1;
        }
    }

    for (int j = 0; j < depth; j++) {
        int c = cc[j];
        int r = aux->r_tbl[c * 9 + cr[j]];
        out[r / 9] = (r % 9) + 1;
    }

    int64_t chk = 0;
    for (int i = 0; i < 81; i++) {
        chk = (chk * 31 + out[i]) % 1000000007;
    }
    return chk;
}

int main(void) {
    SudokuAux aux;
    init_sudoku_aux(&aux);
    const char *puzzles[10] = {
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
    };

    int64_t pow31 = 1;
    for (int k = 0; k < 81; k++) {
        pow31 = (pow31 * 31) % 1000000007;
    }

    int64_t total = 0;
    for (int round = 0; round < 20; round++) {
        for (int p_idx = 0; p_idx < 10; p_idx++) {
            int64_t c = sd_solve(&aux, puzzles[p_idx]);
            total = (total * pow31 + c) % 1000000007;
        }
    }
    printf("%lld\n", (long long)total);
    return 0;
}
