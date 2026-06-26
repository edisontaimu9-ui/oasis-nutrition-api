"""Crawler App Config — starts APScheduler when Django is ready."""

from django.apps import AppConfig


class CrawlerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crawler"

    def ready(self):
        """Start background scheduler when Django finishes loading."""
        from django.conf import settings

        # Only start scheduler in the main process (not in migrations / shell)
        import sys
        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        if "shell" in sys.argv or "test" in sys.argv:
            return

        if settings.CRAWLER_SETTINGS.get("ENABLE_SCHEDULER", True):
            try:
                from crawler.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                import logging
                logging.getLogger("crawler").error(f"Scheduler start failed: {e}")
