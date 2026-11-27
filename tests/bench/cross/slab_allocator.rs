const MOD_V: i64 = 1000000007;

struct SlabArena {
    mem: Vec<i64>,
    page_cls: [i64; 256],
    page_used: [i64; 256],
    page_head: [i64; 256],
    page_prev: [i64; 256],
    page_next: [i64; 256],
    page_in_list: [i64; 256],
    cls_head: [i64; 6],
    free_stack: [i64; 256],
    free_top: usize,
    class_sz: [usize; 6],
    page_allocs: i64,
    page_reclaims: i64,
}

impl SlabArena {
    fn new() -> Self {
        let mut free_stack = [0i64; 256];
        for i in 0..256 {
            free_stack[i] = (255 - i) as i64;
        }
        Self {
            mem: vec![0i64; 256 * 256],
            page_cls: [-1; 256],
            page_used: [0; 256],
            page_head: [-1; 256],
            page_prev: [-1; 256],
            page_next: [-1; 256],
            page_in_list: [0; 256],
            cls_head: [-1; 6],
            free_stack,
            free_top: 256,
            class_sz: [2, 4, 8, 16, 32, 64],
            page_allocs: 0,
            page_reclaims: 0,
        }
    }

    fn list_push(&mut self, cls: usize, pg: usize) {
        let h = self.cls_head[cls];
        self.page_prev[pg] = -1;
        self.page_next[pg] = h;
        if h != -1 {
            self.page_prev[h as usize] = pg as i64;
        }
        self.cls_head[cls] = pg as i64;
        self.page_in_list[pg] = 1;
    }

    fn list_remove(&mut self, cls: usize, pg: usize) {
        let pr = self.page_prev[pg];
        let nx = self.page_next[pg];
        if pr != -1 {
            self.page_next[pr as usize] = nx;
        } else {
            self.cls_head[cls] = nx;
        }
        if nx != -1 {
            self.page_prev[nx as usize] = pr;
        }
        self.page_prev[pg] = -1;
        self.page_next[pg] = -1;
        self.page_in_list[pg] = 0;
    }

    fn alloc(&mut self, cls: usize) -> i64 {
        let mut pg_i = self.cls_head[cls];
        if pg_i == -1 {
            if self.free_top == 0 {
                return -1;
            }
            self.free_top -= 1;
            pg_i = self.free_stack[self.free_top];
            let pg = pg_i as usize;
            self.page_allocs += 1;
            self.page_cls[pg] = cls as i64;
            self.page_used[pg] = 0;
            let sz = self.class_sz[cls];
            let base = pg << 8;
            let cnt = 256 / sz;
            for j in 0..(cnt - 1) {
                self.mem[base + j * sz] = (base + (j + 1) * sz) as i64;
            }
            self.mem[base + (cnt - 1) * sz] = -1;
            self.page_head[pg] = base as i64;
            self.list_push(cls, pg);
        }
        let pg = pg_i as usize;
        let ptr = self.page_head[pg];
        let nxt_ptr = self.mem[ptr as usize];
        self.page_head[pg] = nxt_ptr;
        self.page_used[pg] += 1;
        if nxt_ptr == -1 {
            self.list_remove(cls, pg);
        }
        ptr
    }

    fn free(&mut self, ptr: i64) {
        let pg = (ptr >> 8) as usize;
        let cls = self.page_cls[pg] as usize;
        let was_full = self.page_head[pg] == -1;
        self.mem[ptr as usize] = self.page_head[pg];
        self.page_head[pg] = ptr;
        self.page_used[pg] -= 1;
        if self.page_used[pg] == 0 {
            if self.page_in_list[pg] == 1 {
                self.list_remove(cls, pg);
            }
            self.page_cls[pg] = -1;
            self.page_head[pg] = -1;
            self.free_stack[self.free_top] = pg as i64;
            self.free_top += 1;
            self.page_reclaims += 1;
        } else if was_full {
            self.list_push(cls, pg);
        }
    }
}

fn main() {
    const LIVE: usize = 1024;
    let mut s = SlabArena::new();
    let mut rng: i64 = 31415926;
    let mut live_ptr = [-1i64; LIVE];
    let mut live_cls = [0usize; LIVE];

    let mut alloc_ok: i64 = 0;
    let mut ck: i64 = 0;
    for op_i in 0i64..600000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let slot = (rng & 1023) as usize;
        if (op_i & 4095) == 4095 {
            let mut k = 0usize;
            while k < LIVE {
                let p = live_ptr[k];
                if p != -1 {
                    let sz = s.class_sz[live_cls[k]];
                    let pu = p as usize;
                    ck = (ck * 31 + s.mem[pu] + s.mem[pu + sz - 1]) % MOD_V;
                    s.free(p);
                    live_ptr[k] = -1;
                }
                k += 3;
            }
        }
        if live_ptr[slot] != -1 {
            let p = live_ptr[slot];
            let sz = s.class_sz[live_cls[slot]];
            let pu = p as usize;
            ck = (ck * 31 + s.mem[pu] + s.mem[pu + sz - 1]) % MOD_V;
            s.free(p);
            live_ptr[slot] = -1;
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let r = rng % 100;
            let cls = if r < 35 {
                0
            } else if r < 60 {
                1
            } else if r < 78 {
                2
            } else if r < 90 {
                3
            } else if r < 97 {
                4
            } else {
                5
            };
            let p = s.alloc(cls);
            if p >= 0 {
                let sz = s.class_sz[cls];
                let pu = p as usize;
                let tag = (op_i * 13 + (cls as i64) * 7 + 1) % MOD_V;
                s.mem[pu] = tag;
                s.mem[pu + sz - 1] = (tag ^ (p * 3)) % MOD_V;
                live_ptr[slot] = p;
                live_cls[slot] = cls;
                alloc_ok += 1;
            }
        }
    }

    for k in 0..LIVE {
        let p = live_ptr[k];
        if p != -1 {
            let sz = s.class_sz[live_cls[k]];
            let pu = p as usize;
            ck = (ck * 31 + s.mem[pu] + s.mem[pu + sz - 1]) % MOD_V;
            s.free(p);
            live_ptr[k] = -1;
        }
    }
    ck = (ck * 37 + s.page_allocs * 17 + s.page_reclaims) % MOD_V;
    println!("{}\n{}", alloc_ok, ck);
}
