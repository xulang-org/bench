#[derive(Clone, Copy)]
struct HeapItem {
    freq: i32,
    nid: i32,
}

struct MinHeap {
    items: [HeapItem; 256],
    size: usize,
}

impl MinHeap {
    fn new() -> Self {
        MinHeap {
            items: [HeapItem { freq: 0, nid: 0 }; 256],
            size: 0,
        }
    }

    #[inline(always)]
    fn less(a: HeapItem, b: HeapItem) -> bool {
        if a.freq != b.freq {
            a.freq < b.freq
        } else {
            a.nid < b.nid
        }
    }

    fn push(&mut self, freq: i32, nid: i32) {
        let mut i = self.size;
        self.size += 1;
        let item = HeapItem { freq, nid };
        while i > 0 {
            let p = (i - 1) / 2;
            if Self::less(item, self.items[p]) {
                self.items[i] = self.items[p];
                i = p;
            } else {
                break;
            }
        }
        self.items[i] = item;
    }

    fn pop(&mut self) -> HeapItem {
        let top = self.items[0];
        self.size -= 1;
        let last = self.items[self.size];
        if self.size == 0 {
            return top;
        }
        let mut i = 0;
        while i * 2 + 1 < self.size {
            let left = i * 2 + 1;
            let right = left + 1;
            let mut best = left;
            if right < self.size && Self::less(self.items[right], self.items[left]) {
                best = right;
            }
            if Self::less(self.items[best], last) {
                self.items[i] = self.items[best];
                i = best;
            } else {
                break;
            }
        }
        self.items[i] = last;
        top
    }
}

struct HuffmanTree {
    nodes_freq: [i32; 256],
    nodes_ch: [i32; 256],
    nodes_left: [i32; 256],
    nodes_right: [i32; 256],
    codes: [i32; 64],
    code_lens: [i32; 64],
}

impl HuffmanTree {
    fn get_codes(&mut self, nid: usize, curr_code: i32, curr_len: i32) {
        if self.nodes_left[nid] == -1 && self.nodes_right[nid] == -1 {
            let ch = self.nodes_ch[nid] as usize;
            self.codes[ch] = curr_code;
            self.code_lens[ch] = curr_len;
            return;
        }
        self.get_codes(self.nodes_left[nid] as usize, (curr_code << 1) | 0, curr_len + 1);
        self.get_codes(self.nodes_right[nid] as usize, (curr_code << 1) | 1, curr_len + 1);
    }
}

fn isqrt(n: i64) -> i64 {
    if n <= 0 { return 0; }
    let mut x = n;
    let mut y = (x + 1) / 2;
    while y < x {
        x = y;
        y = (x + n / x) / 2;
    }
    x
}

fn main() {
    let mut raw = [0i32; 20000];
    let mut freqs = [0i32; 64];
    let mut seed = 123456789i64;
    for i in 0..20000 {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        let c = isqrt(seed % 4096) as i32;
        raw[i] = c;
        freqs[c as usize] += 1;
    }

    let mut tree = HuffmanTree {
        nodes_freq: [0; 256],
        nodes_ch: [0; 256],
        nodes_left: [-1; 256],
        nodes_right: [-1; 256],
        codes: [0; 64],
        code_lens: [0; 64],
    };

    let mut heap = MinHeap::new();
    let mut node_count = 0usize;

    for ch in 0..64 {
        if freqs[ch] > 0 {
            let nid = node_count;
            node_count += 1;
            tree.nodes_freq[nid] = freqs[ch];
            tree.nodes_ch[nid] = ch as i32;
            tree.nodes_left[nid] = -1;
            tree.nodes_right[nid] = -1;
            heap.push(freqs[ch], nid as i32);
        }
    }

    while heap.size > 1 {
        let item1 = heap.pop();
        let item2 = heap.pop();
        let pid = node_count;
        node_count += 1;
        tree.nodes_freq[pid] = item1.freq + item2.freq;
        tree.nodes_ch[pid] = -1;
        tree.nodes_left[pid] = item1.nid;
        tree.nodes_right[pid] = item2.nid;
        heap.push(tree.nodes_freq[pid], pid as i32);
    }

    let root = heap.pop().nid as usize;
    tree.get_codes(root, 0, 0);

    let mut bit_buf = Vec::with_capacity(10000);
    let mut bit_count = 0usize;
    let mut curr_word = 0u32;
    let mut curr_bits = 0usize;

    for &b in raw.iter() {
        let bu = b as usize;
        let c = tree.codes[bu];
        let l = tree.code_lens[bu];
        for bit_idx in (0..l).rev() {
            let bit = ((c >> bit_idx) & 1) as u32;
            curr_word = (curr_word << 1) | bit;
            curr_bits += 1;
            if curr_bits == 32 {
                bit_buf.push(curr_word);
                curr_word = 0;
                curr_bits = 0;
            }
            bit_count += 1;
        }
    }
    if curr_bits > 0 {
        curr_word = curr_word << (32 - curr_bits);
        bit_buf.push(curr_word);
    }

    let mut total_checksum = 0i64;
    for _ in 0..50 {
        let mut cur_node = root;
        let mut decoded_sum = 0i64;
        for i in 0..bit_count {
            let word_idx = i / 32;
            let bit_pos = 31 - (i % 32);
            let bit = (bit_buf[word_idx] >> bit_pos) & 1;
            if bit == 0 {
                cur_node = tree.nodes_left[cur_node] as usize;
            } else {
                cur_node = tree.nodes_right[cur_node] as usize;
            }
            if tree.nodes_left[cur_node] == -1 && tree.nodes_right[cur_node] == -1 {
                let ch = tree.nodes_ch[cur_node] as i64;
                decoded_sum = (decoded_sum * 33 + ch) & 0x7fffffff;
                cur_node = root;
            }
        }
        total_checksum = (total_checksum + decoded_sum) & 0x7fffffff;
    }
    println!("{}", total_checksum);
}
