"""Untimed Windows loopback capacity admission for fresh-connection workloads."""
from functools import lru_cache
import re
import socket
import struct
import subprocess
import sys
import time


@lru_cache(maxsize=1)
def _dynamic_tcp_range() -> tuple[int, int]:
    result = subprocess.run(["netsh.exe", "int", "ipv4", "show", "dynamicport", "tcp"],
                            capture_output=True, check=True, timeout=15)
    # Field labels are localized; start/count are the two numeric values.
    values = re.findall(rb":\s*(\d+)\s*$", result.stdout, re.MULTILINE)
    if len(values) != 2:
        raise RuntimeError("cannot read Windows dynamic TCP port range")
    start, count = map(int, values)
    if start <= 0 or count <= 0 or start + count > 65536:
        raise RuntimeError("invalid Windows dynamic TCP port range")
    return start, count


def _occupied_ports(table: bytes, start: int, count: int) -> set[int]:
    if len(table) < 4:
        raise RuntimeError("truncated Windows TCP table")
    rows = struct.unpack_from("<I", table)[0]
    if rows > (len(table) - 4) // 20:
        raise RuntimeError("truncated Windows TCP rows")
    occupied = set()
    for index in range(rows):
        _state, local_ip, local_raw, remote_ip, remote_raw = struct.unpack_from("<IIIII", table, 4 + index * 20)
        local, remote = socket.ntohs(local_raw & 65535), socket.ntohs(remote_raw & 65535)
        if start <= local < start + count:
            occupied.add(local)
        # A server-side TIME_WAIT row also reserves its loopback client's
        # ephemeral endpoint, even though the server's own port is fixed.
        if (local_ip & 255) == 127 and (remote_ip & 255) == 127 and start <= remote < start + count:
            occupied.add(remote)
    return occupied


def _tcp_ports(start: int, count: int) -> set[int]:
    import ctypes
    get_table = ctypes.WinDLL("iphlpapi").GetTcpTable
    get_table.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_int]
    get_table.restype = ctypes.c_ulong
    size = ctypes.c_ulong()
    code = get_table(None, ctypes.byref(size), False)
    if code not in (0, 122):
        raise OSError(code, "GetTcpTable size query failed")
    for _ in range(3):
        table = ctypes.create_string_buffer(max(size.value, 4))
        code = get_table(table, ctypes.byref(size), False)
        if code == 0:
            return _occupied_ports(table.raw[:size.value], start, count)
        if code != 122:
            raise OSError(code, "GetTcpTable failed")
    raise RuntimeError("Windows TCP table kept growing during collection")


def wait_for_loopback_capacity(connections: int, *, timeout_s: float = 300) -> float:
    """Wait before starting the process, without modifying kernel settings.

    Windows may retain each fresh loopback connection in TIME_WAIT. The
    whole workload plus 1024 spare ports must fit before a measured run.
    All implementations use the same admission policy; elapsed cooldown is
    reported separately and never added to target wall/CPU/RSS samples.
    """
    if sys.platform != "win32" or connections <= 0:
        return 0.0
    start, count = _dynamic_tcp_range()
    limit = count - connections - 1024
    if limit < 0:
        raise RuntimeError("dynamic TCP port range cannot fit this loopback workload")
    began = time.monotonic()
    announced = False
    while len(_tcp_ports(start, count)) > limit:
        if not announced:
            print(f"# TCP cooldown: waiting for {connections} connections + 1024 spare ports (outside timing)",
                  file=sys.stderr, flush=True)
            announced = True
        if time.monotonic() - began >= timeout_s:
            raise RuntimeError("Windows loopback ports did not recover before the cooldown deadline")
        time.sleep(1)
    waited = time.monotonic() - began
    if announced:
        print(f"# TCP cooldown: {waited:.1f}s excluded from target measurements", file=sys.stderr, flush=True)
    return waited
