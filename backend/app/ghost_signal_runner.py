import asyncio
from datetime import datetime, timezone
from typing import Callable, Optional

from .config import (
    DEFAULT_TIMEZONE_OFFSET_MINUTES,
    GHOST_SIGNAL_BATCH_SIZE,
    GHOST_SIGNAL_POLL_INTERVAL_SECONDS,
)
from .logging import configure_logging
from .repository import Repository, get_repository

logger = configure_logging()


def _run_once(repo: Repository) -> int:
    now = datetime.now(timezone.utc)
    return repo.deliver_pending_messages(
        now,
        batch_size=GHOST_SIGNAL_BATCH_SIZE,
        default_tz_offset_minutes=DEFAULT_TIMEZONE_OFFSET_MINUTES,
    )


async def run_forever(
    stop_event: asyncio.Event,
    repo_factory: Callable[[], Repository] = get_repository,
) -> None:
    while not stop_event.is_set():
        try:
            repo = repo_factory()
            _run_once(repo)
        except Exception:
            logger.info(
                "ghost_signal_runner",
                {"status": "tick_failed", "reason": "exception"},
            )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=GHOST_SIGNAL_POLL_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue


async def stop_task(task: Optional[asyncio.Task]) -> None:
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return
