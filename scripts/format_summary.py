#!/usr/bin/env python3
"""Format cross-language benchmark results into GitHub Step Summary Markdown and clean JSON for the official website."""
from __future__ import annotations

import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path

BENCH_DESCRIPTIONS = {
    "startup": ("进程启动/空 main", "Process startup / empty main", "control"),
    "loop_sum": ("整数累加循环", "Integer loop accumulation", "control"),
    "fib": ("递归调用 (fib 35)", "Recursive call (fib 35)", "control"),
    "nested_loop": ("深度嵌套循环", "Deeply nested loops", "control"),
    "method_sum": ("结构体方法调用", "Struct method dispatch", "control"),
    "f64_sum": ("双精度浮点算术", "Float64 arithmetic", "control"),
    "matmul": ("矩阵乘法 (i64 matmul)", "Matrix multiplication", "algo"),
    "string_build": ("字符串扩容与构建", "String growth & scan", "string"),
    "string_repeat": ("字符串倍增复制", "String repeat & copy", "string"),
    "array_ops": ("动态数组扩容/索引", "Dynamic array growth", "data"),
    "file_roundtrip": ("文件写入与读取 (32×512KiB)", "File roundtrip IO", "string"),
    "sort_lcg": ("标准库快速排序", "Stdlib sort (LCG data)", "algo"),
    "algorithm_search": ("标准库二分查找", "Stdlib binary search", "algo"),
    "math_bits": ("位运算与硬件指令", "Bitwise ops (hardware popcount/clz)", "algo"),
    "sha256_chain": ("SHA-256 哈希链", "SHA-256 hash chain", "crypto"),
    "chan_ping": ("Channel 协程流水线", "Channel / Coroutine pipeline", "concurrency"),
    "http_concurrent": ("本地并发 HTTP 请求", "Local concurrent HTTP requests", "concurrency"),
    "map_ops": ("哈希表高频读写", "Hash map insert / lookup", "data"),
    "iface_sum": ("接口动态派发", "Interface dynamic dispatch", "control"),
    "match_sum": ("密集模式匹配", "Dense pattern match / switch", "control"),
    "fn_val_sum": ("函数值一等公民调用", "First-class function call", "control"),
    "copy_bytes": ("块内存拷贝", "Block memory copy (load/store)", "data"),
    "sroa_vec3": ("三维向量字段归约 (SROA)", "3D vector SROA reduction", "algo"),
    "scan_dep": ("进位依赖链 prefix-add", "Carry dependency chain", "algo"),
    "chase_index": ("数据依赖下标指针追逐", "Data-dependent index chasing", "data"),
    "sieve_primes": ("埃氏素数筛法", "Sieve of Eratosthenes", "algo"),
    "crc32_iso": ("CRC32 校验和吞吐", "CRC32 stream checksum", "crypto"),
    "builder": ("字符串构建器动态扩容", "String builder dynamic capacity", "string"),
    "byte_view": ("切片视图子串搜索", "String slice view & search", "string"),
    "strings_io": ("字符串综合切分拼接", "Strings IO (repeat/split/join)", "string"),
    "string_count": ("短串字节匹配计数", "Short string byte counting", "string"),
    "heap_priority": ("二叉堆优先队列", "Binary heap priority queue", "data"),
    "hex_codec": ("十六进制编解码流", "Hexadecimal codec stream", "string"),
    "base64_codec": ("Base64 编解码流", "Base64 codec stream", "string"),
    "ring_buffer": ("双端环形缓冲区", "Ring buffer queue", "data"),
    "md5_chain": ("MD5 散列计算链", "MD5 digest chain", "crypto"),
    "quicksort_hoare": ("Hoare 双指针快排", "Hoare quicksort", "algo"),
    "lru_cache": ("LRU 双向链表淘汰缓存", "LRU cache (hash + dll)", "data"),
    "bloom_filter": ("布隆过滤器位图查验", "Bloom filter bitmap", "data"),
    "aes128_encrypt": ("AES-128 软件加密", "AES-128 software encrypt", "crypto"),
    "aes128_decrypt": ("AES-128 软件解密", "AES-128 software decrypt", "crypto"),
    "aes128_key_setup": ("AES-128 密钥扩展", "AES-128 key expansion", "crypto"),
    "aes192_encrypt": ("AES-192 软件加密", "AES-192 software encrypt", "crypto"),
    "aes192_decrypt": ("AES-192 软件解密", "AES-192 software decrypt", "crypto"),
    "aes192_key_setup": ("AES-192 密钥扩展", "AES-192 key expansion", "crypto"),
    "aes256_encrypt": ("AES-256 软件加密", "AES-256 software encrypt", "crypto"),
    "aes256_decrypt": ("AES-256 软件解密", "AES-256 software decrypt", "crypto"),
    "aes256_key_setup": ("AES-256 密钥扩展", "AES-256 key expansion", "crypto"),
    "avl_tree": ("AVL 平衡二叉树插查", "AVL balanced tree insert / lookup", "data"),
    "chacha20_stream": ("ChaCha20 流密码块生成", "ChaCha20 stream cipher blocks", "crypto"),
    "huffman_coding": ("Huffman 编码与位流解码", "Huffman coding & bitstream decode", "algo"),
    "json_tokenizer": ("JSON 词法扫描器", "JSON lexical tokenizer", "string"),
    "lzw_codec": ("LZW 压缩与解压编解码", "LZW compression / decompression", "string"),
    "plb2_nqueen": ("PLB2 15 皇后位运算回溯", "PLB2 15-Queens bitboard backtracking", "algo"),
    "plb2_sudoku": ("PLB2 kudoku 数独求解", "PLB2 kudoku exact-cover solver", "algo"),
    "plb2_bedcov": ("PLB2 隐式区间树重叠查询", "PLB2 implicit interval tree overlap", "data"),
    "thread_ring": ("并发令牌环调度 (503 节点)", "Thread-ring token passing (503 nodes)", "concurrency"),
    "skynet": ("Skynet 10 叉树协程扇出", "Skynet 10-ary task fan-out", "concurrency"),
    "scimark_montecarlo": ("SciMark2 蒙特卡洛积分", "SciMark2 Monte Carlo integration", "algo"),
    "scimark_sor": ("SciMark2 二维 SOR 超松弛", "SciMark2 2D SOR relaxation", "algo"),
    "scimark_lu": ("SciMark2 稠密矩阵 LU 分解", "SciMark2 dense LU factorization", "algo"),
    "scimark_sparse": ("SciMark2 CSR 稀疏矩阵乘", "SciMark2 CSR sparse matvec", "algo"),
    "scimark_fft": ("SciMark2 Radix-2 复数 FFT", "SciMark2 Radix-2 complex FFT", "algo"),
    "awfy_richards": ("AWFY OS 任务调度模拟 (Richards)", "AWFY OS task scheduler simulation", "control"),
    "awfy_json_parser": ("AWFY 递归下降 JSON 解析", "AWFY recursive-descent JSON parser", "string"),
    "brainfuck_vm": ("Brainfuck 字节码虚拟机", "Brainfuck bytecode VM interpreter", "control"),
    "regex_nfa": ("Thompson NFA 正则匹配引擎", "Thompson NFA regex engine", "string"),
    "treap_ops": ("无旋转分裂合并 Treap 树堆", "Split/merge randomized Treap", "data"),
    "astar_maze": ("81×81 迷宫最短路 A* 搜索", "81x81 maze A* shortest path", "algo"),
    "levenshtein_dp": ("Levenshtein 编辑距离滚动 DP", "Levenshtein rolling-row edit distance", "string"),
    "csv_aggregate": ("十万行 CSV 流解析与哈希聚合", "100k-row CSV fixed-point aggregation", "string"),
    "http_router_parse": ("HTTP/1.1 解析与 Trie 动态路由", "HTTP/1.1 parsing & trie router", "web"),
    "websocket_frame": ("WebSocket 帧编解码与掩码", "RFC 6455 WebSocket frame codec", "web"),
    "protobuf_varint": ("Protobuf Varint/ZigZag 编解码", "Protobuf Varint/ZigZag nested RPC codec", "web"),
    "toml_config_parse": ("TOML 多节配置文件解析", "Multi-section TOML config parser", "web"),
    "template_render": ("HTML 模板编译与转义渲染", "HTML template compiler & XSS escaping", "web"),
    "hmac_pbkdf2": ("HMAC-SHA256 与 PBKDF2 派生", "HMAC-SHA256 & PBKDF2 key derivation", "crypto"),
    "btree_index": ("Order-32 B+ 树插查与范围扫描", "Order-32 B+ tree insert, lookup & range scan", "storage"),
    "lsm_compaction": ("LSM-Tree 多路归并压缩", "LSM-Tree flush, K-way merge & SSTable lookup", "storage"),
    "bm25_search": ("倒排索引与 BM25 Top-10 检索", "Inverted index & integer BM25 Top-10 search", "storage"),
    "sql_query_exec": ("列式 SQL Hash Join 与分组聚合", "Columnar SQL hash-join, GROUP BY & ORDER BY", "storage"),
    "consistent_hash": ("虚拟节点一致性哈希与扩缩容", "Virtual-node consistent hashing & rebalance", "storage"),
    "wal_log_recovery": ("二进制 WAL 日志 CRC-32 与崩溃恢复", "Binary WAL framing, CRC-32 & crash recovery", "storage"),
    "expr_bytecode_vm": ("表达式编译与栈字节码 VM", "Expression compiler & stack bytecode VM", "systems"),
    "myers_diff": ("Myers O(ND) 文本差异与回溯", "Myers O(ND) diff & edit script backtrack", "systems"),
    "slab_allocator": ("分级 Slab 内存分配与页回收", "Segregated slab allocator & page reclaim", "systems"),
    "timing_wheel": ("双层层级时间轮定时器调度", "Hierarchical timing wheel timer scheduler", "systems"),
    "lz4_block_codec": ("LZ4 块压缩与重叠解压编解码", "LZ4 block hash-match compression codec", "systems"),
    "utf8_text_norm": ("UTF-8 校验解码与文本规范化", "UTF-8 validation, case-fold & normalization", "systems"),
    "raytrace_sphere": ("3D 球体光线追踪与反射", "3D ray-sphere tracer with shadows & reflections", "graphics"),
    "image_sobel_blur": ("高斯模糊与 Sobel 边缘检测", "2D Gaussian blur & Sobel edge pipeline", "graphics"),
    "physics_collision": ("2D 空间哈希碰撞物理仿真", "2D spatial-hash rigid-circle collision sim", "graphics"),
    "mlp_inference": ("三层稠密 MLP 神经网络推理", "3-layer dense MLP forward inference (ReLU)", "ai"),
    "kmeans_cluster": ("多维 K-Means 聚类迭代", "8D Lloyd K-Means clustering", "ai"),
    "order_book_match": ("限价订单簿高频撮合引擎", "Limit order book price-time matching engine", "ai"),
    "x25519_dh": ("Curve25519 / X25519 密钥交换", "RFC 7748 Curve25519 / X25519 DH ladder", "crypto"),
    "parallel_mapreduce": ("多 Worker 并发 MapReduce", "8-worker parallel MapReduce channel pipeline", "concurrency"),
}

CATEGORY_NAMES = {
    "control": ("控制流与语言机制", "Control flow & primitives"),
    "algo": ("算法与数值计算", "Algorithms & numerical"),
    "data": ("数据结构与内存访问", "Data structures & memory"),
    "string": ("字符串与文本 I/O", "Strings & text I/O"),
    "web": ("Web 后端与网络协议", "Web, protocols & serialization"),
    "storage": ("数据库与存储检索", "Storage, databases & search"),
    "systems": ("系统编程与工具链", "Systems, tooling & compression"),
    "graphics": ("图形图像与物理仿真", "Graphics, imaging & physics"),
    "ai": ("AI 推理与金融计算", "AI inference, ML & quant"),
    "crypto": ("密码学与安全", "Cryptography & security"),
    "concurrency": ("并发与多核并行", "Concurrency & parallelism"),
}

# Single source of truth for the 6 CI platforms and wall-clock-optimal shard split:
# 20 total concurrent bench jobs (GitHub Actions cap) with 5 macOS jobs (2+3, macOS cap).
PLATFORM_SPECS: tuple[dict, ...] = (
    {
        "name": "Linux ARM64",
        "os": "ubuntu-24.04-arm",
        "platform_id": "linux-arm64",
        "target": "linux-arm64",
        "os_name": "Linux",
        "arch_name": "arm64",
        "auto_shards": 3,
    },
    {
        "name": "Linux x86_64",
        "os": "ubuntu-latest",
        "platform_id": "linux-x64",
        "target": "linux-x64",
        "os_name": "Linux",
        "arch_name": "x86_64",
        "auto_shards": 4,
    },
    {
        "name": "macOS ARM64 (Apple Silicon)",
        "os": "macos-latest",
        "platform_id": "macos-arm64",
        "target": "macos-arm64",
        "os_name": "macOS",
        "arch_name": "arm64",
        "auto_shards": 2,
    },
    {
        "name": "macOS x86_64 (Intel)",
        "os": "macos-15-intel",
        "platform_id": "macos-x64",
        "target": "macos-x64",
        "os_name": "macOS",
        "arch_name": "x86_64",
        "auto_shards": 3,
    },
    {
        "name": "Windows x86_64",
        "os": "windows-latest",
        "platform_id": "windows-x64",
        "target": "windows-x64",
        "os_name": "Windows",
        "arch_name": "x86_64",
        "auto_shards": 4,
    },
    {
        "name": "Windows ARM64",
        "os": "windows-11-arm",
        "platform_id": "windows-arm64",
        "target": "windows-arm64",
        "os_name": "Windows",
        "arch_name": "arm64",
        "auto_shards": 4,
    },
)
PLATFORM_BY_ID: dict[str, dict] = {spec["platform_id"]: spec for spec in PLATFORM_SPECS}


def plan_ci_matrix(
    *,
    mode: str = "full",
    benches: str = "",
    shards: str = "auto",
    macos_arm64_image: str = "macos-latest",
) -> dict:
    """Plan the dynamic build and sharded benchmark matrices for GitHub Actions."""
    norm_mode = (mode or "full").strip()
    norm_benches = (benches or "").strip()
    norm_shards = (shards or "auto").strip()
    norm_macos_img = (macos_arm64_image or "macos-latest").strip()
    if norm_mode not in ("full", "quick"):
        raise ValueError(f"unsupported mode {norm_mode!r}; expected 'full' or 'quick'")
    if norm_shards not in ("auto", "1"):
        raise ValueError(f"unsupported shards strategy {norm_shards!r}; expected 'auto' or '1'")

    use_auto = norm_shards == "auto" and norm_mode == "full" and not norm_benches
    expect_full_registry = norm_mode == "full" and not norm_benches

    build_include = []
    bench_include = []
    platform_shards: dict[str, int] = {}

    for spec in PLATFORM_SPECS:
        entry_base = {k: v for k, v in spec.items() if k != "auto_shards"}
        if spec["platform_id"] == "macos-arm64":
            entry_base["os"] = norm_macos_img
        build_include.append(entry_base)

        shard_total = spec["auto_shards"] if use_auto else 1
        platform_shards[spec["platform_id"]] = shard_total
        for shard_idx in range(1, shard_total + 1):
            job_name = (
                f"{spec['name']} ({shard_idx}/{shard_total})"
                if shard_total > 1
                else spec["name"]
            )
            bench_include.append({
                **entry_base,
                "shard": shard_idx,
                "shard_total": shard_total,
                "job_name": job_name,
            })

    return {
        "build_matrix": {"include": build_include},
        "bench_matrix": {"include": bench_include},
        "platform_shards": platform_shards,
        "expect_full_registry": expect_full_registry,
    }


def parse_crosslang_txt(content: str) -> dict:
    records = re.findall(r'^# result: (.+)$', content, re.M)
    if records:
        results = {}
        for raw in records:
            record = json.loads(raw)
            name, impl = record.pop('bench'), record.pop('impl')
            if impl in results.setdefault(name, {}):
                raise ValueError(f'duplicate runtime result: {name}/{impl}')
            if record['status'] != 'ok':
                if record['status'] not in {'compile_failed', 'run_failed', 'stdout_mismatch', 'measurement_failed'}:
                    raise ValueError(f'unknown result status: {name}/{impl}')
                record = {key: record[key] for key in ('status', 'error')}
            results[name][impl] = record
        # Registry order is independent of the implementation scheduling order.
        selected = re.search(r'^# benches: (.+)$', content, re.M)
        names = selected[1].split(', ') if selected else list(results)
        if set(names) != set(results):
            raise ValueError('runtime results do not cover the requested workloads')
        return {name: results[name] for name in names}
    pat = re.compile(
        r"^(.+?)\s+([a-z0-9_]+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s+OK(?:\s|$)",
        re.M,
    )
    results = {}
    for raw_impl, bench, best, med, rss, cpu, size in pat.findall(content):
        impl = raw_impl.strip()
        results.setdefault(bench, {})[impl] = {
            "wall_ms": float(med),
            "best_ms": float(best),
            "rss_mib": float(rss),
            "cpu_ms": float(cpu),
            "bytes": int(size),
        }
    return results


def parse_toolchains(content: str) -> dict:
    """Keep versions from the same raw measurement log, never the import host."""
    versions = {}
    for name in ("clang", "rustc", "go", "swiftc"):
        match = re.search(r"^# " + name + r": (.+)$", content, re.M)
        versions[name] = match.group(1).strip() if match else None
    return versions


def build_benchmark_payload(results: dict, meta: dict | None = None) -> dict:
    meta = meta or {}
    benches = []
    for name, implementations in results.items():
        xu = implementations.get("Xu")
        if xu is None:
            raise ValueError(f'missing Xu outcome: {name}')
        def select_best_opt(prefix):
            choices = [implementations[name] for name in (f"{prefix} -O{i}" for i in (1, 2, 3))
                       if name in implementations and isinstance(implementations[name].get("wall_ms"), (int, float))
                       and implementations[name]["wall_ms"] > 0]
            return min(choices, key=lambda impl: impl["wall_ms"]) if choices else None

        c_opt = select_best_opt("clang")
        rust_opt = select_best_opt("rustc")
        go_opt = implementations.get("go build")
        swift_opt = implementations.get("swiftc -O")

        desc_zh, desc_en, category = BENCH_DESCRIPTIONS.get(name, (name, name, "algo"))

        def calc_ratio(peer):
            if not peer or not isinstance(peer.get("wall_ms"), (int, float)) or peer["wall_ms"] <= 0:
                return None
            if not xu or not isinstance(xu.get("wall_ms"), (int, float)) or xu["wall_ms"] <= 0:
                return None
            return round(xu["wall_ms"] / peer["wall_ms"], 2)

        benches.append({
            "name": name,
            "desc_zh": desc_zh,
            "desc_en": desc_en,
            "category": category,
            "xu_status": xu.get("status", "ok"),
            "xu_error": xu.get("error"),
            "xu_wall_ms": xu.get("wall_ms"),
            "xu_best_ms": xu.get("best_ms"),
            "xu_rss_mib": xu.get("rss_mib"),
            "xu_bytes": xu.get("bytes"),
            "c_wall_ms": c_opt["wall_ms"] if c_opt else None,
            "rust_wall_ms": rust_opt["wall_ms"] if rust_opt else None,
            "go_wall_ms": go_opt.get("wall_ms") if go_opt else None,
            "swift_wall_ms": swift_opt.get("wall_ms") if swift_opt else None,
            "ratio_vs_c": calc_ratio(c_opt),
            "ratio_vs_rust": calc_ratio(rust_opt),
            "ratio_vs_go": calc_ratio(go_opt),
            "ratio_vs_swift": calc_ratio(swift_opt),
            "implementations": implementations,
        })

    return {
        "metadata": {
            "date": meta.get("date", date.today().isoformat()),
            "os": meta.get("os", "Linux / macOS"),
            "arch": meta.get("arch", "arm64 / x64"),
            "platform_id": meta.get("platform_id", "default"),
            "platform_name": meta.get("platform_name", f"{meta.get('os')} ({meta.get('arch')})"),
            "xu_version": meta.get("xu_version", "0.8.8"),
            "total_benches": len(benches),
            "xu_failed_benches": sum(b['xu_status'] != 'ok' for b in benches),
            "rss_method": meta.get("rss_method", "unrecorded"),
            "toolchains": meta.get("toolchains", {}),
            "methodology": "Whole-program wall time, 7 iterations median; Linux RSS from separate post-exec tracing, macOS wait4, Windows peak working set; verified stdout",
        },
        "categories": {k: {"zh": v[0], "en": v[1]} for k, v in CATEGORY_NAMES.items()},
        "benches": benches,
    }


def generate_markdown_summary(payload: dict) -> str:
    meta = payload["metadata"]
    benches = payload["benches"]
    platform_label = meta.get("platform_name") or f"{meta.get('os')} ({meta.get('arch')})"
    lines = [
        f"## 🚀 Xu 全量跨语言基准横向测评 ({meta['date']})",
        "",
        f"- **运行平台 / 架构**: `{platform_label}`",
        f"- **编译器版本**: `Xu v{meta['xu_version']}`",
        f"- **测试负载数量**: `{meta['total_benches']}` 项算法与业务场景",
        f"- **对比语言**: `C (Clang best O1–O3)`, `Rust (rustc best O1–O3)`, `Go (go build)`, `Swift (-O)`",
        f"- **评测准则**: `{meta['methodology']}`",
        "",
        "### 🌟 核心特性与资源开销总览",
        "",
        "| 特性 / 负载 | Xu | Go | C 最佳 (O1–O3) | Rust 最佳 (O1–O3) | 表现分析 |",
        "|---|---:|---:|---:|---:|---|",
    ]

    versions = meta.get("toolchains", {})
    lines[8:8] = [f"- **{name}**: `{versions.get(name) or 'not available in this run'}`"
                  for name in ("clang", "rustc", "go", "swiftc")]
    key_benches = [
        "startup", "chan_ping", "loop_sum", "matmul", "sroa_vec3", "aes128_encrypt",
        "plb2_nqueen", "scimark_fft", "awfy_richards", "treap_ops",
    ]
    for kb in key_benches:
        item = next((b for b in benches if b["name"] == kb), None)
        if not item:
            continue
        c_str = f"{item['c_wall_ms']:.1f}ms" if item['c_wall_ms'] else "—"
        rust_str = f"{item['rust_wall_ms']:.1f}ms" if item['rust_wall_ms'] else "—"
        go_str = f"{item['go_wall_ms']:.1f}ms" if item['go_wall_ms'] else "—"
        note = ""
        if item['xu_wall_ms'] is None:
            note = item['xu_status']
        elif kb == "startup":
            note = f"极速冷启动，领先 Go {round((item['go_wall_ms']/item['xu_wall_ms']-1)*100)}%" if item['go_wall_ms'] else "极速原生冷启动"
        elif kb == "chan_ping":
            note = "原生轻量协程与 Channel 高性能调度"
        elif kb == "sroa_vec3":
            note = "SROA 字段标量展开消除冗余访问"
        elif kb == "aes128_encrypt":
            note = "纯软件算法实现，表现稳健"
        elif kb == "plb2_nqueen":
            note = "PLB2 位运算回溯搜索"
        elif kb == "scimark_fft":
            note = "SciMark2 浮点复数 FFT 核"
        elif kb == "awfy_richards":
            note = "AWFY 经典 OS 任务调度模拟"
        elif kb == "treap_ops":
            note = "节点池分裂合并动态树结构"
        xu_str = f"{item['xu_wall_ms']:.2f}ms" if item['xu_wall_ms'] is not None else item['xu_status']
        lines.append(f"| **{item['desc_zh']}** (`{kb}`) | **{xu_str}** | {go_str} | {c_str} | {rust_str} | {note} |")

    lines.extend([
        "",
        "### 📊 全量横向性能对比表 (Wall Time 中位数，ms)",
        "",
        "| 负载类别 | 负载名称 | Xu (ms) | Go (ms) | C 最佳 (ms) | Rust 最佳 (ms) | Xu / 最佳对照 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])

    for b in benches:
        cat_zh = CATEGORY_NAMES.get(b["category"], (b["category"], ""))[0]
        c_val = f"{b['c_wall_ms']:.2f}" if b['c_wall_ms'] is not None else "—"
        rust_val = f"{b['rust_wall_ms']:.2f}" if b['rust_wall_ms'] is not None else "—"
        go_val = f"{b['go_wall_ms']:.2f}" if b['go_wall_ms'] is not None else "—"
        ratio_c = f"{b['ratio_vs_c']}×" if b['ratio_vs_c'] is not None else "—"
        xu_val = f"{b['xu_wall_ms']:.2f}" if b['xu_wall_ms'] is not None else b['xu_status']
        lines.append(
            f"| {cat_zh} | `{b['name']}`<br><small>{b['desc_zh']}</small> | **{xu_val}** | {go_val} | {c_val} | {rust_val} | {ratio_c} |"
        )

    lines.append("")
    lines.append("> 💡 完整结构化数据与图表已同步至官网 [xulang.org/benchmarks](https://xulang.org/benchmarks)。")
    return "\n".join(lines)


def generate_multi_arch_summary(aggregated: dict) -> str:
    meta = aggregated["metadata"]
    platforms = aggregated["platforms"]
    lines = [
        f"## 🌐 Xu 多架构 & 跨平台基准测评全矩阵汇总报告",
        "",
        f"- **基准评测日期**: `{meta['date']}`",
        f"- **编译器版本**: `Xu v{meta['xu_version']}`",
        f"- **测试覆盖矩阵**: `{len(platforms)}` 组平台架构环境（ARM64 与 x86_64 双架构支持）",
        "",
        "### 🖥️ 平台与架构执行状态",
        "",
        "| 平台代号 | 操作系统 | 硬件架构 | 评测负载数 | 状态 |",
        "|---|---|---|---:|---|",
    ]

    for pid, pdata in platforms.items():
        pmeta = pdata.get("metadata", {})
        os_str = pmeta.get("os", pid)
        arch_str = pmeta.get("arch", "")
        count = len(pdata.get("benches", []))
        failed = pmeta.get('xu_failed_benches', 0)
        status = f'⚠️ Xu {failed} 项失败' if failed else '✅ 输出校验通过'
        lines.append(f"| **`{pid}`** | {os_str} | `{arch_str}` | {count} 项 | {status} |")

    lines.extend([
        "",
        "### ⚡ 核心负载跨架构与跨平台对照 (Xu 运行耗时，ms)",
        "",
    ])

    # Versions belong to each measured platform, not the aggregation host.
    lines.extend(["", "### 编译工具链版本 / Measured toolchains", "",
                  "| Platform | Clang | Rust | Go | Swift |", "|---|---|---|---|---|"])
    for pid, data in platforms.items():
        versions = data.get("metadata", {}).get("toolchains", {})
        values = [versions.get(name) or "unavailable" for name in ("clang", "rustc", "go", "swiftc")]
        lines.append("| " + " | ".join([pid, *values]) + " |")
    lines.append("")

    key_benches = [
        "startup", "loop_sum", "fib", "matmul", "sroa_vec3", "chan_ping", "aes128_encrypt",
        "plb2_nqueen", "scimark_fft", "awfy_richards", "treap_ops",
    ]
    header = "| 核心负载 | 说明 |" + "".join(f" {pid} |" for pid in platforms.keys())
    separator = "|---|---|" + "".join("---:|" for _ in platforms)
    lines.append(header)
    lines.append(separator)

    for kb in key_benches:
        desc = BENCH_DESCRIPTIONS.get(kb, (kb, kb))[0]
        row = [f"`{kb}`", desc]
        for pid, pdata in platforms.items():
            b_item = next((b for b in pdata.get("benches", []) if b["name"] == kb), None)
            if b_item and b_item.get("xu_wall_ms") is not None:
                row.append(f"**{b_item['xu_wall_ms']:.2f}ms**")
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend([
        "",
        "> 💡 官网 [xulang.org/benchmarks](https://xulang.org/benchmarks) 已提供多架构实时交互切换 Tab，可查看各架构全量详细数据及内存/体积对比。",
    ])
    return "\n".join(lines)


def merge_platform_payloads(dir_path: Path) -> dict:
    platforms = {}
    latest_meta = {}
    all_categories = {}

    for file_path in dir_path.glob("**/*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "metadata" not in data or "benches" not in data:
            continue
        pid = data["metadata"].get("platform_id")
        if not pid or pid == "default":
            # Guess from filename or directory
            m = re.search(r"benchmarks[_-]([a-z0-9_-]+)\.json", file_path.name)
            if m:
                pid = m.group(1)
            else:
                pid = file_path.stem
        platforms[pid] = data
        latest_meta.update(data["metadata"])
        if "categories" in data:
            all_categories.update(data["categories"])

    if not platforms:
        raise ValueError(f"No valid benchmark JSON files found in {dir_path}")

    # Pick default platform priority: linux-arm64 > macos-arm64 > linux-x64 > first
    default_pid = next(
        (p for p in ["linux-arm64", "macos-arm64", "linux-x64", "windows-x64"] if p in platforms),
        list(platforms.keys())[0]
    )

    aggregated = {
        "metadata": {
            "date": latest_meta.get("date", date.today().isoformat()),
            "xu_version": latest_meta.get("xu_version", "0.8.8"),
            "platforms": list(platforms.keys()),
            "total_benches": max(len(p.get("benches", [])) for p in platforms.values()),
            "methodology": "Whole-program wall time, 7 iterations median; per-platform RSS method recorded separately, Linux RSS from untimed post-exec tracing; verified stdout",
        },
        "platforms": platforms,
        "default_platform": default_pid,
        "categories": all_categories or {k: {"zh": v[0], "en": v[1]} for k, v in CATEGORY_NAMES.items()},
        "benches": platforms[default_pid].get("benches", []),
    }
    return aggregated


def _canonical_bench_order() -> list[str]:
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import bench_crosslang  # noqa: E402
    return [b.name for b in bench_crosslang.BENCHES]


def _parse_rss_method(content: str) -> str:
    match = re.search(r"^# rss_method: (.+)$", content, re.M)
    return match.group(1).strip() if match else "unrecorded"


def _split_crosslang_sections(content: str) -> dict[str, list[str]]:
    """Split a crosslang.txt report into header, runtime, compile, and size sections."""
    lines = content.splitlines()
    has_runtime_heading = any(
        line.strip() == "## runtime + resources + binary size" for line in lines
    )
    sections: dict[str, list[str]] = {
        "header": [],
        "runtime": [],
        "compile": [],
        "size": [],
    }
    if not has_runtime_heading:
        for line in lines:
            if line.startswith("# ") and not line.startswith("# result:"):
                sections["header"].append(line)
            elif line.strip():
                sections["runtime"].append(line)
        return sections

    state = "header"
    skip_col_header = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## runtime + resources + binary size":
            state = "runtime"
            skip_col_header = True
            continue
        if stripped.startswith("## compile ("):
            state = "compile"
            skip_col_header = True
            continue
        if stripped == "## binary size (on-disk, not stripped)":
            state = "size"
            skip_col_header = True
            continue
        if stripped.startswith("## ") or stripped.startswith(("# wrote ", "# bins in ", "# FAIL:")):
            state = "ignore"
            skip_col_header = False
            continue

        if skip_col_header:
            skip_col_header = False
            if stripped.startswith("impl"):
                continue
        if state in sections:
            sections[state].append(line)

    while sections["header"] and not sections["header"][-1].strip():
        sections["header"].pop()
    for key in ("runtime", "compile", "size"):
        while sections[key] and not sections[key][-1].strip():
            sections[key].pop()
    return sections


def _build_merged_crosslang_txt(
    sorted_shards: list[tuple[int, int, str]],
    ordered_benches: list[str],
    shard_total: int,
) -> str:
    first_content = sorted_shards[0][2]
    first_sections = _split_crosslang_sections(first_content)

    header_lines: list[str] = []
    saw_benches = False
    saw_shard = False
    for line in first_sections["header"]:
        if line.startswith("# benches: "):
            header_lines.append(f"# benches: {', '.join(ordered_benches)}")
            saw_benches = True
        elif line.startswith("# shard: "):
            header_lines.append(f"# merged_shards: {shard_total}")
            saw_shard = True
        else:
            header_lines.append(line)
    if not saw_benches:
        header_lines.append(f"# benches: {', '.join(ordered_benches)}")
    if not saw_shard:
        header_lines.append(f"# merged_shards: {shard_total}")

    out: list[str] = [
        *header_lines,
        "",
        "## runtime + resources + binary size",
        f"{'impl':<22} {'bench':<14} {'best_ms':>8} {'med_ms':>8} {'rss_mib':>8} {'cpu_ms':>8} {'bytes':>10}  stdout",
    ]
    compile_lines: list[str] = []
    size_lines: list[str] = []
    for idx, total, content in sorted_shards:
        secs = _split_crosslang_sections(content)
        out.append(f"# shard-section: {idx}/{total}")
        out.extend(secs["runtime"])
        compile_lines.extend(secs["compile"])
        size_lines.extend(secs["size"])

    if compile_lines:
        out.extend([
            "",
            "## compile (already-built compilers, best-of-5)",
            f"{'impl':<22} {'bench':<14} {'best_ms':>8}",
            *compile_lines,
        ])
    if size_lines:
        out.extend([
            "",
            "## binary size (on-disk, not stripped)",
            f"{'impl':<22} {'bench':<14} {'bytes':>10} {'KiB':>8} {'vs Xu':>8}",
            *size_lines,
        ])
    return "\n".join(out) + "\n"


def merge_platform_shards(
    shard_dirs: list[Path],
    out_dir: Path,
    *,
    platform_id: str,
    platform_name: str | None = None,
    os_name: str | None = None,
    arch_name: str | None = None,
    expected_shard_total: int | None = None,
    expected_benches: list[str] | None = None,
    expect_full_registry: bool = False,
) -> dict:
    """Validate and losslessly merge all benchmark shards for one platform."""
    if not shard_dirs:
        raise ValueError(f"{platform_id}: no shard directories found")

    spec = PLATFORM_BY_ID.get(platform_id, {})
    resolved_platform_name = platform_name or spec.get("name")
    resolved_os = os_name or spec.get("os_name") or "Linux / macOS"
    resolved_arch = arch_name or spec.get("arch_name") or "arm64 / x64"
    if not resolved_platform_name:
        resolved_platform_name = f"{resolved_os} ({resolved_arch})"

    parsed_shards: list[tuple[int, int, str, dict, dict, dict, str]] = []
    seen_indices: set[int] = set()
    declared_total: int | None = None
    first_identity: dict | None = None
    first_toolchains: dict | None = None
    first_rss_method: str | None = None

    for sdir in shard_dirs:
        txt_path = sdir / "crosslang.txt"
        id_path = sdir / "compiler-identity.json"
        if not txt_path.is_file():
            raise ValueError(f"{platform_id}: missing crosslang.txt in {sdir}")
        if not id_path.is_file():
            raise ValueError(f"{platform_id}: missing compiler-identity.json in {sdir}")

        content = txt_path.read_text(encoding="utf-8")
        identity = json.loads(id_path.read_text(encoding="utf-8"))
        if identity.get("target") != platform_id:
            raise ValueError(
                f"{platform_id}: compiler-identity target mismatch {identity.get('target')!r} in {sdir}"
            )

        shard_match = re.search(r"^# shard:\s*(\d+)\s*/\s*(\d+)\s*$", content, re.M)
        if not shard_match:
            if len(shard_dirs) == 1 and (expected_shard_total in (None, 1)):
                idx, total = 1, 1
            else:
                raise ValueError(f"{platform_id}: missing `# shard: k/N` header in {txt_path}")
        else:
            idx, total = int(shard_match.group(1)), int(shard_match.group(2))

        if total < 1 or idx < 1 or idx > total:
            raise ValueError(f"{platform_id}: invalid shard index {idx}/{total} in {sdir}")
        if declared_total is None:
            declared_total = total
        elif total != declared_total:
            raise ValueError(f"{platform_id}: inconsistent shard total {total} vs {declared_total}")
        if idx in seen_indices:
            raise ValueError(f"{platform_id}: duplicate shard index {idx}/{total}")
        seen_indices.add(idx)

        if first_identity is None:
            first_identity = identity
        elif identity != first_identity:
            raise ValueError(
                f"{platform_id}: compiler-identity mismatch across shards (shard {idx})"
            )

        toolchains = parse_toolchains(content)
        if first_toolchains is None:
            first_toolchains = toolchains
        elif toolchains != first_toolchains:
            raise ValueError(
                f"{platform_id}: toolchain versions differ across shards (shard {idx}): "
                f"{toolchains} != {first_toolchains}"
            )

        rss_method = _parse_rss_method(content)
        if first_rss_method is None:
            first_rss_method = rss_method
        elif rss_method != first_rss_method:
            raise ValueError(
                f"{platform_id}: rss_method differs across shards (shard {idx}): "
                f"{rss_method!r} != {first_rss_method!r}"
            )

        shard_parsed = parse_crosslang_txt(content)
        parsed_shards.append((idx, total, content, identity, toolchains, shard_parsed, rss_method))

    assert declared_total is not None and first_identity is not None and first_toolchains is not None
    if expected_shard_total is not None and declared_total != expected_shard_total:
        raise ValueError(
            f"{platform_id}: expected {expected_shard_total} shards, got {declared_total}"
        )
    expected_indices = set(range(1, declared_total + 1))
    if seen_indices != expected_indices:
        missing = sorted(expected_indices - seen_indices)
        raise ValueError(f"{platform_id}: missing shards {missing} of {declared_total}")

    parsed_shards.sort(key=lambda item: item[0])

    all_names: set[str] = set()
    shard_order_names: list[str] = []
    for idx, _total, _content, _id, _tc, shard_parsed, _rss in parsed_shards:
        overlap = all_names & set(shard_parsed)
        if overlap:
            raise ValueError(
                f"{platform_id}: duplicate benchmark(s) across shards (shard {idx}): {sorted(overlap)}"
            )
        all_names.update(shard_parsed)
        shard_order_names.extend(shard_parsed.keys())

    ref_order = list(expected_benches) if expected_benches is not None else _canonical_bench_order()
    if expect_full_registry or expected_benches is not None:
        missing_benches = [b for b in ref_order if b not in all_names]
        extra_benches = sorted(all_names - set(ref_order))
        if missing_benches or extra_benches:
            raise ValueError(
                f"{platform_id}: workload coverage mismatch (missing={missing_benches}, extra={extra_benches})"
            )
        ordered_benches = ref_order
    else:
        ref_set = set(ref_order)
        ordered_benches = (
            [b for b in ref_order if b in all_names]
            + [b for b in shard_order_names if b not in ref_set]
        )

    merged_txt = _build_merged_crosslang_txt(
        [(idx, total, content) for idx, total, content, *_ in parsed_shards],
        ordered_benches,
        declared_total,
    )
    merged_parsed = parse_crosslang_txt(merged_txt)
    if list(merged_parsed) != ordered_benches:
        raise ValueError(f"{platform_id}: merged crosslang.txt order mismatch")

    meta = {
        "toolchains": first_toolchains,
        "rss_method": first_rss_method or "unrecorded",
        "xu_version": first_identity["xu_version"],
        "os": resolved_os,
        "arch": resolved_arch,
        "platform_id": platform_id,
        "platform_name": resolved_platform_name,
    }
    payload = build_benchmark_payload(merged_parsed, meta)
    summary_md = generate_markdown_summary(payload)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "crosslang.txt").write_text(merged_txt, encoding="utf-8", newline="\n")
    (out_dir / f"benchmarks-{platform_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "github_summary.md").write_text(summary_md, encoding="utf-8", newline="\n")
    (out_dir / "compiler-identity.json").write_text(
        json.dumps(first_identity, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def merge_all_platform_shards(
    shards_root: Path,
    out_root: Path,
    *,
    platform_shards: dict[str, int] | None = None,
    expect_full_registry: bool = False,
) -> dict[str, dict]:
    """Merge downloaded shard directories for all six platforms into benchmark-reports-<id>/."""
    if not shards_root.is_dir():
        raise ValueError(f"shards directory not found: {shards_root}")
    target_ids = list(platform_shards.keys()) if platform_shards else [s["platform_id"] for s in PLATFORM_SPECS]
    merged: dict[str, dict] = {}
    for pid in target_ids:
        pat = re.compile(rf"^benchmark-shard-{re.escape(pid)}-(\d+)-of-(\d+)$")
        dirs = sorted(
            p for p in shards_root.iterdir() if p.is_dir() and pat.fullmatch(p.name)
        )
        expected_total = platform_shards.get(pid) if platform_shards else None
        merged[pid] = merge_platform_shards(
            dirs,
            out_root / f"benchmark-reports-{pid}",
            platform_id=pid,
            expected_shard_total=expected_total,
            expect_full_registry=expect_full_registry,
        )
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, default=Path("reports/crosslang.txt"))
    parser.add_argument("--json-out", "-j", type=Path, help="Path to write structured JSON")
    parser.add_argument("--summary-out", "-s", type=Path, help="Path to write GitHub step summary Markdown")
    parser.add_argument("--xu-version", default="0.8.8")
    parser.add_argument("--os", default="Linux / macOS")
    parser.add_argument("--arch", default="arm64 / x64")
    parser.add_argument("--platform-id", default="default")
    parser.add_argument("--platform-name", default=None)
    parser.add_argument("--merge-dir", type=Path, help="Merge all platform JSONs inside a directory")
    parser.add_argument("--plan-ci-matrix", action="store_true", help="Emit CI build and sharded bench matrices")
    parser.add_argument("--mode", default="full", help="CI mode: full or quick")
    parser.add_argument("--benches", default="", help="Comma-separated CI benchmark subset")
    parser.add_argument("--shards", default="auto", help="CI sharding strategy: auto or 1")
    parser.add_argument("--macos-arm64-image", default="macos-latest", help="macOS ARM64 runner image")
    parser.add_argument("--github-output", type=Path, help="Append CI matrix outputs to GITHUB_OUTPUT")
    parser.add_argument("--merge-shards-root", type=Path, help="Merge benchmark-shard-* directories for all platforms")
    parser.add_argument("--merge-shards", type=Path, help="Merge shards for one platform from a directory")
    parser.add_argument("--out-dir", type=Path, help="Output directory for merged shard artifacts")
    parser.add_argument("--platform-shards-json", default="", help="JSON mapping platform_id -> expected shard count")
    parser.add_argument("--expected-shards", type=int, default=None, help="Expected shard count for --merge-shards")
    parser.add_argument("--expect-full-registry", action="store_true", help="Require merged shards to cover all BENCHES")
    args = parser.parse_args()

    if args.plan_ci_matrix:
        plan = plan_ci_matrix(
            mode=args.mode,
            benches=args.benches,
            shards=args.shards,
            macos_arm64_image=args.macos_arm64_image,
        )
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as fh:
                fh.write(f"build_matrix={json.dumps(plan['build_matrix'], separators=(',', ':'))}\n")
                fh.write(f"bench_matrix={json.dumps(plan['bench_matrix'], separators=(',', ':'))}\n")
                fh.write(f"platform_shards={json.dumps(plan['platform_shards'], separators=(',', ':'))}\n")
                fh.write(f"expect_full_registry={'true' if plan['expect_full_registry'] else 'false'}\n")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    if args.merge_shards_root:
        if not args.out_dir:
            sys.exit("--out-dir is required with --merge-shards-root")
        platform_shards = json.loads(args.platform_shards_json) if args.platform_shards_json else None
        merged = merge_all_platform_shards(
            args.merge_shards_root,
            args.out_dir,
            platform_shards=platform_shards,
            expect_full_registry=args.expect_full_registry,
        )
        print(f"Merged shards for {len(merged)} platforms into {args.out_dir}")
        return

    if args.merge_shards:
        if not args.out_dir:
            sys.exit("--out-dir is required with --merge-shards")
        pat = re.compile(rf"^benchmark-shard-{re.escape(args.platform_id)}-(\d+)-of-(\d+)$")
        shard_dirs = sorted(
            p for p in args.merge_shards.iterdir() if p.is_dir() and pat.fullmatch(p.name)
        )
        if not shard_dirs:
            shard_dirs = sorted(
                p for p in args.merge_shards.iterdir()
                if p.is_dir() and (p / "crosslang.txt").is_file()
            )
        payload = merge_platform_shards(
            shard_dirs,
            args.out_dir,
            platform_id=args.platform_id,
            platform_name=args.platform_name,
            os_name=None if args.os == "Linux / macOS" else args.os,
            arch_name=None if args.arch == "arm64 / x64" else args.arch,
            expected_shard_total=args.expected_shards,
            expect_full_registry=args.expect_full_registry,
        )
        print(f"Merged {len(shard_dirs)} shards ({payload['metadata']['total_benches']} benches) into {args.out_dir}")
        return

    if args.merge_dir:
        aggregated = merge_platform_payloads(args.merge_dir)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(aggregated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote merged payload to {args.json_out}")
        if args.summary_out:
            summary_md = generate_multi_arch_summary(aggregated)
            args.summary_out.parent.mkdir(parents=True, exist_ok=True)
            args.summary_out.write_text(summary_md, encoding="utf-8")
            print(f"Wrote merged summary Markdown to {args.summary_out}")
        return

    if not args.input.is_file():
        sys.exit(f"Input file not found: {args.input}")

    content = args.input.read_text(encoding="utf-8")
    parsed = parse_crosslang_txt(content)
    meta = {
        "toolchains": parse_toolchains(content),
        "rss_method": (re.search(r"^# rss_method: (.+)$", content, re.M).group(1)
                       if re.search(r"^# rss_method: (.+)$", content, re.M) else "unrecorded"),
        "xu_version": args.xu_version,
        "os": args.os,
        "arch": args.arch,
        "platform_id": args.platform_id,
        "platform_name": args.platform_name or f"{args.os} ({args.arch})",
    }
    payload = build_benchmark_payload(parsed, meta)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON payload to {args.json_out}")

    if args.summary_out:
        summary_md = generate_markdown_summary(payload)
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(summary_md, encoding="utf-8")
        print(f"Wrote summary Markdown to {args.summary_out}")


if __name__ == "__main__":
    main()
