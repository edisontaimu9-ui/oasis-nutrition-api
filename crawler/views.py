"""
Crawler Views — Crawl trigger, status, and log endpoints
"""

import threading
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from articles.models import CrawlLog, Source
from articles.serializers import CrawlLogSerializer, CrawlTriggerSerializer

logger = logging.getLogger("crawler")


class CrawlTriggerView(APIView):
    """
    POST /api/v1/crawl/trigger/
    Body (optional):
        { "source_id": 3 }       → crawl single source
        { "force": true }        → skip recently-crawled check
        {}                       → crawl all sources
    """

    def post(self, request):
        serializer = CrawlTriggerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        source_id = serializer.validated_data.get("source_id")

        if source_id:
            # Fire single-source crawl in background thread
            thread = threading.Thread(
                target=self._run_single,
                args=(source_id,),
                daemon=True,
            )
            thread.start()
            return Response({
                "status":  "triggered",
                "message": f"Crawl started for source ID {source_id}",
                "async":   True,
            }, status=status.HTTP_202_ACCEPTED)

        # Crawl all sources in background thread
        thread = threading.Thread(
            target=self._run_all,
            daemon=True,
        )
        thread.start()
        return Response({
            "status":  "triggered",
            "message": "Full crawl started for all active sources",
            "async":   True,
        }, status=status.HTTP_202_ACCEPTED)

    def _run_all(self):
        from crawler.scheduler import crawl_all_sources
        crawl_all_sources(triggered_by="api")

    def _run_single(self, source_id):
        from crawler.scheduler import crawl_single_source
        crawl_single_source(source_id, triggered_by="api")


class CrawlStatusView(APIView):
    """
    GET /api/v1/crawl/status/
    Returns: latest crawl log + scheduler state + source stats.
    """

    def get(self, request):
        from crawler.scheduler import get_scheduler

        latest = (
            CrawlLog.objects.filter(source__isnull=True)
            .order_by("-started_at")
            .first()
        )
        running_count = CrawlLog.objects.filter(status="running").count()

        scheduler = get_scheduler()
        next_run  = None
        try:
            job = scheduler.get_job("crawl_all")
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        except Exception:
            pass

        return Response({
            "scheduler_running": scheduler.running,
            "next_scheduled_crawl": next_run,
            "active_crawls": running_count,
            "last_full_crawl": CrawlLogSerializer(latest).data if latest else None,
            "sources": {
                "total":  Source.objects.count(),
                "active": Source.objects.filter(is_active=True).count(),
            },
        })


class CrawlLogsView(APIView):
    """
    GET /api/v1/crawl/logs/?limit=20&source_id=3
    Returns recent crawl logs.
    """

    def get(self, request):
        limit     = min(int(request.query_params.get("limit", 20)), 100)
        source_id = request.query_params.get("source_id")

        qs = CrawlLog.objects.all().order_by("-started_at")
        if source_id:
            qs = qs.filter(source_id=source_id)

        serializer = CrawlLogSerializer(qs[:limit], many=True)
        return Response({
            "count":   qs.count(),
            "results": serializer.data,
        })
