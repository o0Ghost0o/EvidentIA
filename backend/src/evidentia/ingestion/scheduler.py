"""Periodic background auto-ingestion scheduler (Pitch mode & live feeds).

Provides non-blocking background scheduling of live news ingestion with
dynamic feature flag toggling, interval adjustment and on-demand trigger.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from evidentia.config import get_settings

logger = logging.getLogger(__name__)


class AutoIngestScheduler:
    """Manages periodic background ingestion runs using asyncio."""

    def __init__(self) -> None:
        settings = get_settings()
        self.enabled: bool = bool(settings.auto_ingest_enabled)
        self.interval_minutes: int = max(1, int(settings.auto_ingest_interval_minutes))
        self.last_run: datetime | None = None
        self.next_run: datetime | None = None
        self.is_running: bool = False
        self.last_status: str = "idle"  # idle | running | success | error
        self.last_error: str | None = None
        self.items_ingested_last_run: int = 0
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    def start(self) -> None:
        """Start the background monitoring loop if not already running."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._scheduler_loop(), name="auto_ingest_loop")
            logger.info(
                "AutoIngestScheduler started (enabled=%s, interval=%dm)",
                self.enabled,
                self.interval_minutes,
            )

    async def stop(self) -> None:
        """Cancel and await the scheduler loop on application shutdown."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("AutoIngestScheduler stopped cleanly.")

    async def _scheduler_loop(self) -> None:
        """Periodic loop that checks if an auto-ingestion run is due."""
        while True:
            try:
                now = datetime.now(timezone.utc)
                if self.enabled:
                    if self.next_run is None:
                        self.next_run = now + timedelta(minutes=self.interval_minutes)

                    if now >= self.next_run and not self.is_running:
                        logger.info("AutoIngestScheduler: starting scheduled live ingestion...")
                        await self.run_now(use_seed=False)
                        self.next_run = datetime.now(timezone.utc) + timedelta(
                            minutes=self.interval_minutes
                        )
                else:
                    self.next_run = None

                # Sleep 15 seconds between evaluations
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("AutoIngestScheduler loop encountered error: %s", exc)
                await asyncio.sleep(15)

    async def run_now(self, use_seed: bool = False) -> dict[str, Any]:
        """Trigger an ingestion job asynchronously in a worker thread."""
        async with self._lock:
            if self.is_running:
                return {
                    "status": "already_running",
                    "message": "An ingestion job is currently executing.",
                }
            self.is_running = True
            self.last_status = "running"
            self.last_error = None

        started_at = datetime.now(timezone.utc)
        try:
            from evidentia.ingestion.pipeline import run_ingestion

            # Run in worker thread so event loop remains 100% responsive
            report = await asyncio.to_thread(run_ingestion, use_seed=use_seed)

            news_valid = report.get("families", {}).get("noticias.csv", {}).get("valid", 0)
            self.items_ingested_last_run = news_valid
            self.last_run = datetime.now(timezone.utc)
            self.last_status = "success"
            self.last_error = None
            logger.info(
                "AutoIngestScheduler: ingestion completed successfully (%d news, source=%s, took=%.1fs)",
                news_valid,
                report.get("source"),
                (self.last_run - started_at).total_seconds(),
            )
            return {"status": "success", "report": report}
        except Exception as exc:
            self.last_status = "error"
            self.last_error = str(exc)
            logger.exception("AutoIngestScheduler: ingestion job failed: %s", exc)
            return {"status": "error", "error": str(exc)}
        finally:
            self.is_running = False
            if self.enabled:
                self.next_run = datetime.now(timezone.utc) + timedelta(
                    minutes=self.interval_minutes
                )

    def configure(
        self,
        enabled: bool | None = None,
        interval_minutes: int | None = None,
    ) -> dict[str, Any]:
        """Dynamically configure scheduler settings."""
        if enabled is not None:
            self.enabled = bool(enabled)
            if self.enabled:
                self.next_run = datetime.now(timezone.utc) + timedelta(
                    minutes=self.interval_minutes
                )
            else:
                self.next_run = None

        if interval_minutes is not None:
            self.interval_minutes = max(1, int(interval_minutes))
            if self.enabled:
                self.next_run = datetime.now(timezone.utc) + timedelta(
                    minutes=self.interval_minutes
                )

        logger.info(
            "AutoIngestScheduler reconfigured: enabled=%s, interval=%dm, next_run=%s",
            self.enabled,
            self.interval_minutes,
            self.next_run,
        )
        return self.get_status()

    def get_status(self) -> dict[str, Any]:
        """Return the current scheduler state for UI / API."""
        return {
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "is_running": self.is_running,
            "last_status": self.last_status,
            "last_error": self.last_error,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "items_ingested_last_run": self.items_ingested_last_run,
        }


# Global singleton instance
scheduler = AutoIngestScheduler()
