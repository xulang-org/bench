# NIST SciMark2 浮点科学计算基准接入

参考来源：NIST SciMark 2.0（Public Domain，Roldan Pozo & Bruce Miller）。
本批 5 项负载采用与 SciMark2 一致的滞后斐波那契随机数生成器 `Random`（`m1 = 2147483647`、`m2 = 65536`、`i = 4`、`j = 16`）构造确定性输入，保持同算法直译，不启用第三方 BLAS/FFT 库或手写 SIMD。

为避免 ARM64 FMA 与 x86_64 标量指令在末位 ULP 上的细微差异导致浮点字符串漂移，连续浮点汇总类题目对总和按固定尺度（`×1000` 或 `×100`）四舍五入为整数校验和，并确保参考值远离 `.5` 舍入边界。

| 注册名 | SciMark2 内核 | 规模与校验方式 |
|---|---|---|
| `scimark_montecarlo` | `MonteCarlo` | 5,000,000 次单位正方形采样，输出落入单位圆四分象限的精确次数 |
| `scimark_sor` | `SOR` | 100×100 网格 500 轮二维超松弛迭代（`omega = 1.25`），输出网格和 ×1000 取整 |
| `scimark_lu` | `LU` | 100×100 稠密矩阵 30 轮部分主元 LU 分解，输出矩阵绝对值总和 ×100 + 主元校验和 |
| `scimark_sparse` | `SparseCompRow` | 10,000 阶 / 50,000 非零元 CSR 矩阵-向量乘 500 轮，输出 ×1000 取整 |
| `scimark_fft` | `FFT` | 1024 点 Cooley-Tukey Radix-2 复数正/逆 FFT 200 轮，输出 ×10 取整 |
