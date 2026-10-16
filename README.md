# Xu 基准与横测

完整基准套件的独立仓库：语言能力、标准库、优化档、编译时间、
Benchmarks Game、Clang 差距、资源曲线与 stdout 金标。

默认与 `xu` 放在同级目录；可通过 `XU_ROOT=/path/to/xu` 选择编译器源码仓库。
编译器与标准库仍由 Xu 仓库构建，本仓库维护负载、对照实现和测量方法。
产品负载通过 Xu 的 hosted seed resolver 与 hermetic wrapper 编译；
显式 oracle 诊断只接受冻结的 bootstrap primer。

```sh
make list
make crosslang ARGS="--quick --benches=loop_sum --iters=1 --sample-ms=0"
make game ARGS="--verify-only --benches=nbody"
make stdlib ARGS="--bench=rand_read --iters=1"
make opt-levels ARGS="--xu=../xu/bin/xu --quick --check"
python3 scripts/bench_clang_gap_manifest.py
python3 -m pytest tests scripts/test_bench_game.py
```

更多负载说明见 [套件索引](tests/bench/README.md)。
`reports/`、曲线和运行产物仅本机保留，不提交。原语言仓库的 `docs/`
评测记录留在原处；需要旧基线时显式传入其路径。
`make compile` 默认要求 `reports/bench_compile.baseline.txt`，可以用
`BENCH_BASELINE=/path/to/baseline.txt` 指定经过校准的基线。

## 测量口径

跨语言测试默认预跑一次，再取七次独立进程运行的中位数；核对 stdout
后才接受结果。wall time 和 CPU time 来自直接执行的进程。

Linux 的 `wait4.ru_maxrss` 会保留启动器在 exec 前的内存峰值，不能直接
当作目标程序的 RSS。Linux 因此另行执行相同命令：原生 C 采样器在目标
exec 完成后、退出前读取该地址空间的 `VmHWM`，并以 `smaps_rollup` 的
当前 RSS 补齐短进程计数。每次 RSS 重跑都核对退出状态；跨语言负载还
要求 stdout/stderr 与计时运行一致。采样器构建及 ptrace 开销不计入
wall/CPU time。Linux 需要可用的 `cc`、`clang` 或 `gcc` 及 ptrace 权限；
采样不可用时失败，不回退到失真的旧数值。此协议记为
`linux-post-exec-vmhwm-v1`，旧 Linux RSS 结果需要重新测量。

macOS 使用 `wait4` 的峰值 RSS，Windows 使用 `PeakWorkingSetSize`。
RSS 描述目标进程本身，不合计子进程；原生负载只允许一次 exec。
实时 RSS 曲线来自计时进程的实际轮询，不用另一次运行的峰值补点。
不同负载的资源范围只用于描述，不能按范围下限判定某语言整体最优。
