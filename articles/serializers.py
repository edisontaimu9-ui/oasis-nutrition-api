"""
DRF Serializers — Source, Article, CrawlLog
"""

from rest_framework import serializers
from .models import Source, Article, CrawlLog


class SourceSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Source
        fields = [
            "id", "name", "url", "region", "source_type",
            "is_active", "logo_url", "description",
            "last_crawled", "article_count", "created_at",
        ]


class ArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no full summary."""
    source_name   = serializers.CharField(source="source.name", read_only=True)
    source_region = serializers.CharField(source="source.region", read_only=True)
    source_logo   = serializers.URLField(source="source.logo_url", read_only=True)

    class Meta:
        model  = Article
        fields = [
            "id", "title", "short_summary", "url",
            "category", "region", "tags",
            "image_url", "authors", "journal",
            "published_at", "crawled_at",
            "is_featured", "relevance_score",
            "source_name", "source_region", "source_logo",
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for single article view."""
    source = SourceSerializer(read_only=True)

    class Meta:
        model  = Article
        fields = [
            "id", "title", "summary", "url", "source",
            "category", "region", "tags",
            "image_url", "authors", "journal",
            "published_at", "crawled_at",
            "is_featured", "relevance_score",
        ]


class CrawlLogSerializer(serializers.ModelSerializer):
    source_name    = serializers.CharField(source="source.name", read_only=True,
                                           default="ALL SOURCES")
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model  = CrawlLog
        fields = [
            "id", "source_name", "status",
            "started_at", "completed_at", "duration_seconds",
            "articles_found", "articles_new", "articles_updated",
            "error_message", "triggered_by",
        ]


class CrawlTriggerSerializer(serializers.Serializer):
    """Input serializer for POST /crawl/trigger/"""
    source_id = serializers.IntegerField(
        required=False,
        help_text="Optional: crawl a specific source by ID. Omit for all sources.",
    )
    force     = serializers.BooleanField(
        default=False,
        help_text="Force re-crawl even if recently crawled.",
    )
