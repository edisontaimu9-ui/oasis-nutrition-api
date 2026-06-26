"""
Oasis Nutrition Crawler — Base class
Shared utilities for all source crawlers.
"""

import logging
import hashlib
import re
from datetime import datetime
from typing import Optional

import requests
import feedparser
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger("crawler")

# ─── Nutrition keyword taxonomy ──────────────────────────────────────────────────

CLINICAL_NUTRITION_KEYWORDS = {
    # High relevance — clinical
    "clinical_nutrition": [
        "clinical nutrition", "medical nutrition therapy", "MNT", "NCP",
        "nutrition care process", "enteral nutrition", "parenteral nutrition",
        "TPN", "tube feeding", "nasogastric", "PEG", "nutrition support",
        "malnutrition", "nutritional assessment", "dietary assessment",
        "ADIME", "nutrition diagnosis", "dietitian", "dietetics",
        "registered dietitian", "RD", "RDN",
    ],
    # Research
    "research": [
        "randomized controlled trial", "systematic review", "meta-analysis",
        "cohort study", "clinical trial", "evidence-based nutrition",
        "nutrition research", "dietary intervention", "biomarker",
        "nutritional epidemiology",
    ],
    # Public health / SSA relevant
    "public_health": [
        "public health nutrition", "food security", "nutrition surveillance",
        "stunting", "wasting", "undernutrition", "micronutrient deficiency",
        "vitamin A deficiency", "iron deficiency anemia", "iodine deficiency",
        "zinc deficiency", "WASH", "nutrition transition",
        "sub-Saharan Africa", "Malawi", "Africa nutrition",
    ],
    # Pediatric
    "pediatric": [
        "pediatric nutrition", "infant nutrition", "breastfeeding",
        "complementary feeding", "CMAM", "RUTF", "MUAC",
        "stunting", "wasting", "child malnutrition", "growth monitoring",
        "SAM", "MAM", "therapeutic feeding",
    ],
    # Chronic disease / NCD
    "dietetics": [
        "diabetes nutrition", "renal nutrition", "cardiovascular nutrition",
        "oncology nutrition", "obesity", "metabolic syndrome",
        "dyslipidemia", "hypertension diet", "DASH diet",
        "glycemic index", "insulin resistance",
    ],
    # Policy
    "policy": [
        "nutrition policy", "food fortification", "WHO guideline",
        "dietary guideline", "nutrition program", "WFP", "UNICEF nutrition",
        "PEPFAR nutrition", "global nutrition report",
    ],
}

# Flat list of all keywords for quick containment checks
ALL_KEYWORDS = [kw.lower() for kws in CLINICAL_NUTRITION_KEYWORDS.values() for kw in kws]

CATEGORY_PRIORITY = [
    "clinical_nutrition", "pediatric", "research",
    "public_health", "dietetics", "policy", "other",
]


# ─── Base Crawler ────────────────────────────────────────────────────────────────

class BaseCrawler:
    """
    Base class for all Oasis Nutrition source crawlers.
    Subclasses implement `fetch_articles()` and return a list of dicts.
    """

    def __init__(self, source):
        """
        Args:
            source: articles.models.Source instance
        """
        self.source  = source
        self.config  = settings.CRAWLER_SETTINGS
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config["USER_AGENT"],
            "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        self.timeout = self.config["REQUEST_TIMEOUT"]

    # ── HTTP helpers ─────────────────────────────────────────────────────────────

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        try:
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"GET failed [{self.source.name}] {url}: {e}")
            return None

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        resp = self.get(url)
        if resp:
            return BeautifulSoup(resp.text, "lxml")
        return None

    # ── RSS / Atom parsing ────────────────────────────────────────────────────────

    def parse_feed(self, feed_url: str) -> list[dict]:
        """Parse an RSS/Atom feed and return normalised article dicts."""
        articles = []
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                article = self._normalise_feed_entry(entry)
                if article:
                    articles.append(article)
        except Exception as e:
            logger.error(f"Feed parse error [{self.source.name}]: {e}")
        return articles

    def _normalise_feed_entry(self, entry) -> Optional[dict]:
        title = entry.get("title", "").strip()
        url   = entry.get("link", "").strip()
        if not title or not url:
            return None

        # Summary — prefer content over summary
        summary = ""
        if hasattr(entry, "content") and entry.content:
            summary = BeautifulSoup(entry.content[0].value, "lxml").get_text(" ", strip=True)
        elif hasattr(entry, "summary"):
            summary = BeautifulSoup(entry.summary, "lxml").get_text(" ", strip=True)

        # Published date
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import time
            ts = time.mktime(entry.published_parsed)
            published_at = datetime.fromtimestamp(ts, tz=timezone.get_current_timezone())

        # Image
        image_url = self._extract_feed_image(entry)

        return {
            "title":        title,
            "url":          url,
            "summary":      summary[:2000],
            "published_at": published_at,
            "image_url":    image_url,
            "authors":      self._extract_authors(entry),
        }

    def _extract_feed_image(self, entry) -> Optional[str]:
        # Try media:thumbnail
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        # Try media:content
        if hasattr(entry, "media_content") and entry.media_content:
            for mc in entry.media_content:
                if "image" in mc.get("medium", "") or mc.get("url", "").endswith(
                    (".jpg", ".jpeg", ".png", ".webp")
                ):
                    return mc.get("url")
        # Try enclosures
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href")
        return None

    def _extract_authors(self, entry) -> str:
        if hasattr(entry, "author"):
            return entry.author[:300]
        if hasattr(entry, "authors") and entry.authors:
            return ", ".join(a.get("name", "") for a in entry.authors)[:300]
        return ""

    # ── Classification ────────────────────────────────────────────────────────────

    def classify(self, title: str, summary: str) -> tuple[str, list[str], float]:
        """
        Returns (category, tags, relevance_score).
        """
        text  = (title + " " + summary).lower()
        found = {}
        tags  = set()

        for cat, keywords in CLINICAL_NUTRITION_KEYWORDS.items():
            hits = [kw for kw in keywords if kw.lower() in text]
            if hits:
                found[cat] = len(hits)
                tags.update(hits[:5])

        if not found:
            return "other", [], 0.0

        # Pick highest-scoring category, but prefer priority order on ties
        best_cat = max(found, key=lambda c: (found[c], -CATEGORY_PRIORITY.index(c)
                                              if c in CATEGORY_PRIORITY else -99))

        # Relevance: ratio of matched to total keywords
        total_checked = sum(len(kws) for kws in CLINICAL_NUTRITION_KEYWORDS.values())
        score = round(sum(found.values()) / total_checked, 4)

        return best_cat, list(tags)[:10], min(score * 10, 1.0)

    # ── Dedup hash ────────────────────────────────────────────────────────────────

    @staticmethod
    def url_hash(url: str) -> str:
        return hashlib.md5(url.strip().encode()).hexdigest()

    # ── Main entry point (override in subclasses) ─────────────────────────────────

    def fetch_articles(self) -> list[dict]:
        """
        Subclasses return a list of dicts with keys:
            title, url, summary, published_at, image_url, authors, journal (opt)
        """
        raise NotImplementedError

    def run(self) -> tuple[int, int]:
        """
        Run the crawler, save new articles, return (found, new).
        """
        from articles.models import Article
        from django.utils import timezone as tz

        found    = 0
        new_count = 0

        try:
            raw_articles = self.fetch_articles()
            found = len(raw_articles)

            for data in raw_articles:
                url = data.get("url", "").strip()
                if not url:
                    continue

                # Skip if already exists
                if Article.objects.filter(url=url).exists():
                    continue

                category, tags, score = self.classify(
                    data.get("title", ""),
                    data.get("summary", ""),
                )

                # Skip irrelevant articles (score 0 = no nutrition keywords at all)
                # unless source is fully nutrition-specific (skip filter)
                if score == 0.0 and not self.source.description.lower().__contains__("nutrition"):
                    pass  # still save, just mark low relevance

                Article.objects.create(
                    title          = data.get("title", "")[:500],
                    summary        = data.get("summary", "")[:3000],
                    url            = url,
                    source         = self.source,
                    category       = category,
                    region         = self.source.region,
                    tags           = tags,
                    image_url      = data.get("image_url"),
                    authors        = data.get("authors", "")[:500],
                    journal        = data.get("journal", "")[:300],
                    published_at   = data.get("published_at"),
                    relevance_score = score,
                )
                new_count += 1

            # Update source metadata
            self.source.last_crawled  = tz.now()
            self.source.article_count = Article.objects.filter(source=self.source).count()
            self.source.save(update_fields=["last_crawled", "article_count"])

        except Exception as e:
            logger.error(f"Crawler run error [{self.source.name}]: {e}", exc_info=True)

        logger.info(f"[{self.source.name}] found={found} new={new_count}")
        return found, new_count
