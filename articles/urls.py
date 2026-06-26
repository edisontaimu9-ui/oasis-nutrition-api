"""Articles app URL routes"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SourceViewSet, ArticleViewSet

router = DefaultRouter(trailing_slash=True)
router.register("articles", ArticleViewSet, basename="article")
router.register("sources",  SourceViewSet,  basename="source")

urlpatterns = [
    path("", include(router.urls)),
]
