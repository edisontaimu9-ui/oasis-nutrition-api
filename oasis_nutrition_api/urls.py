"""Oasis Nutrition API — Root URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    return JsonResponse({
        "name": "Oasis CNST Nutrition News API",
        "version": "1.0.0",
        "description": "Clinical nutrition news & updates crawler for Oasis CNST",
        "endpoints": {
            "articles": "/api/v1/articles/",
            "sources":  "/api/v1/sources/",
            "crawl":    "/api/v1/crawl/",
            "admin":    "/admin/",
        },
        "regions": ["global", "africa", "malawi"],
        "categories": [
            "clinical_nutrition", "dietetics", "research", "public_health",
            "pediatric", "malnutrition", "food_security", "policy", "education",
        ],
    })


urlpatterns = [
    path("",          api_root),
    path("admin/",    admin.site.urls),
    path("api/v1/",   include("articles.urls")),
    path("api/v1/",   include("crawler.urls")),
]
