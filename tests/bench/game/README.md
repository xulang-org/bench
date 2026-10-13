# Benchmarks Game 对齐套件（Wave 1）

对齐 [Computer Language Benchmarks Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/) 的玩具题，用作 Xu 与 **C / C++ / Rust / Go** 的横向尺子。

与上级 [`../README.md`](../README.md) 的「语言能力」微基准分开：本题集跟官方题意与 stdout 格式，不混进 `bench_crosslang.py`。

## 规则

- **单线程**同算法直译；禁止手写 SIMD / unsafe / OpenMP / goroutine 冲榜写法。
- `argv[1]` = N；缺省用 perf N（便于手跑）。
- verify：小 N，stdout 与 `golden/`（官方 download）逐字节一致。
- perf：大 N；报 **median + best** wall、**median 峰值 RSS**、**median CPU**；默认 `--sample-ms=5` 写出 RSS 时间曲线（CSV + SVG）。
- `nbody` 用 `[5]Body`（与 `cross/nbody.rs` / C `sys[5]` 同构）。`fannkuchredux` 用 `[12]int`。

## Wave 1

| 题 | verify N | perf N | 度量面 |
|---|---:|---:|---|
| `nbody` | 1000 | 5000000 | f64 多体 |
| `fannkuchredux` | 7 | 12 | 整数置换 |
| `spectralnorm` | 100 | 5500 | f64 幂迭代 |
| `mandelbrot` | 200 | 4000 | 位图 PBM |
| `fasta` | 1000 | 2500000 | LCG + 写出 |
| `binarytrees` | 10 | 18 | 分配（Xu 用节点池，非 GC） |

Wave 2（未实现）：`revcomp` / `knucleotide` / `pidigits` / `regexredux`。

## 跑法

```bash
make game
# 或
python3 scripts/bench_game.py --out reports/bench_game.latest.txt
python3 scripts/bench_game.py --verify-only
python3 scripts/bench_game.py --benches=nbody,spectralnorm --quick
python3 scripts/bench_game.py --out /tmp/g.txt --discard-first --iters=5
```

报告：[`reports/game.md`](../../../reports/game.md)
