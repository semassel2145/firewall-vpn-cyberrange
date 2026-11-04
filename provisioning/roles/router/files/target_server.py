#!/usr/bin/env python3
"""HTTP target plus a simple TCP banner service for the isolated lab."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import socketserver
import threading

CONFIG_PATH = os.environ.get("TARGET_CONFIG", "/etc/firewall-vpn-target.json")
with open(CONFIG_PATH, encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)

BIND = CONFIG.get("target_bind", "192.168.20.1")
HTTP_PORT = int(CONFIG.get("http_port", 8080))
TCP_PORT = int(CONFIG.get("tcp_port", 2323))
FLAG_WEB = CONFIG["flag_web"]
FLAG_TCP = CONFIG["flag_tcp"]
FLAG_PCAP = CONFIG["flag_pcap"]


class TargetHandler(BaseHTTPRequestHandler):
    server_version = "CRCZ-Lab-Target/1.0"

    def _send(self, status: int, body: str, extra_headers=None):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self._send(200, "Firewall Evasion Lab target is online.\n")
        elif self.path == "/flag":
            self._send(200, f"VPN_PATH_FLAG={FLAG_WEB}\n")
        elif self.path == "/capture":
            self._send(
                200,
                "Capture this HTTP response on tun0 and inspect its headers.\n",
                {"X-CRCZ-Lab-Flag": FLAG_PCAP},
            )
        elif self.path == "/robots.txt":
            self._send(200, "User-agent: *\nDisallow: /capture\n")
        else:
            self._send(404, "Not found\n")

    def log_message(self, fmt, *args):
        return


class TcpFlagHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(
            f"Firewall Evasion Lab diagnostic TCP service\nTCP_SERVICE_FLAG={FLAG_TCP}\n".encode("ascii")
        )
        # Echo any client data so this behaves as a small generic TCP service.
        while True:
            data = self.request.recv(4096)
            if not data:
                return
            self.request.sendall(data)


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    tcp_server = ReusableThreadingTCPServer((BIND, TCP_PORT), TcpFlagHandler)
    threading.Thread(target=tcp_server.serve_forever, name="lab-tcp-service", daemon=True).start()
    ThreadingHTTPServer((BIND, HTTP_PORT), TargetHandler).serve_forever()
