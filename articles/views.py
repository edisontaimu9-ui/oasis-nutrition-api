"""
Articles Views — REST API endpoints for Oasis CNST
"""

from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters

from .models import Source, Article, CrawlLog
from .serializers import (
    SourceSerializer,
    ArticleListSerializer,
    ArticleDetailSerializer,
    CrawlLogSerializer,
    CrawlTriggerSerializer,
)


# ─── Article Filter ──────────────────────────────────────────────────────────────

class ArticleFilter(django_filters.FilterSet):
    category    = django_filters.CharFilter(field_name="category")
    region      = django_filters.CharFilter(field_name="region")
    source      = django_filters.NumberFilter(field_name="source__id")
    source_name = django_filters.CharFilter(field_name="source__name",
                                            lookup_expr="icontains")
    is_featured = django_filters.BooleanFilter(field_name="is_featured")
    tag         = django_filters.CharFilter(method="filter_by_tag",
                                            label="Tag (exact match)")
    published_after  = django_filters.DateTimeFilter(field_name="published_at",
                                                     lookup_expr="gte")
    published_before = django_filters.DateTimeFilter(field_name="published_at",
                                                     lookup_expr="lte")
    min_relevance    = django_filters.NumberFilter(field_name="relevance_score",
                                                   lookup_expr="gte")

    def filter_by_tag(self, queryset, name, value):
        return queryset.filter(tags__contains=value)

    class Meta:
        model  = Article
        fields = ["category", "region", "source", "is_featured"]


# ─── Viewsets ────────────────────────────────────────────────────────────────────

class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/sources/         — list all active sources
    GET /api/v1/sources/{id}/    — source detail
    GET /api/v1/sources/regions/ — breakdown by region
    """
    queryset = Source.objects.filter(is_active=True).annotate(
        computed_article_count=Count("articles")
    )
    serializer_class = SourceSerializer
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["region", "source_type"]
    search_fields    = ["name", "description"]
    ordering_fields  = ["name", "region", "last_crawled", "article_count"]
    ordering         = ["region", "name"]

    @action(detail=False, methods=["get"], url_path="regions")
    def regions(self, request):
        """Return source counts grouped by region."""
        data = (
            Source.objects.filter(is_active=True)
            .values("region")
            .annotate(source_count=Count("id"), article_count=Count("articles"))
            .order_by("region")
        )
        return Response(list(data))


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/articles/            — list articles (filtered/searched/paginated)
    GET /api/v1/articles/{id}/       — article detail
    GET /api/v1/articles/featured/   — featured articles only
    GET /api/v1/articles/categories/ — articles grouped by category with counts
    GET /api/v1/articles/latest/     — 10 most recent articles
    GET /api/v1/articles/malawi/     — Malawi-region articles
    GET /api/v1/articles/africa/     — Africa-region articles
    """
    queryset = Article.objects.select_related("source").order_by(
        "-published_at", "-crawled_at"
    )
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = ArticleFilter
    search_fields    = ["title", "summary", "authors", "journal", "tags"]
    ordering_fields  = ["published_at", "crawled_at", "relevance_score", "title"]
    ordering         = ["-published_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArticleDetailSerializer
        return ArticleListSerializer

    @action(detail=False, methods=["get"])
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True)[:20]
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        qs = self.get_queryset()[:10]
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def malawi(self, request):
        qs = self.get_queryset().filter(region="malawi")
        page = self.paginate_queryset(qs)
        serializer = ArticleListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def africa(self, request):
        qs = self.get_queryset().filter(region__in=["africa", "malawi"])
        page = self.paginate_queryset(qs)
        serializer = ArticleListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Return article counts per category."""
        data = (
            Article.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response(list(data))

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Overall stats snapshot for Oasis CNST dashboard."""
        total      = Article.objects.count()
        by_region  = list(Article.objects.values("region").annotate(count=Count("id")))
        by_cat     = list(
            Article.objects.values("category").annotate(count=Count("id")).order_by("-count")
        )
        last_crawl = (
            CrawlLog.objects.filter(status="completed")
            .order_by("-completed_at")
            .values("completed_at", "articles_new")
            .first()
        )
        return Response({
            "total_articles": total,
            "by_region":      by_region,
            "by_category":    by_cat,
            "last_crawl":     last_crawl,
            "sources_active": Source.objects.filter(is_active=True).count(),
            "generated_at":   timezone.now(),
        })
