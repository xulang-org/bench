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
