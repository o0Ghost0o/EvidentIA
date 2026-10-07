"""Shared HTTP GET with backoff for transient egress failures."""

from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

RETRY_WAITS = (10.0, 30.0, 90.0)


def get_with_retry(
    client: httpx.Client, url: str, params: dict | None = None, what: str = "request"
) -> httpx.Response:
    """GET with retries on timeouts/connection errors and 429/5xx statuses."""
    last: Exception | None = None
    for attempt, wait in enumerate((0.0, *RETRY_WAITS)):
        if wait:
            logger.warning("%s: retrying in %ss (attempt %d)", what, wait, attempt + 1)
            time.sleep(wait)
        try:
            resp = client.get(url, params=params)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last = exc
            logger.warning("%s: %s — backing off", what, exc)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < len(RETRY_WAITS):
                logger.warning("%s: HTTP %s — backing off", what, resp.status_code)
                continue
        resp.raise_for_status()
        return resp
    assert last is not None
    raise last
