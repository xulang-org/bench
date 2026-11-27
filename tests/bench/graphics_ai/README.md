# Graphics, Physics, AI/Quant, Modern Crypto & Multi-Core Suite (Batch G)

Self-contained deterministic benchmarks spanning 3D ray tracing, 2D image filtering & edge detection, fixed-point rigid-body collision physics, neural-network MLP inference, K-Means clustering, financial limit-order-book matching, Curve25519 / X25519 Diffie-Hellman key exchange, and multi-worker parallel MapReduce pipelines.

| Benchmark | Category | Domain / Algorithm | Scale | Peers | Golden |
|---|---|---|---|---|---|
| `raytrace_sphere` | `graphics` | 3D ray-sphere intersection, shadow rays & 3-bounce specular reflections (`f64`) | 320 × 240 × 16 spheres | `Go / C / Rust / Swift` | `67051\n1054947\n` |
| `image_sobel_blur` | `graphics` | 3×3 Gaussian blur & Sobel gradient edge pipeline (6 feedback passes) | 512 × 512 × 6 passes | `Go / C / Rust / Swift` | `347022\n56665161\n` |
| `physics_collision` | `graphics` | 2D 16×16 spatial-hash broad phase & Q10 fixed-point elastic circle collision | 512 bodies × 500 steps | `Go / C / Rust / Swift` | `5806\n207742175\n` |
| `mlp_inference` | `ai` | 3-layer dense MLP forward pass (`64 → 128 → 64 → 16`, ReLU, argmax) | 2,000 samples | `Go / C / Rust / Swift` | `8065\n3467\n` |
| `kmeans_cluster` | `ai` | 8D Euclidean Lloyd K-Means clustering (`f64`) | 8,192 pts × 16 clusters × 25 iters | `Go / C / Rust / Swift` | `267395148\n88966\n` |
| `order_book_match` | `ai` | Financial price-time FIFO limit order book matching & O(1) cancel | 250,000 events | `Go / C / Rust / Swift` | `161133\n760872136\n` |
| `x25519_dh` | `crypto` | RFC 7748 Curve25519 / X25519 16-limb Montgomery ladder chain | 100 iterations | `Go / C / Rust / Swift` | `100\nb1a5a73158904c020866c13939dd7e1aa26852ee1d2609c92e5a8f1debe2150a\n` |
| `parallel_mapreduce` | `concurrency` | 8-worker channel fan-out/fan-in histogram aggregation | 64 tasks × 131,072 events | `Go / Rust` | `8388608\n317365354\n` |
