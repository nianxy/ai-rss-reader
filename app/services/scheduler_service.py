from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.config_service import load_rss_config
from app.services.digest_service import DailyDigestService
from app.services.email_service import EmailService
from app.services.llm_service import LLMService
from app.services.rss_service import RSSIngestService

settings = get_settings()

scheduler = BackgroundScheduler(timezone='Asia/Shanghai')


def _parse_cron_expr(expr: str) -> tuple[str, str, str, str, str]:
    cleaned = (expr or '').strip().strip('"').strip("'")
    parts = cleaned.split()
    if len(parts) != 5:
        raise ValueError(f'Invalid cron expression: "{expr}" (expected 5 fields)')
    return parts[0], parts[1], parts[2], parts[3], parts[4]


def run_fetch_job() -> None:
    rss_cfg = load_rss_config(settings.rss_config_path)
    llm = LLMService()
    with SessionLocal() as db:
        svc = RSSIngestService(db=db, llm=llm)
        for category in rss_cfg.categories:
            svc.run_for_category(category)


def run_daily_digest_job() -> None:
    llm = LLMService()
    email = EmailService()
    with SessionLocal() as db:
        svc = DailyDigestService(db=db, llm=llm, email=email)
        svc.send_yesterday_digest()


def start_scheduler() -> None:
    if scheduler.running:
        return

    fetch_min, fetch_hour, fetch_dom, fetch_month, fetch_dow = _parse_cron_expr(settings.fetch_cron)
    daily_min, daily_hour, daily_dom, daily_month, daily_dow = _parse_cron_expr(settings.daily_summary_cron)

    scheduler.add_job(
        run_fetch_job,
        trigger=CronTrigger(minute=fetch_min, hour=fetch_hour, day=fetch_dom, month=fetch_month, day_of_week=fetch_dow),
        id='fetch_rss_job',
        replace_existing=True,
    )
    scheduler.add_job(
        run_daily_digest_job,
        trigger=CronTrigger(minute=daily_min, hour=daily_hour, day=daily_dom, month=daily_month, day_of_week=daily_dow),
        id='daily_digest_job',
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
