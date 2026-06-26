from django.contrib import admin
from .models import Source, Article, CrawlLog


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display  = ["name", "region", "source_type", "is_active", "last_crawled", "article_count"]
    list_filter   = ["region", "source_type", "is_active"]
    search_fields = ["name", "url"]
    actions       = ["activate_sources", "deactivate_sources"]

    def activate_sources(self, request, queryset):
        queryset.update(is_active=True)
    activate_sources.short_description = "Activate selected sources"

    def deactivate_sources(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_sources.short_description = "Deactivate selected sources"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display  = ["title", "category", "region", "source", "published_at", "is_featured", "relevance_score"]
    list_filter   = ["category", "region", "is_featured", "source__region"]
    search_fields = ["title", "summary", "authors", "journal"]
    list_editable = ["is_featured"]
    date_hierarchy = "published_at"
    ordering      = ["-published_at"]


@admin.register(CrawlLog)
class CrawlLogAdmin(admin.ModelAdmin):
    list_display = ["__str__", "status", "articles_new", "articles_found",
                    "triggered_by", "started_at", "duration_seconds"]
    list_filter  = ["status", "triggered_by"]
    ordering     = ["-started_at"]
    readonly_fields = ["started_at", "completed_at", "duration_seconds"]
