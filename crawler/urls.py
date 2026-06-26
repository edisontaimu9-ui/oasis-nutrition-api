"""Crawler app URL routes"""

from django.urls import path
from .views import CrawlTriggerView, CrawlStatusView, CrawlLogsView

urlpatterns = [
    path("crawl/trigger/", CrawlTriggerView.as_view(), name="crawl-trigger"),
    path("crawl/status/",  CrawlStatusView.as_view(),  name="crawl-status"),
    path("crawl/logs/",    CrawlLogsView.as_view(),    name="crawl-logs"),
]
