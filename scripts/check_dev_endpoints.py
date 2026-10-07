#!/usr/bin/env python3
"""Pre-flight check for EvidentIA dev endpoints in Vertex DC.

Checks DNS, TCP connectivity, TLS handshake, and HTTP status codes
for both dev-evidentia.vertexdc.com and dev-evidentia-api.vertexdc.com.
"""

from __future__ import annotations

import os
import socket
import ssl
import sys
import urllib.request
import urllib.error

FRONTEND_URL = os.getenv("E2E_BASE_URL", "https://dev-evidentia.vertexdc.com").rstrip("/")
API_URL = os.getenv("E2E_API_URL", "https://dev-evidentia-api.vertexdc.com").rstrip("/")


def check_host(host: str, port: int = 443, timeout: float = 5.0) -> bool:
    """Check DNS resolution and TCP handshake."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception as exc:
        print(f"  ❌ TCP connection to {host}:{port} failed: {exc}")
        return False


def probe_url(url: str, timeout: float = 6.0) -> tuple[int | None, str]:
    """Probe an HTTPS URL returning (status_code, summary)."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EvidentIA-E2E-Preflight/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            return resp.status, "OK"
    except urllib.error.HTTPError as exc:
        return exc.code, f"HTTP {exc.code} {exc.reason}"
    except urllib.error.URLError as exc:
        return None, f"URL Error: {exc.reason}"
    except Exception as exc:
        return None, f"Exception: {exc}"


def main() -> int:
    print("=" * 65)
    print(" 🔍 EVIDENTIA DEV ENDPOINTS PRE-FLIGHT CHECK")
    print("=" * 65)
    print(f" Frontend Target: {FRONTEND_URL}")
    print(f" Backend API Target: {API_URL}")
    print("-" * 65)

    all_ready = True

    targets = [
        ("Frontend Web", FRONTEND_URL, FRONTEND_URL.replace("https://", "").replace("http://", "").split("/")[0]),
        ("Backend API Health", f"{API_URL}/health", API_URL.replace("https://", "").replace("http://", "").split("/")[0]),
    ]

    for label, url, host in targets:
        print(f"\n[+] Probing {label} ({url})...")
        tcp_ok = check_host(host, 443)
        if not tcp_ok:
            all_ready = False
            continue

        status, detail = probe_url(url)
        if status == 200:
            print(f"  ✅ Status: 200 OK — Service is LIVE and healthy.")
        elif status in (525, 520, 521, 522):
            print(f"  ⚠️  Status: {status} ({detail}) — Cloudflare to origin SSL/upstream issue (deploy likely building or starting).")
            all_ready = False
        elif status == 503:
            print(f"  ⚠️  Status: 503 Service Unavailable — Origin proxy is waiting for containers to start.")
            all_ready = False
        else:
            print(f"  ℹ️  Status: {status} ({detail})")
            if status is None or status >= 500:
                all_ready = False

    print("\n" + "=" * 65)
    if all_ready:
        print(" 🎉 ALL DEV ENDPOINTS ARE READY FOR E2E TESTING!")
        print("=" * 65)
        return 0
    else:
        print(" ⚠️  SOME ENDPOINTS ARE NOT READY YET.")
        print("    If a build/deploy is in progress in Coolify, wait a few moments.")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(main())
