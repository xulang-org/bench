#!/usr/bin/env python3
"""
bench_local_fast.py - Fast local multi-platform benchmarking tool using macOS native and Docker.

Usage:
  python3 scripts/bench_local_fast.py --benches hex_codec,base64_codec,string_count
  python3 scripts/bench_local_fast.py --platform macos-arm64 --benches md5_chain
  python3 scripts/bench_local_fast.py --platform linux-x64 --benches hex_codec
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parent.parent
XU_ROOT = BENCH_ROOT.parent / "xu"
XU_BIN = XU_ROOT / "bin" / "xu"
XU_SRC = XU_ROOT / "src"

def run_cmd(cmd, check=True, capture=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE if capture else None,
                       text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed (exit {p.returncode}): {' '.join(cmd)}\n{p.stderr}")
    return p

def time_command(cmd, iters=3):
    durations = []
    out = ""
    for _ in range(iters):
        t0 = time.perf_counter()
        p = run_cmd(cmd, check=True, capture=True)
        t1 = time.perf_counter()
        durations.append((t1 - t0) * 1000.0)
        out = p.stdout.strip()
    durations.sort()
    med = durations[len(durations) // 2]
    return med, out

def ensure_docker_container(target_arch):
    container_name = f"xu_bench_{target_arch}"
    check = subprocess.run(["docker", "ps", "-q", "-f", f"name={container_name}"],
                           stdout=subprocess.PIPE, text=True)
    if not check.stdout.strip():
        # Start persistent container
        docker_platform = "linux/amd64" if target_arch == "x64" else "linux/arm64"
        subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "docker", "run", "-d", "--name", container_name,
            "--platform", docker_platform,
            "-v", "/tmp:/tmp",
            "debian:bookworm-slim", "sleep", "infinity"
        ], check=True, stdout=subprocess.DEVNULL)
    return container_name

def bench_xu_linux_docker(bench_name, target_arch="x64", iters=3):
    xu_target = f"linux-{target_arch}"
    src_xu = BENCH_ROOT / "tests" / "bench" / f"{bench_name}.xu"
    if not src_xu.is_file():
        raise FileNotFoundError(f"Missing {src_xu}")

    bin_path = f"/tmp/{bench_name}_linux_{target_arch}"
    env = os.environ.copy()
    env["XU_STDLIB_ROOT"] = str(XU_SRC)

    build_cmd = [
        str(XU_BIN), "build", "-O3",
        "--target", xu_target,
        str(src_xu), "-o", bin_path
    ]
    p_build = subprocess.run(build_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p_build.returncode != 0:
        return None, f"Build error: {p_build.stderr}"

    container_name = ensure_docker_container(target_arch)
    # Run inside container with python3 timing to measure pure binary execution time
    py_script = f"""
import time, subprocess
durations = []
out = ""
for _ in range({iters}):
    t0 = time.perf_counter()
    p = subprocess.run(['{bin_path}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    t1 = time.perf_counter()
    durations.append((t1 - t0) * 1000.0)
    out = p.stdout.strip()
durations.sort()
print(f'{{durations[len(durations)//2]:.2f}}||{{out}}')
"""
    p_run = subprocess.run([
        "docker", "exec", container_name, "python3", "-c", py_script
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p_run.returncode != 0:
        return None, f"Runtime error: {p_run.stderr}"

    raw = p_run.stdout.strip()
    if "||" in raw:
        med_str, out = raw.split("||", 1)
        return float(med_str), out
    return None, raw

def bench_peer_go(bench_name, iters=3):
    go_src = BENCH_ROOT / "tests" / "bench" / "cross" / f"{bench_name}.go"
    if not go_src.is_file():
        return None, "No Go peer"
    bin_path = Path("/tmp") / f"{bench_name}_go"
    p_build = subprocess.run(["go", "build", "-o", str(bin_path), str(go_src)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p_build.returncode != 0:
        return None, f"Go build error: {p_build.stderr}"
    med_ms, out = time_command([str(bin_path)], iters=iters)
    return med_ms, out

def bench_xu_macos(bench_name, iters=3):
    src_xu = BENCH_ROOT / "tests" / "bench" / f"{bench_name}.xu"
    bin_path = Path("/tmp") / f"{bench_name}_mac"
    env = os.environ.copy()
    env["XU_STDLIB_ROOT"] = str(XU_SRC)
    build_cmd = [str(XU_BIN), "build", "-O3", str(src_xu), "-o", str(bin_path)]
    p_build = subprocess.run(build_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p_build.returncode != 0:
        return None, f"Build error: {p_build.stderr}"
    med_ms, out = time_command([str(bin_path)], iters=iters)
    return med_ms, out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benches", default="hex_codec,base64_codec,string_count,md5_chain,fn_val_sum")
    parser.add_argument("--iters", type=int, default=3)
    args = parser.parse_args()

    if args.benches == "all":
        bench_dir = BENCH_ROOT / "tests" / "bench"
        bench_list = sorted([f.stem for f in bench_dir.glob("*.xu")])
    else:
        bench_list = [b.strip() for b in args.benches.split(",") if b.strip()]

    print("=" * 95)
    print("FAST LOCAL MULTI-PLATFORM BENCHMARK SUITE (macOS + Docker Linux)")
    print("=" * 95)
    print(f"{'Benchmark':<16} | {'macOS-arm64':<12} | {'Linux-arm64':<12} | {'Linux-x64':<12} | {'Go (macOS)':<10} | {'Ratio':<8}")
    print("-" * 95)

    for b in bench_list:
        mac_ms, _ = bench_xu_macos(b, iters=args.iters)
        lin_arm_ms, _ = bench_xu_linux_docker(b, target_arch="arm64", iters=args.iters)
        lin_x64_ms, _ = bench_xu_linux_docker(b, target_arch="x64", iters=args.iters)
        go_ms, _ = bench_peer_go(b, iters=args.iters)

        mac_str = f"{mac_ms:.2f}ms" if mac_ms is not None else "FAIL"
        larm_str = f"{lin_arm_ms:.2f}ms" if lin_arm_ms is not None else "FAIL"
        lx64_str = f"{lin_x64_ms:.2f}ms" if lin_x64_ms is not None else "FAIL"
        go_str = f"{go_ms:.2f}ms" if go_ms is not None else "N/A"

        ratio_str = "N/A"
        if mac_ms and go_ms and go_ms > 0:
            ratio = mac_ms / go_ms
            ratio_str = f"{ratio:.2f}x"

        print(f"{b:<16} | {mac_str:<12} | {larm_str:<12} | {lx64_str:<12} | {go_str:<10} | {ratio_str:<8}")

if __name__ == "__main__":
    main()
