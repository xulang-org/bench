#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>

typedef struct {
    int freq;
    int nid;
} HeapItem;

typedef struct {
    HeapItem items[256];
    int size;
} MinHeap;

static inline int heap_less(HeapItem a, HeapItem b) {
    if (a.freq != b.freq) return a.freq < b.freq;
    return a.nid < b.nid;
}

static void heap_push(MinHeap *h, int freq, int nid) {
    int i = h->size++;
    HeapItem item = {freq, nid};
    while (i > 0) {
        int p = (i - 1) / 2;
        if (heap_less(item, h->items[p])) {
            h->items[i] = h->items[p];
            i = p;
        } else break;
    }
    h->items[i] = item;
}

static HeapItem heap_pop(MinHeap *h) {
    HeapItem top = h->items[0];
    HeapItem last = h->items[--h->size];
    if (h->size == 0) return top;
    int i = 0;
    while (i * 2 + 1 < h->size) {
        int left = i * 2 + 1;
        int right = left + 1;
        int best = left;
        if (right < h->size && heap_less(h->items[right], h->items[left])) {
            best = right;
        }
        if (heap_less(h->items[best], last)) {
            h->items[i] = h->items[best];
            i = best;
        } else break;
    }
    h->items[i] = last;
    return top;
}

int nodes_freq[256];
int nodes_ch[256];
int nodes_left[256];
int nodes_right[256];
int node_count = 0;

int codes[64];
int code_lens[64];

static void get_codes(int nid, int curr_code, int curr_len) {
    if (nodes_left[nid] == -1 && nodes_right[nid] == -1) {
        int ch = nodes_ch[nid];
        codes[ch] = curr_code;
        code_lens[ch] = curr_len;
        return;
    }
    get_codes(nodes_left[nid], (curr_code << 1) | 0, curr_len + 1);
    get_codes(nodes_right[nid], (curr_code << 1) | 1, curr_len + 1);
}

int main(void) {
    int raw[20000];
    int64_t seed = 123456789;
    int freqs[64] = {0};
    for (int i = 0; i < 20000; i++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        int c = (int)sqrt(seed % 4096);
        raw[i] = c;
        freqs[c]++;
    }

    MinHeap heap = {.size = 0};
    for (int ch = 0; ch < 64; ch++) {
        if (freqs[ch] > 0) {
            int nid = node_count++;
            nodes_freq[nid] = freqs[ch];
            nodes_ch[nid] = ch;
            nodes_left[nid] = -1;
            nodes_right[nid] = -1;
            heap_push(&heap, freqs[ch], nid);
        }
    }

    while (heap.size > 1) {
        HeapItem item1 = heap_pop(&heap);
        HeapItem item2 = heap_pop(&heap);
        int pid = node_count++;
        nodes_freq[pid] = item1.freq + item2.freq;
        nodes_ch[pid] = -1;
        nodes_left[pid] = item1.nid;
        nodes_right[pid] = item2.nid;
        heap_push(&heap, nodes_freq[pid], pid);
    }
    int root = heap_pop(&heap).nid;
    get_codes(root, 0, 0);

    // encode
    uint32_t bit_buf[10000];
    int bit_buf_len = 0;
    int bit_count = 0;
    uint32_t curr_word = 0;
    int curr_bits = 0;

    for (int i = 0; i < 20000; i++) {
        int b = raw[i];
        int c = codes[b];
        int l = code_lens[b];
        for (int bit_idx = l - 1; bit_idx >= 0; bit_idx--) {
            int bit = (c >> bit_idx) & 1;
            curr_word = (curr_word << 1) | bit;
            curr_bits++;
            if (curr_bits == 32) {
                bit_buf[bit_buf_len++] = curr_word;
                curr_word = 0;
                curr_bits = 0;
            }
            bit_count++;
        }
    }
    if (curr_bits > 0) {
        curr_word = curr_word << (32 - curr_bits);
        bit_buf[bit_buf_len++] = curr_word;
    }

    int64_t total_checksum = 0;
    for (int round = 0; round < 50; round++) {
        int cur_node = root;
        int64_t decoded_sum = 0;
        for (int i = 0; i < bit_count; i++) {
            int word_idx = i / 32;
            int bit_pos = 31 - (i % 32);
            int bit = (bit_buf[word_idx] >> bit_pos) & 1;
            if (bit == 0) {
                cur_node = nodes_left[cur_node];
            } else {
                cur_node = nodes_right[cur_node];
            }
            if (nodes_left[cur_node] == -1 && nodes_right[cur_node] == -1) {
                int ch = nodes_ch[cur_node];
                decoded_sum = (decoded_sum * 33 + ch) & 0x7fffffff;
                cur_node = root;
            }
        }
        total_checksum = (total_checksum + decoded_sum) & 0x7fffffff;
    }

    printf("%lld\n", total_checksum);
    return 0;
}
