"""
Articles models — Source, Article, CrawlLog
"""

from django.db import models
from django.utils import timezone


class Source(models.Model):
    """A news/content source the crawler monitors."""

    REGION_CHOICES = [
        ("global",  "Global"),
        ("africa",  "Africa"),
        ("malawi",  "Malawi"),
    ]
    TYPE_CHOICES = [
        ("rss",     "RSS Feed"),
        ("scrape",  "HTML Scrape"),
        ("api",     "REST API"),
    ]

    name        = models.CharField(max_length=200, unique=True)
    url         = models.URLField(max_length=500)
    feed_url    = models.URLField(max_length=500, blank=True, null=True,
                                  help_text="RSS/Atom feed URL if different from main URL")
    region      = models.CharField(max_length=20, choices=REGION_CHOICES, default="global")
    source_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="rss")
    is_active   = models.BooleanField(default=True)
    logo_url    = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True)
    last_crawled = models.DateTimeField(null=True, blank=True)
    article_count = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["region", "name"]

    def __str__(self):
        return f"{self.name} [{self.region.upper()}]"


class Article(models.Model):
    """A crawled clinical nutrition article or news item."""

    CATEGORY_CHOICES = [
        ("clinical_nutrition", "Clinical Nutrition"),
        ("dietetics",          "Dietetics Practice"),
        ("research",           "Research & Evidence"),
        ("public_health",      "Public Health Nutrition"),
        ("pediatric",          "Pediatric Nutrition"),
        ("malnutrition",       "Malnutrition & Wasting"),
        ("food_security",      "Food Security"),
        ("policy",             "Policy & Guidelines"),
        ("education",          "Nutrition Education"),
        ("other",              "Other"),
    ]

    REGION_CHOICES = [
        ("global",  "Global"),
        ("africa",  "Africa"),
        ("malawi",  "Malawi"),
    ]

    # Core fields
    title         = models.CharField(max_length=500)
    summary       = models.TextField(blank=True)
    url           = models.URLField(max_length=1000, unique=True)
    source        = models.ForeignKey(Source, on_delete=models.CASCADE,
                                      related_name="articles")

    # Classification
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES,
                                     default="other")
    region        = models.CharField(max_length=20, choices=REGION_CHOICES,
                                     default="global")
    tags          = models.JSONField(default=list, blank=True,
                                     help_text="List of keyword tags")

    # Media
    image_url     = models.URLField(max_length=1000, blank=True, null=True)

    # Authors / journal
    authors       = models.CharField(max_length=500, blank=True)
    journal       = models.CharField(max_length=300, blank=True)

    # Dates
    published_at  = models.DateTimeField(null=True, blank=True)
    crawled_at    = models.DateTimeField(default=timezone.now)

    # Quality / relevance
    is_featured   = models.BooleanField(default=False)
    relevance_score = models.FloatField(default=0.0,
                                        help_text="0–1 keyword relevance score")

    class Meta:
        ordering  = ["-published_at", "-crawled_at"]
        indexes   = [
            models.Index(fields=["category"]),
            models.Index(fields=["region"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self):
        return f"[{self.category}] {self.title[:80]}"

    @property
    def short_summary(self):
        return self.summary[:200] + "..." if len(self.summary) > 200 else self.summary


class CrawlLog(models.Model):
    """Records each crawl run for monitoring and debugging."""

    STATUS_CHOICES = [
        ("running",   "Running"),
        ("completed", "Completed"),
        ("failed",    "Failed"),
        ("partial",   "Partial"),
    ]

    source          = models.ForeignKey(Source, on_delete=models.CASCADE,
                                        related_name="crawl_logs",
                                        null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default="running")
    started_at      = models.DateTimeField(default=timezone.now)
    completed_at    = models.DateTimeField(null=True, blank=True)
    articles_found  = models.PositiveIntegerField(default=0)
    articles_new    = models.PositiveIntegerField(default=0)
    articles_updated = models.PositiveIntegerField(default=0)
    error_message   = models.TextField(blank=True)
    triggered_by    = models.CharField(max_length=50, default="scheduler",
                                       help_text="scheduler | manual | api")

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        src = self.source.name if self.source else "ALL"
        return f"Crawl [{src}] {self.started_at:%Y-%m-%d %H:%M} — {self.status}"

    @property
    def duration_seconds(self):
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
