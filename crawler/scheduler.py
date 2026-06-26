"""
Oasis Nutrition Crawler — APScheduler
Runs periodic crawls in the background within Django's process.
No Redis or Celery needed — Termux-friendly.
"""

import logging
from django.conf import settings

logger = logging.getLogger("crawler")

_scheduler = None


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.jobstores.memory import MemoryJobStore
        _scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={"coalesce": True, "max_instances": 1},
            timezone=settings.TIME_ZONE,
        )
    return _scheduler


def crawl_all_sources(triggered_by: str = "scheduler"):
    """
    Main crawl job — iterates all active sources and runs their crawlers.
    Called by the scheduler or triggered via API.
    """
    from articles.models import Source, CrawlLog
    from crawler.registry import get_crawler_for_source
    from django.utils import timezone

    active_sources = Source.objects.filter(is_active=True)
    if not active_sources.exists():
        logger.warning("No active sources found. Run: python manage.py seed_sources")
        return

    log = CrawlLog.objects.create(
        source=None,
        status="running",
        triggered_by=triggered_by,
    )

    total_found = 0
    total_new   = 0

    for source in active_sources:
        src_log = CrawlLog.objects.create(
            source=source,
            status="running",
            triggered_by=triggered_by,
        )
        try:
            crawler = get_crawler_for_source(source)
            if not crawler:
                logger.warning(f"No crawler for source: {source.name}")
                src_log.status = "failed"
                src_log.error_message = "No crawler class registered for this source"
            else:
                found, new = crawler.run()
                total_found += found
                total_new   += new
                src_log.articles_found = found
                src_log.articles_new   = new
                src_log.status = "completed"
        except Exception as e:
            logger.error(f"Source crawl failed [{source.name}]: {e}", exc_info=True)
            src_log.status = "failed"
            src_log.error_message = str(e)[:1000]
        finally:
            src_log.completed_at = timezone.now()
            src_log.save()

    log.status         = "completed"
    log.articles_found = total_found
    log.articles_new   = total_new
    log.completed_at   = timezone.now()
    log.save()

    logger.info(f"Full crawl complete — found={total_found}, new={total_new}")


def crawl_single_source(source_id: int, triggered_by: str = "api"):
    """Crawl a single source by ID."""
    from articles.models import Source, CrawlLog
    from crawler.registry import get_crawler_for_source
    from django.utils import timezone

    try:
        source = Source.objects.get(pk=source_id, is_active=True)
    except Source.DoesNotExist:
        logger.error(f"Source {source_id} not found or inactive")
        return None

    log = CrawlLog.objects.create(
        source=source,
        status="running",
        triggered_by=triggered_by,
    )

    try:
        crawler = get_crawler_for_source(source)
        if not crawler:
            log.status = "failed"
            log.error_message = "No crawler registered for this source"
        else:
            found, new = crawler.run()
            log.articles_found = found
            log.articles_new   = new
            log.status = "completed"
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)[:1000]
    finally:
        log.completed_at = timezone.now()
        log.save()

    return log


def start_scheduler():
    """Start the APScheduler with configured interval."""
    config    = settings.CRAWLER_SETTINGS
    interval  = config.get("CRAWL_INTERVAL_HOURS", 6)
    scheduler = get_scheduler()

    if scheduler.running:
        return

    scheduler.add_job(
        crawl_all_sources,
        trigger="interval",
        hours=interval,
        id="crawl_all",
        replace_existing=True,
        kwargs={"triggered_by": "scheduler"},
    )

    scheduler.start()
    logger.info(f"Crawl scheduler started — interval: every {interval}h")


def stop_scheduler():
    """Gracefully stop the scheduler."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Crawl scheduler stopped")
