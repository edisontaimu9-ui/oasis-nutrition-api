"""
Africa & Malawi Clinical Nutrition Sources
WHO AFRO, Africa Nutrition Society, KEMRI, MoH Malawi, SAZA, CORN, etc.
"""

import logging
from datetime import datetime, timezone as dt_tz
from typing import Optional

from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger("crawler")


class WHOAFROCrawler(BaseCrawler):
    """
    WHO Regional Office for Africa — nutrition news.
    """

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.afro.who.int/news/rss.xml"
        )


class UNICEFESACrawler(BaseCrawler):
    """UNICEF Eastern and Southern Africa — nutrition updates."""

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.unicef.org/esa/press-releases/feed.xml"
        )


class MalawiMoHCrawler(BaseCrawler):
    """
    Malawi Ministry of Health — scrapes news/publications page.
    https://www.health.gov.mw
    """

    def fetch_articles(self) -> list[dict]:
        articles = []
        soup = self.get_soup("https://www.health.gov.mw/index.php/news")
        if not soup:
            return articles

        # MoH Malawi news listing — adapt selectors if site changes
        for item in soup.select("div.news-item, article.news, .blog-post")[:20]:
            title_el = item.select_one("h2, h3, .title, a")
            link_el  = item.select_one("a[href]")
            desc_el  = item.select_one("p, .description, .intro")

            if not title_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            href  = link_el["href"]
            url   = href if href.startswith("http") else f"https://www.health.gov.mw{href}"
            summary = desc_el.get_text(strip=True) if desc_el else ""

            articles.append({
                "title":        title,
                "url":          url,
                "summary":      summary[:1000],
                "published_at": None,
                "image_url":    None,
                "authors":      "Ministry of Health, Malawi",
            })

        return articles


class AfricaNutritionSocietyCrawler(BaseCrawler):
    """
    Africa Nutrition Society — news & events scraper.
    https://www.africanutritionsociety.org
    """

    def fetch_articles(self) -> list[dict]:
        articles = []
        soup = self.get_soup("https://www.africanutritionsociety.org/news/")
        if not soup:
            return articles

        for item in soup.select("article, .post, .news-card")[:15]:
            title_el = item.select_one("h2, h3, .entry-title")
            link_el  = item.select_one("a[href]")
            desc_el  = item.select_one("p, .entry-summary")
            date_el  = item.select_one("time, .entry-date, .date")

            if not title_el or not link_el:
                continue

            title    = title_el.get_text(strip=True)
            href     = link_el["href"]
            url      = href if href.startswith("http") else f"https://www.africanutritionsociety.org{href}"
            summary  = desc_el.get_text(strip=True) if desc_el else ""
            pub_date = self._parse_date_element(date_el)

            articles.append({
                "title":        title,
                "url":          url,
                "summary":      summary[:1000],
                "published_at": pub_date,
                "image_url":    None,
                "authors":      "Africa Nutrition Society",
            })

        return articles

    def _parse_date_element(self, el) -> Optional[datetime]:
        if not el:
            return None
        dt_str = el.get("datetime", el.get_text(strip=True))
        for fmt in ["%Y-%m-%d", "%B %d, %Y", "%d %B %Y"]:
            try:
                return datetime.strptime(dt_str[:20], fmt).replace(tzinfo=dt_tz.utc)
            except ValueError:
                continue
        return None


class SAZACrawler(BaseCrawler):
    """
    Southern African Nutrition Association (SAZA) — news scraper.
    """

    def fetch_articles(self) -> list[dict]:
        articles = []
        resp = self.get("https://www.saza.org.za/news/")
        if not resp:
            return articles

        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select("article, .post, .entry")[:15]:
            title_el = item.select_one("h2, h3, .entry-title, a")
            link_el  = item.select_one("a[href]")
            desc_el  = item.select_one("p, .entry-summary, .excerpt")
            date_el  = item.select_one("time")

            if not title_el or not link_el:
                continue

            title   = title_el.get_text(strip=True)
            href    = link_el["href"]
            url     = href if href.startswith("http") else f"https://www.saza.org.za{href}"
            summary = desc_el.get_text(strip=True) if desc_el else ""

            pub_date = None
            if date_el and date_el.get("datetime"):
                try:
                    pub_date = datetime.fromisoformat(
                        date_el["datetime"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            articles.append({
                "title":        title,
                "url":          url,
                "summary":      summary[:1000],
                "published_at": pub_date,
                "image_url":    None,
                "authors":      "SAZA",
            })

        return articles


class CORNAfricaCrawler(BaseCrawler):
    """
    Consortium of Research into Nutritional Status (CORN) / African journals
    via RSS from African Journals Online (AJOL).
    """

    FEEDS = [
        "https://www.ajol.info/index.php/ajfand/gateway/plugin/WebFeedGatewayPlugin/rss2",
        "https://www.ajol.info/index.php/sajcn/gateway/plugin/WebFeedGatewayPlugin/rss2",
    ]

    def fetch_articles(self) -> list[dict]:
        articles = []
        for feed_url in self.FEEDS:
            articles.extend(self.parse_feed(feed_url))
        return articles


class AJOLNutritionCrawler(BaseCrawler):
    """
    African Journals Online — South African Journal of Clinical Nutrition RSS.
    """

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.ajol.info/index.php/sajcn/gateway/plugin/"
            "WebFeedGatewayPlugin/rss2"
        )


class GlobalNutritionReportCrawler(BaseCrawler):
    """Global Nutrition Report — annual insights and country data."""

    def fetch_articles(self) -> list[dict]:
        articles = []
        soup = self.get_soup("https://globalnutritionreport.org/news/")
        if not soup:
            return articles

        for item in soup.select("article, .card, .news-item")[:10]:
            title_el = item.select_one("h2, h3, .card-title")
            link_el  = item.select_one("a[href]")
            desc_el  = item.select_one("p, .card-text, .excerpt")

            if not title_el or not link_el:
                continue

            title   = title_el.get_text(strip=True)
            href    = link_el["href"]
            url     = href if href.startswith("http") else f"https://globalnutritionreport.org{href}"
            summary = desc_el.get_text(strip=True) if desc_el else ""

            articles.append({
                "title":        title,
                "url":          url,
                "summary":      summary[:1000],
                "published_at": None,
                "image_url":    None,
                "authors":      "Global Nutrition Report",
            })

        return articles


class ACTAFricaCrawler(BaseCrawler):
    """
    Action Against Hunger Africa — nutrition emergency updates.
    """

    def fetch_articles(self) -> list[dict]:
        return self.parse_feed(
            "https://www.actionagainsthunger.org/feed/"
        )
