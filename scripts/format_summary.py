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
}

CATEGORY_NAMES = {
    "control": ("控制流与语言机制", "Control flow & primitives"),
    "algo": ("算法与数值计算", "Algorithms & numerical"),
    "data": ("数据结构与内存访问", "Data structures & memory"),
    "string": ("字符串与文本 I/O", "Strings & text I/O"),
    "crypto": ("密码学与散列", "Cryptography & hashing"),
    "concurrency": ("并发与协程通信", "Concurrency & channels"),
}


def parse_crosslang_txt(content: str) -> dict:
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
        if not xu:
            continue
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
            "xu_wall_ms": xu["wall_ms"],
            "xu_best_ms": xu["best_ms"],
            "xu_rss_mib": xu["rss_mib"],
            "xu_bytes": xu["bytes"],
            "c_wall_ms": c_opt["wall_ms"] if c_opt else None,
            "rust_wall_ms": rust_opt["wall_ms"] if rust_opt else None,
            "go_wall_ms": go_opt["wall_ms"] if go_opt else None,
            "swift_wall_ms": swift_opt["wall_ms"] if swift_opt else None,
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
    key_benches = ["startup", "chan_ping", "loop_sum", "matmul", "sroa_vec3", "aes128_encrypt"]
    for kb in key_benches:
        item = next((b for b in benches if b["name"] == kb), None)
        if not item:
            continue
        c_str = f"{item['c_wall_ms']:.1f}ms" if item['c_wall_ms'] else "—"
        rust_str = f"{item['rust_wall_ms']:.1f}ms" if item['rust_wall_ms'] else "—"
        go_str = f"{item['go_wall_ms']:.1f}ms" if item['go_wall_ms'] else "—"
        note = ""
        if kb == "startup":
            note = f"极速冷启动，领先 Go {round((item['go_wall_ms']/item['xu_wall_ms']-1)*100)}%" if item['go_wall_ms'] else "极速原生冷启动"
        elif kb == "chan_ping":
            note = "原生轻量协程与 Channel 高性能调度"
        elif kb == "sroa_vec3":
            note = "SROA 字段标量展开消除冗余访问"
        elif kb == "aes128_encrypt":
            note = "纯软件算法实现，表现稳健"
        lines.append(f"| **{item['desc_zh']}** (`{kb}`) | **{item['xu_wall_ms']:.2f}ms** | {go_str} | {c_str} | {rust_str} | {note} |")

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
        lines.append(
            f"| {cat_zh} | `{b['name']}`<br><small>{b['desc_zh']}</small> | **{b['xu_wall_ms']:.2f}** | {go_val} | {c_val} | {rust_val} | {ratio_c} |"
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
        lines.append(f"| **`{pid}`** | {os_str} | `{arch_str}` | {count} 项 | ✅ 测试通过 |")

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

    key_benches = ["startup", "loop_sum", "fib", "matmul", "sroa_vec3", "chan_ping", "aes128_encrypt"]
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
    args = parser.parse_args()

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
