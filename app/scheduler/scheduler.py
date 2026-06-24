from __future__ import annotations

import logging

from app.core.config import settings
from app.scheduler.jobs import check_ticket_sla_timeout

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ModuleNotFoundError:
    AsyncIOScheduler = None
    IntervalTrigger = None
    scheduler = None
else:
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        logger.info("[Scheduler] APScheduler disabled by config")
        return
    if scheduler is None or IntervalTrigger is None:
        logger.warning("[Scheduler] APScheduler is not installed; scheduler will not start")
        return
    if scheduler.running:
        logger.info("[Scheduler] APScheduler already running")
        return

    # This in-process scheduler is intended for single-worker deployments. With multiple
    # uvicorn workers, enable it in exactly one process or move scheduling to a dedicated worker.
    scheduler.add_job(
        check_ticket_sla_timeout,
        trigger=IntervalTrigger(minutes=settings.sla_check_interval_minutes),
        id="check_ticket_sla_timeout",
        name="检查工单SLA超时",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started")


def shutdown_scheduler() -> None:
    if scheduler is None:
        return
    if not scheduler.running:
        return
    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] APScheduler shutdown")
