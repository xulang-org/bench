"""Child-process wall time + rusage + live RSS curve sampling.

Peak RSS via wait4(ru_maxrss): macOS/BSD = bytes; Linux = KiB → bytes.
Live curve: poll RSS while the child runs (libproc /proc or ps fallback).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape


@dataclass(frozen=True)
class RunSample:
    wall_s: float
    max_rss_bytes: int
    user_s: float
    sys_s: float
    stdout: bytes
    stderr: bytes
    returncode: int
    # (elapsed_s, rss_mib) samples while running; may be empty if disabled/short
    rss_curve: tuple[tuple[float, float], ...] = ()

    @property
    def cpu_s(self) -> float:
        return self.user_s + self.sys_s

    @property
    def max_rss_mib(self) -> float:
        return self.max_rss_bytes / (1024.0 * 1024.0)


def _maxrss_to_bytes(ru_maxrss: int) -> int:
    if sys.platform.startswith("linux"):
        return int(ru_maxrss) * 1024
    return int(ru_maxrss)


def _status_rc(status: int) -> int:
    if hasattr(os, "WIFEXITED"):
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        if os.WIFSIGNALED(status):
            return -os.WTERMSIG(status)
        return -1
    return status


@dataclass
class _Win32Rusage:
    ru_maxrss: int = 0
    ru_utime: float = 0.0
    ru_stime: float = 0.0


def _run_one_win32(
    p: subprocess.Popen,
    timeout_s: float | None = None,
) -> tuple[int, _Win32Rusage]:
    try:
        p.wait(timeout=timeout_s)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        try:
            p.kill()
        except OSError:
            pass
        p.wait()
        rc = -9

    peak_bytes = 0
    user_s = 0.0
    sys_s = 0.0
    try:
        import ctypes
        from ctypes import wintypes

        handle = int(p._handle)

        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

        def _ft_to_s(ft: FILETIME) -> float:
            val = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
            return val / 10_000_000.0

        c_time, e_time, k_time, u_time = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        if ctypes.windll.kernel32.GetProcessTimes(
            handle, ctypes.byref(c_time), ctypes.byref(e_time), ctypes.byref(k_time), ctypes.byref(u_time)
        ):
            sys_s = _ft_to_s(k_time)
            user_s = _ft_to_s(u_time)

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        fn = getattr(ctypes.windll.psapi, "GetProcessMemoryInfo", None) or getattr(
            ctypes.windll.kernel32, "K32GetProcessMemoryInfo", None
        )
        if fn and fn(handle, ctypes.byref(pmc), pmc.cb):
            peak_bytes = int(pmc.PeakWorkingSetSize)
    except Exception:
        pass

    return rc, _Win32Rusage(ru_maxrss=peak_bytes, ru_utime=user_s, ru_stime=sys_s)


# --- live RSS readers -------------------------------------------------------

_darwin_proc_pidinfo = None
_darwin_pti_ok = False


def _init_darwin_rss() -> None:
    global _darwin_proc_pidinfo, _darwin_pti_ok
    if _darwin_proc_pidinfo is not None:
        return
    try:
        import ctypes

        lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)

        class proc_taskinfo(ctypes.Structure):
            _fields_ = [
                ("pti_virtual_size", ctypes.c_uint64),
                ("pti_resident_size", ctypes.c_uint64),
                ("pti_total_user", ctypes.c_uint64),
                ("pti_total_system", ctypes.c_uint64),
                ("pti_threads_user", ctypes.c_uint64),
                ("pti_threads_system", ctypes.c_uint64),
                ("pti_policy", ctypes.c_int32),
                ("pti_faults", ctypes.c_int32),
                ("pti_pageins", ctypes.c_int32),
                ("pti_cow_faults", ctypes.c_int32),
                ("pti_messages_sent", ctypes.c_int32),
                ("pti_messages_received", ctypes.c_int32),
                ("pti_syscalls_mach", ctypes.c_int32),
                ("pti_syscalls_unix", ctypes.c_int32),
                ("pti_csw", ctypes.c_int32),
                ("pti_threadnum", ctypes.c_int32),
                ("pti_numrunning", ctypes.c_int32),
                ("pti_priority", ctypes.c_int32),
            ]

        PROC_PIDTASKINFO = 4
        lib.proc_pidinfo.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        lib.proc_pidinfo.restype = ctypes.c_int
        info = proc_taskinfo()
        sz = ctypes.sizeof(info)

        def read(pid: int) -> int | None:
            n = lib.proc_pidinfo(pid, PROC_PIDTASKINFO, 0, ctypes.byref(info), sz)
            if n <= 0:
                return None
            return int(info.pti_resident_size)

        _darwin_proc_pidinfo = read
        _darwin_pti_ok = True
    except Exception:
        _darwin_proc_pidinfo = lambda _pid: None  # type: ignore
        _darwin_pti_ok = False


def rss_bytes_live(pid: int) -> int | None:
    """Best-effort current RSS of a live process, in bytes."""
    if sys.platform == "darwin":
        _init_darwin_rss()
        assert _darwin_proc_pidinfo is not None
        v = _darwin_proc_pidinfo(pid)
        if v is not None:
            return v
    if sys.platform.startswith("linux"):
        try:
            with open(f"/proc/{pid}/statm", "r", encoding="ascii") as f:
                parts = f.read().split()
            # second field = resident pages
            return int(parts[1]) * os.sysconf("SC_PAGE_SIZE")
        except (FileNotFoundError, ProcessLookupError, IndexError, ValueError, OSError):
            return None
    # portable fallback (ps rss is KiB on macOS and Linux)
    try:
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(pid)], stderr=subprocess.DEVNULL
        )
        s = out.decode().strip()
        if not s:
            return None
        return int(s.split()[0]) * 1024
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def run_one(
    cmd: list[str],
    *,
    sample_interval_s: float | None = None,
    timeout_s: float | None = None,
    cwd: str | Path | None = None,
) -> RunSample:
    """Run cmd; optionally sample live RSS every sample_interval_s seconds.

    sample_interval_s=None → no live curve (peak still from wait4/Win32).
    timeout_s: kill the child (returncode -9) if it runs longer than this.
    """
    with tempfile.SpooledTemporaryFile(max_size=4 * 1024 * 1024) as out_f, tempfile.SpooledTemporaryFile(
        max_size=256 * 1024
    ) as err_f:
        t0 = time.perf_counter()
        p = subprocess.Popen(cmd, stdout=out_f, stderr=err_f, cwd=cwd)
        curve: list[tuple[float, float]] = []
        status = 0
        ru = None
        sample = sample_interval_s is not None and sample_interval_s > 0
        limit = timeout_s is not None and timeout_s > 0
        if sys.platform == "win32" or not hasattr(os, "wait4"):
            status, ru = _run_one_win32(p, timeout_s=timeout_s)
        elif not sample:
            # Blocking wait4. A WNOHANG + 50ms sleep quantized every short
            # O2/O3/--no-regcache run to ~56ms wall while CPU was 7–25ms.
            killer = None
            if limit:
                def _kill() -> None:
                    try:
                        p.kill()
                    except OSError:
                        pass

                killer = threading.Timer(timeout_s, _kill)
                killer.daemon = True
                killer.start()
            try:
                _pid, status, ru = os.wait4(p.pid, 0)
            finally:
                if killer is not None:
                    killer.cancel()
        else:
            slice_s = sample_interval_s
            while True:
                wpid, status, ru = os.wait4(p.pid, os.WNOHANG)
                now = time.perf_counter() - t0
                if wpid == 0:
                    if limit and now >= timeout_s:
                        try:
                            p.kill()
                        except OSError:
                            pass
                        _pid, status, ru = os.wait4(p.pid, 0)
                        break
                    b = rss_bytes_live(p.pid)
                    if b is not None:
                        curve.append((now, b / (1024.0 * 1024.0)))
                    time.sleep(slice_s)
                    continue
                break
        wall = time.perf_counter() - t0
        out_f.seek(0)
        err_f.seek(0)
        out = out_f.read()
        err = err_f.read()

    assert ru is not None
    peak = _maxrss_to_bytes(ru.ru_maxrss)
    # Ensure curve ends at wall with peak (so SVG shows true max even if poll missed it)
    if curve:
        last_t, last_r = curve[-1]
        if wall > last_t + 1e-6:
            curve.append((wall, max(last_r, peak / (1024.0 * 1024.0))))
        else:
            curve[-1] = (wall, max(last_r, peak / (1024.0 * 1024.0)))
    elif sample_interval_s and sample_interval_s > 0:
        curve.append((0.0, peak / (1024.0 * 1024.0)))
        curve.append((wall, peak / (1024.0 * 1024.0)))

    return RunSample(
        wall_s=wall,
        max_rss_bytes=peak,
        user_s=float(ru.ru_utime),
        sys_s=float(ru.ru_stime),
        stdout=out,
        stderr=err,
        returncode=_status_rc(status),
        rss_curve=tuple(curve),
    )


# --- curve I/O / SVG --------------------------------------------------------

PALETTE = [
    "#2563eb",  # blue
    "#dc2626",  # red
    "#16a34a",  # green
    "#ca8a04",  # yellow/brown
    "#9333ea",  # purple
    "#0891b2",  # cyan
    "#ea580c",  # orange
    "#4b5563",  # gray
]


def write_curve_csv(path: Path, curve: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["t_ms,rss_mib"]
    for t, r in curve:
        lines.append(f"{t * 1000:.3f},{r:.4f}")
    path.write_text("\n".join(lines) + "\n")


def write_rss_svg(
    path: Path,
    series: dict[str, list[tuple[float, float]] | tuple[tuple[float, float], ...]],
    *,
    title: str,
    width: int = 720,
    height: int = 360,
) -> None:
    """Multi-series RSS-vs-time SVG (no external deps)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = {k: list(v) for k, v in series.items() if v}
    if not clean:
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<text x="20" y="40">no RSS samples for {escape(title)}</text></svg>\n'
        )
        return

    pad_l, pad_r, pad_t, pad_b = 56, 24, 36, 48
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    t_max = max(pt[0] for pts in clean.values() for pt in pts)
    r_max = max(pt[1] for pts in clean.values() for pt in pts)
    t_max = t_max if t_max > 0 else 1e-3
    r_max = r_max if r_max > 0 else 1.0
    # headroom
    r_max *= 1.08

    def xy(t: float, r: float) -> tuple[float, float]:
        x = pad_l + (t / t_max) * plot_w
        y = pad_t + plot_h - (r / r_max) * plot_h
        return x, y

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        f'<text x="{pad_l}" y="22" font-family="system-ui,sans-serif" font-size="14" '
        f'font-weight="600" fill="#111">{escape(title)}</text>',
        # axes
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" '
        f'stroke="#9ca3af" stroke-width="1"/>',
        f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" '
        f'y2="{pad_t + plot_h}" stroke="#9ca3af" stroke-width="1"/>',
        f'<text x="{pad_l + plot_w / 2}" y="{height - 10}" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="11" fill="#4b5563">'
        f'time (ms), x-max={t_max * 1000:.1f}</text>',
        f'<text x="14" y="{pad_t + plot_h / 2}" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="11" fill="#4b5563" '
        f'transform="rotate(-90 14 {pad_t + plot_h / 2})">RSS (MiB)</text>',
    ]

    # y ticks
    for i in range(5):
        frac = i / 4
        r = r_max * frac
        _x, y = xy(0, r)
        parts.append(
            f'<line x1="{pad_l}" y1="{y}" x2="{pad_l + plot_w}" y2="{y}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{pad_l - 6}" y="{y + 4}" text-anchor="end" '
            f'font-family="system-ui,sans-serif" font-size="10" fill="#6b7280">'
            f"{r:.2f}</text>"
        )

    legend_x = pad_l + 8
    legend_y = pad_t + 8
    for idx, (name, pts) in enumerate(clean.items()):
        color = PALETTE[idx % len(PALETTE)]
        d = "M " + " L ".join(f"{xy(t, r)[0]:.2f},{xy(t, r)[1]:.2f}" for t, r in pts)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        parts.append(
            f'<rect x="{legend_x}" y="{legend_y + idx * 16}" width="10" height="10" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{legend_x + 16}" y="{legend_y + 9 + idx * 16}" '
            f'font-family="system-ui,sans-serif" font-size="11" fill="#111">'
            f"{escape(name)}</text>"
        )

    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def sparkline(curve: list[tuple[float, float]] | tuple[tuple[float, float], ...], width: int = 24) -> str:
    """Tiny unicode sparkline for log lines."""
    if not curve:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    vals = [r for _t, r in curve]
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        return blocks[0] * min(width, len(vals))
    # downsample
    n = len(vals)
    out = []
    for i in range(min(width, n)):
        j = int(i * (n - 1) / max(width - 1, 1))
        v = vals[j]
        idx = int((v - lo) / (hi - lo) * (len(blocks) - 1))
        out.append(blocks[idx])
    return "".join(out)
