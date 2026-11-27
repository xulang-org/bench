# Storage, Databases & Search Suite (Batch E)

Self-contained deterministic benchmarks covering storage engines, full-text information retrieval, analytical SQL query execution, distributed cluster routing, and durable binary write-ahead log recovery. All 6 workloads provide five-language ports (`Xu`, `Go`, `C`, `Rust`, `Swift`) with LF-normalized deterministic stdout goldens.

| Benchmark | Domain / Algorithm | Scale | Golden |
|---|---|---|---|
| `btree_index` | Order-32 B+ tree in flat node pools (`next_leaf` chain), bottom-up node splits, point lookups & leaf-linked range scans | 80k inserts + 120k lookups + 2k scans | `156642\n923128089\n` |
| `lsm_compaction` | LSM-Tree buffered L0 flush (in-place heapsort & dedup), K-way min-heap merge compaction with tombstones, SSTable binary search | 4 cycles × (8 × 12k L0 + 60k queries) | `210492\n473464819\n` |
| `bm25_search` | CSR inverted index construction, fixed-point integer `log2` IDF, sparse query accumulator & Top-10 ranking | 6,000 docs × 2,000 queries | `20000\n285545384\n` |
| `sql_query_exec` | Columnar fact table scan, multi-predicate filter, open-addressed Hash Join, `GROUP BY (region, cat)` & `ORDER BY rev DESC` | 16 rounds × 200k orders ⋈ 8,192 customers | `1053790\n365717875\n` |
| `consistent_hash` | Virtual-node consistent hash ring (`mix32`, 128 vnodes/node), binary-search routing & live topology rebalance migration | 600k lookups + 4 cluster rebalances (150k keys) | `61873\n601893444\n` |
| `wal_log_recovery` | Little-endian binary WAL record framing, IEEE 802.3 CRC-32 checksums, torn-tail truncation/corruption & open-addressed KV replay | 40 segments × 3,000 records | `119984\n241048890\n` |
