# Systems, Tooling & Compression Suite (Batch F)

Self-contained deterministic benchmarks covering compiler front-ends & bytecode VMs, Myers sequence diffing, kernel-style slab memory management, hierarchical timing wheels, block lossless compression, and strict multilingual UTF-8 validation/normalization. All 6 workloads provide five-language ports (`Xu`, `Go`, `C`, `Rust`, `Swift`) with LF-normalized deterministic stdout goldens.

| Benchmark | Domain / Algorithm | Scale | Golden |
|---|---|---|---|
| `expr_bytecode_vm` | Expression lexer, recursive-descent compiler & 30-bit stack bytecode VM | 16 exprs × 160 compiles × 100 evals | `5488000\n628681581\n` |
| `myers_diff` | Myers `O(ND)` shortest-edit-script search & trace backtrack | 1,200 mutated pairs (len ~200) | `35144\n450000758\n` |
| `slab_allocator` | 6-class segregated slab allocator, intrusive free lists & full-page reclaim | 600,000 mixed ops (256 × 256-word pages) | `300032\n352385751\n` |
| `timing_wheel` | 2-level hierarchical hashed timing wheel (`256 + 256`), cascade & O(1) cancel | 160,000 ticks (~480k firings) | `479931\n463812537\n` |
| `lz4_block_codec` | LZ4 block hash-match compression & overlapping-copy decompression | 24 × 32 KiB blocks × 4 rounds | `609348\n141693848\n` |
| `utf8_text_norm` | Strict UTF-8 decoder (`U+FFFD` fault handling), case/width fold & whitespace collapse | 40 passes × 65,523 bytes | `2339280\n538177438\n` |
