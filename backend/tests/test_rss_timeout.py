"""Regression: a stalled RSS server must degrade to [] instead of hanging ingestion.

Context: ``rss_rows`` used to hand the URL to ``feedparser.parse``, which
performs its HTTP request with no timeout. One stalled outlet (TVN / La
Prensa / Crítica) blocked the live-ingestion worker thread forever, wedging
the scheduler in ``is_running`` so every later auto-run and ``live-now``
call answered ``already_running`` and no live feed was processed.
"""

from __future__ import annotations

import socket
import threading
import time

from evidentia.ingestion.fetchers.rss import rss_rows


def _black_hole_server() -> tuple[socket.socket, int]:
    """Accept connections and never answer — simulates a stalled feed server."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port = srv.getsockname()[1]

    def _serve() -> None:
        while True:
            try:
                conn, _ = srv.accept()
                # Hold the connection open without sending anything.
                with conn:
                    time.sleep(60)
            except OSError:
                return

    threading.Thread(target=_serve, daemon=True).start()
    return srv, port


def test_stalled_feed_returns_empty_within_timeout() -> None:
    srv, port = _black_hole_server()
    try:
        start = time.monotonic()
        rows = rss_rows(
            f"http://127.0.0.1:{port}/rss",
            medio="Probe",
            origen="probe",
            timeout_seconds=2,
        )
        elapsed = time.monotonic() - start
    finally:
        srv.close()
    assert rows == []
    # 2s timeout + generous slack for slow CI; the old code never returned.
    assert elapsed < 20, f"stalled feed blocked ingestion for {elapsed:.1f}s"
