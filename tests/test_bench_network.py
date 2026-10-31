"""Capacity waits must stay outside samples and fail when capacity is unavailable."""
import importlib
from pathlib import Path
import socket
import struct
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bench_network as network


def row(local, remote, local_ip="127.0.0.1", remote_ip="127.0.0.1"):
    address = lambda value: int.from_bytes(socket.inet_aton(value), "little")
    return struct.pack("<IIIII", 11, address(local_ip), socket.htons(local),
                       address(remote_ip), socket.htons(remote))


def test_tcp_table_counts_server_side_time_wait_and_unique_ephemeral_ports():
    data = struct.pack("<I", 4) + row(19901, 50000) + row(50000, 19901) + row(50001, 443, remote_ip="1.1.1.1") + row(80, 50002, remote_ip="1.1.1.1")
    assert network._occupied_ports(data, 49152, 16384) == {50000, 50001}


@pytest.mark.parametrize("data", [b"", struct.pack("<I", 2) + row(19901, 50000)])
def test_truncated_tcp_table_is_an_error(data):
    with pytest.raises(RuntimeError, match="truncated"):
        network._occupied_ports(data, 49152, 16384)


def test_dynamic_range_handles_localized_field_labels(monkeypatch):
    from types import SimpleNamespace
    response = SimpleNamespace(stdout="协议 tcp\n起始端口 : 49152\n端口数 : 16384\n".encode())
    network._dynamic_tcp_range.cache_clear()
    monkeypatch.setattr(network.subprocess, "run", lambda *a, **kw: response)
    assert network._dynamic_tcp_range() == (49152, 16384)
    network._dynamic_tcp_range.cache_clear()


def test_wait_is_bounded_and_reports_capacity_recovery(monkeypatch, capsys):
    clock = [0.0]
    monkeypatch.setattr(network.sys, "platform", "win32")
    monkeypatch.setattr(network, "_dynamic_tcp_range", lambda: (49152, 16384))
    monkeypatch.setattr(network.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(network.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    samples = iter([set(range(15000)), set(range(14000)), set(range(12000))])
    monkeypatch.setattr(network, "_tcp_ports", lambda *args: next(samples))
    assert network.wait_for_loopback_capacity(3200, timeout_s=5) == 2
    assert "outside timing" in capsys.readouterr().err


def test_exhaustion_is_not_reported_as_a_successful_measurement(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(network.sys, "platform", "win32")
    monkeypatch.setattr(network, "_dynamic_tcp_range", lambda: (49152, 16384))
    monkeypatch.setattr(network, "_tcp_ports", lambda *args: set(range(15000)))
    monkeypatch.setattr(network.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(network.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    with pytest.raises(RuntimeError, match="did not recover"):
        network.wait_for_loopback_capacity(3200, timeout_s=2)


def test_admission_precedes_every_interleaved_sample(monkeypatch, tmp_path):
    levels = importlib.import_module("bench_opt_levels")
    from types import SimpleNamespace
    events = []
    def measured(*args, **kwargs):
        assert events[-1] == "admit"
        events.append("measure")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"", wall_s=.1,
                               cpu_s=.1, max_rss_mib=1, rss_curve=())
    monkeypatch.setattr(levels, "run_one", measured)
    rows, errors = levels.timed_interleaved({("xu", 1): Path("xu")}, 2, discard_first=True,
                                           sample_interval_s=.01, cwd=tmp_path, expect=b"ok",
                                           before_run=lambda: events.append("admit"))
    assert not errors and rows
    assert events == ["admit", "measure"] * 4


def test_non_windows_does_not_query_windows_settings(monkeypatch):
    monkeypatch.setattr(network.sys, "platform", "linux")
    monkeypatch.setattr(network, "_dynamic_tcp_range", lambda: pytest.fail("Windows query on Unix"))
    assert network.wait_for_loopback_capacity(3200) == 0


def test_admission_precedes_cross_language_warmup_samples_and_curve(monkeypatch):
    cross = importlib.import_module("bench_crosslang")
    from types import SimpleNamespace
    events = []
    def measured(*args, **kwargs):
        assert events[-1] == "admit"
        events.append("measure")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"", wall_s=.1,
                               cpu_s=.1, max_rss_mib=1, rss_curve=())
    monkeypatch.setattr(cross, "run_one", measured)
    result = cross.timed_runs("program", 2, discard_first=True, sample_interval_s=.01,
                              before_run=lambda: events.append("admit"))
    assert result.stdout == "ok"
    assert events == ["admit", "measure"] * 4
