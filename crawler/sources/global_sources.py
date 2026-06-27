"""
Global Clinical Nutrition Sources
WHO, PubMed, ESPEN, Academy of Nutrition & Dietetics, Lancet, AJCN, etc.
"""

import logging
import re
from datetime import datetime, timezone as dt_tz
from typing import Optional

from bs4 import BeautifulSoup
from crawler.base import BaseCrawler

logger = logging.getLogger("crawler")


# ─── RSS-based crawlers (simple, reliable) ───────────────────────────────────────

class RSSCrawler(BaseCrawler):
    """Generic RSS crawler — works for any standard RSS/Atom feed."""

    def fetch_articles(self) -> list[dict]:
        feed_url = self.source.feed_url or self.source.url
        return self.parse_feed(feed_url)


class WHONutritionCrawler(BaseCrawler):
    """
    WHO Nutrition News — scrapes the WHO nutrition news page.
    https://www.who.int/news-room/news
    """

    def fetch_articles(self) -> list[dict]:
        # WHO has a news RSS feed filtered by nutrition tag
        return self.parse_feed(
            "https://www.who.int/feeds/entity/nutrition/news/rss.xml"
        )


class PubMedNutritionCrawler(BaseCrawler):
    """
    PubMed — searches for recent clinical nutrition articles via E-utilities.
    Query: clinical nutrition[MeSH] OR medical nutrition therapy[tiab]
    Free, no API key needed for basic access.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    QUERY    = (
        "(clinical nutrition[MeSH] OR medical nutrition therapy[tiab] "
        "OR malnutrition[MeSH] OR enteral nutrition[MeSH] "
        "OR parenteral nutrition[MeSH]) AND hasabstract"
    )

    def fetch_articles(self) -> list[dict]:
        articles = []

        # Step 1: esearch — get PMIDs
        search_url = (
            f"{self.BASE_URL}/esearch.fcgi"
            f"?db=pubmed&term={self.QUERY}"
            f"&retmax=30&sort=pub+date&retmode=json&datetype=pdat&reldate=30"
        )
        resp = self.get(search_url)
        if not resp:
            return articles

        try:
            ids = resp.json()["esearchresult"]["idlist"]
        except (KeyError, ValueError):
            return articles

        if not ids:
            return articles

        # Step 2: esummary — fetch metadata
        ids_str    = ",".join(ids)
        summary_url = (
            f"{self.BASE_URL}/esummary.fcgi"
            f"?db=pubmed&id={ids_str}&retmode=json"
        )
        resp2 = self.get(summary_url)
        if not resp2:
            return articles

        try:
            result = resp2.json()["result"]
        except (KeyError, ValueError):
            return articles

        for pmid in ids:
            item = result.get(pmid, {})
            if not item or "error" in item:
                continue

            title   = item.get("title", "").rstrip(".")
            pub_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            authors = ", ".join(
                a.get("name", "") for a in item.get("authors", [])[:3]
            )
            journal  = item.get("fulljournalname", item.get("source", ""))
            pub_date = self._parse_pubmed_date(item.get("pubdate", ""))

            articles.append({
                "title":        title,
                "url":          pub_url,
                "summary":      item.get("sorttitle", title),
                "published_at": pub_date,
                "authors":      authors,
                "journal":      journal,
                "image_url":    None,
            })

        return articles

    def _parse_pubmed_date(self, datestr: str) -> Optional[datetime]:
        """Parse PubMed date strings like '2024 Mar', '2024 Mar 15'."""
        formats = ["%Y %b %d", "%Y %b", "%Y"]
        now = datetime.now(dt_tz.utc)
        for fmt in formats:
            try:
                dt = datetime.strptime(datestr.strip(), fmt)
                dt = dt.replace(tzinfo=dt_tz.utc)
                return dt if dt <= now else None
            except ValueError:
                continue
        return None


class ESPENJournalCrawler(BaseCrawler):
    """
    ESPEN — Clinical Nutrition journal RSS feed.
    https://www.clinicalnutritionjournal.com
    """

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://rss.sciencedirect.com/publication/science/02615614"
        )


class JournalClinicalNutritionCrawler(RSSCrawler):
    """JPEN — Journal of Parenteral and Enteral Nutrition RSS."""
    pass  # Uses RSSCrawler with feed_url set on Source


class LancetNutritionCrawler(BaseCrawler):
    """The Lancet — nutrition-tagged articles."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.thelancet.com/action/showFeed"
            "?jc=lanpub&type=etoc&feed=rss"
        )


class AJCNCrawler(BaseCrawler):
    """American Journal of Clinical Nutrition RSS."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://academic.oup.com/rss/site_6122/advanceAccess_6122.xml"
        )


class EatRightCrawler(BaseCrawler):
    """
    Academy of Nutrition & Dietetics — EatRight.org news scraper.
    """

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.eatright.org/rss/news"
        )


class NutritionDayCrawler(RSSCrawler):
    """NutritionDay worldwide — annual survey insights."""
    pass


class BMJNutritionCrawler(BaseCrawler):
    """BMJ Nutrition, Prevention & Health."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://nutrition.bmj.com/rss/current.xml"
        )


class NutritionReviewsCrawler(BaseCrawler):
    """Nutrition Reviews (Oxford Academic)."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://academic.oup.com/rss/site_5127/advanceAccess_5127.xml"
        )


class NutrientsMDPICrawler(BaseCrawler):
    """Nutrients (MDPI) — open access nutrition journal."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.mdpi.com/rss/journal/nutrients"
        )


class UNICEFNutritionCrawler(BaseCrawler):
    """UNICEF Nutrition press releases and reports."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.unicef.org/press-releases/feed.xml"
        )


class WFPNewsCrawler(BaseCrawler):
    """World Food Programme news feed."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.wfp.org/rss.xml"
        )
