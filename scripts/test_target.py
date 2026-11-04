#!/usr/bin/env python3
"""Smoke-test the isolated HTTP and raw TCP target services on loopback."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "provisioning/roles/router/files/target_server.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"target service exited early with code {process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=0.3) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.1)
    raise TimeoutError("target HTTP service did not become ready")


def main() -> int:
    http_port = free_port()
    tcp_port = free_port()
    while tcp_port == http_port:
        tcp_port = free_port()

    config = {
        "target_bind": "127.0.0.1",
        "http_port": http_port,
        "tcp_port": tcp_port,
        "flag_web": "WEB123",
        "flag_tcp": "TCP123",
        "flag_pcap": "PCAP12",
    }

    with tempfile.TemporaryDirectory(prefix="firewall-vpn-test-") as directory:
        config_path = Path(directory) / "target-config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        environment = os.environ.copy()
        environment["TARGET_CONFIG"] = str(config_path)
        process = subprocess.Popen(
            [sys.executable, str(TARGET)],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            base = f"http://127.0.0.1:{http_port}"
            wait_for_http(f"{base}/health", process)

            with urllib.request.urlopen(f"{base}/flag", timeout=2) as response:
                body = response.read().decode("utf-8")
            assert "VPN_PATH_FLAG=WEB123" in body, body

            with urllib.request.urlopen(f"{base}/capture", timeout=2) as response:
                assert response.headers.get("X-CRCZ-Lab-Flag") == "PCAP12"

            with socket.create_connection(("127.0.0.1", tcp_port), timeout=2) as connection:
                banner = connection.recv(4096).decode("ascii")
            assert "TCP_SERVICE_FLAG=TCP123" in banner, banner

            print("Target-service smoke test passed (HTTP health, web flag, capture header, TCP banner).")
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            if process.returncode not in (0, -15):
                stderr = process.stderr.read() if process.stderr else ""
                print(f"target service stderr:\n{stderr}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
