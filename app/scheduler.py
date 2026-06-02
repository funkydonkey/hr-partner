import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.pipeline import run_pipeline


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Paris")
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=8, minute=0, timezone="Europe/Paris"),
        id="daily_job_search",
        name="Daily job search pipeline",
        replace_existing=True,
    )
    return scheduler
