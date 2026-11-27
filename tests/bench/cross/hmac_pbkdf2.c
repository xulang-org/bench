#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MASK32 4294967295ULL

static inline uint64_t rotr32(uint64_t x, int n) {
    return ((x >> n) | ((x << (32 - n)) & MASK32)) & MASK32;
}

static void sha256_block(uint64_t *state, const uint64_t *blk, int off, uint64_t *w, const uint64_t *kv) {
    for (int t = 0; t < 16; t++) {
        int j = off + t * 4;
        w[t] = (blk[j] << 24) | (blk[j + 1] << 16) | (blk[j + 2] << 8) | blk[j + 3];
    }
    for (int t = 16; t < 64; t++) {
        uint64_t w15 = w[t - 15], w2 = w[t - 2];
        uint64_t s0 = rotr32(w15, 7) ^ rotr32(w15, 18) ^ (w15 >> 3);
        uint64_t s1 = rotr32(w2, 17) ^ rotr32(w2, 19) ^ (w2 >> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) & MASK32;
    }
    uint64_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint64_t e = state[4], f = state[5], g = state[6], h = state[7];
    for (int t = 0; t < 64; t++) {
        uint64_t bs1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25);
        uint64_t ch = (e & f) ^ ((e ^ MASK32) & g);
        uint64_t temp1 = (h + bs1 + ch + kv[t] + w[t]) & MASK32;
        uint64_t bs0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22);
        uint64_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint64_t temp2 = (bs0 + maj) & MASK32;
        h = g; g = f; f = e; e = (d + temp1) & MASK32;
        d = c; c = b; b = a; a = (temp1 + temp2) & MASK32;
    }
    state[0] = (state[0] + a) & MASK32;
    state[1] = (state[1] + b) & MASK32;
    state[2] = (state[2] + c) & MASK32;
    state[3] = (state[3] + d) & MASK32;
    state[4] = (state[4] + e) & MASK32;
    state[5] = (state[5] + f) & MASK32;
    state[6] = (state[6] + g) & MASK32;
    state[7] = (state[7] + h) & MASK32;
}

static void sha256_compute(const uint64_t *msg, int mlen, uint64_t *state, uint64_t *pad,
                           uint64_t *w, const uint64_t *kv, const uint64_t *iv, uint64_t *out) {
    for (int i = 0; i < 8; i++) state[i] = iv[i];
    int pos = 0;
    while (pos + 64 <= mlen) {
        sha256_block(state, msg, pos, w, kv);
        pos += 64;
    }
    int rem = mlen - pos;
    for (int pi = 0; pi < rem; pi++) pad[pi] = msg[pos + pi];
    pad[rem] = 128;
    int total_len = rem >= 56 ? 128 : 64;
    for (int pi = rem + 1; pi < total_len - 8; pi++) pad[pi] = 0;
    uint64_t bitlen = (uint64_t)mlen * 8ULL;
    for (int bi = 0; bi < 8; bi++) pad[total_len - 8 + bi] = (bitlen >> ((7 - bi) * 8)) & 255ULL;
    sha256_block(state, pad, 0, w, kv);
    if (total_len == 128) sha256_block(state, pad, 64, w, kv);
    for (int i = 0; i < 8; i++) {
        uint64_t sv = state[i];
        out[i * 4] = (sv >> 24) & 255ULL;
        out[i * 4 + 1] = (sv >> 16) & 255ULL;
        out[i * 4 + 2] = (sv >> 8) & 255ULL;
        out[i * 4 + 3] = sv & 255ULL;
    }
}

static void hmac_sha256(const uint64_t *key, int klen, const uint64_t *msg, int mlen,
                        uint64_t *ipad, uint64_t *opad, uint64_t *inner_buf, uint64_t *outer_buf,
                        uint64_t *inner_hash, uint64_t *state, uint64_t *pad, uint64_t *w,
                        const uint64_t *kv, const uint64_t *iv, uint64_t *out) {
    for (int i = 0; i < 64; i++) {
        uint64_t kb = i < klen ? key[i] : 0ULL;
        ipad[i] = kb ^ 54ULL;
        opad[i] = kb ^ 92ULL;
        inner_buf[i] = ipad[i];
        outer_buf[i] = opad[i];
    }
    for (int i = 0; i < mlen; i++) inner_buf[64 + i] = msg[i];
    sha256_compute(inner_buf, 64 + mlen, state, pad, w, kv, iv, inner_hash);
    for (int i = 0; i < 32; i++) outer_buf[64 + i] = inner_hash[i];
    sha256_compute(outer_buf, 96, state, pad, w, kv, iv, out);
}

static void push_lit(uint64_t *buf, int *len, const char *s) {
    while (*s) buf[(*len)++] = (uint64_t)(unsigned char)(*s++);
}

static void push_nd(uint64_t *buf, int *len, int64_t v, int digits) {
    uint64_t tmp[8];
    int64_t x = v;
    for (int i = digits - 1; i >= 0; i--) {
        tmp[i] = 48ULL + (uint64_t)(x % 10);
        x /= 10;
    }
    for (int i = 0; i < digits; i++) buf[(*len)++] = tmp[i];
}

int main(void) {
    const uint64_t iv[8] = {
        1779033703ULL, 3144134277ULL, 1013904242ULL, 2773480762ULL,
        1359893119ULL, 2600822924ULL, 528734635ULL, 1541459225ULL,
    };
    const uint64_t kv[64] = {
        1116352408ULL, 1899447441ULL, 3049323471ULL, 3921009573ULL, 961987163ULL, 1508970993ULL, 2453635748ULL, 2870763221ULL,
        3624381080ULL, 310598401ULL, 607225278ULL, 1426881987ULL, 1925078388ULL, 2162078206ULL, 2614888103ULL, 3248222580ULL,
        3835390401ULL, 4022224774ULL, 264347078ULL, 604807628ULL, 770255983ULL, 1249150122ULL, 1555081692ULL, 1996064986ULL,
        2554220882ULL, 2821834349ULL, 2952996808ULL, 3210313671ULL, 3336571891ULL, 3584528711ULL, 113926993ULL, 338241895ULL,
        666307205ULL, 773529912ULL, 1294757372ULL, 1396182291ULL, 1695183700ULL, 1986661051ULL, 2177026350ULL, 2456956037ULL,
        2730485921ULL, 2820302411ULL, 3259730800ULL, 3345764771ULL, 3516065817ULL, 3600352804ULL, 4094571909ULL, 275423344ULL,
        430227734ULL, 506948616ULL, 659060556ULL, 883997877ULL, 958139571ULL, 1322822218ULL, 1537002063ULL, 1747873779ULL,
        1955562222ULL, 2024104815ULL, 2227730452ULL, 2361852424ULL, 2428436474ULL, 2756734187ULL, 3204031479ULL, 3329325298ULL,
    };

    uint64_t state[8], w[64], pad[128], ipad[64], opad[64];
    uint64_t inner_buf[256], outer_buf[256], inner_hash[32], dk[32], u_buf[32], acc[32];
    memset(acc, 0, sizeof(acc));
    uint64_t pw[64], salt[64], key[64], msg[128];
    int64_t ops = 0;

    for (int64_t i = 0; i < 80; i++) {
        int pw_len = 0, salt_len = 0;
        push_lit(pw, &pw_len, "xu-pass-");
        push_nd(pw, &pw_len, i, 3);
        push_lit(pw, &pw_len, "-secret");

        push_lit(salt, &salt_len, "salt-");
        push_nd(salt, &salt_len, i * 7, 4);
        push_lit(salt, &salt_len, "-v1");
        salt[salt_len++] = 0; salt[salt_len++] = 0; salt[salt_len++] = 0; salt[salt_len++] = 1;

        hmac_sha256(pw, pw_len, salt, salt_len, ipad, opad, inner_buf, outer_buf, inner_hash, state, pad, w, kv, iv, u_buf);
        for (int bi = 0; bi < 32; bi++) dk[bi] = u_buf[bi];
        for (int it = 1; it < 1000; it++) {
            hmac_sha256(pw, pw_len, u_buf, 32, ipad, opad, inner_buf, outer_buf, inner_hash, state, pad, w, kv, iv, u_buf);
            for (int bi = 0; bi < 32; bi++) dk[bi] ^= u_buf[bi];
        }
        for (int bi = 0; bi < 32; bi++) acc[bi] ^= dk[bi];
        ops++;
    }

    for (int64_t i = 0; i < 200; i++) {
        int klen = 0, mlen = 0;
        push_lit(key, &klen, "jwt-hmac-key-");
        push_nd(key, &klen, i % 16, 2);

        push_lit(msg, &mlen, "eyJhbGciOiJIUzI1NiJ9.sub=user_");
        push_nd(msg, &mlen, i, 4);
        push_lit(msg, &mlen, "&seq=");
        push_nd(msg, &mlen, i * 37, 5);

        hmac_sha256(key, klen, msg, mlen, ipad, opad, inner_buf, outer_buf, inner_hash, state, pad, w, kv, iv, u_buf);
        for (int bi = 0; bi < 32; bi++) acc[bi] ^= u_buf[bi];
        ops++;
    }

    printf("%" PRId64 "\n", ops);
    for (int i = 0; i < 32; i++) printf("%02x", (unsigned)acc[i]);
    putchar('\n');
    return 0;
}
