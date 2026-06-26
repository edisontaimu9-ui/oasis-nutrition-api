"""
Crawler Registry
Maps Source.name → crawler class.
Also contains SEED_SOURCES — the initial set of sources to populate the DB.
"""

from crawler.sources.global_sources import (
    RSSCrawler,
    WHONutritionCrawler,
    PubMedNutritionCrawler,
    ESPENJournalCrawler,
    LancetNutritionCrawler,
    AJCNCrawler,
    EatRightCrawler,
    BMJNutritionCrawler,
    NutritionReviewsCrawler,
    NutrientsMDPICrawler,
    UNICEFNutritionCrawler,
    WFPNewsCrawler,
)
from crawler.sources.africa_sources import (
    WHOAFROCrawler,
    UNICEFESACrawler,
    MalawiMoHCrawler,
    AfricaNutritionSocietyCrawler,
    SAZACrawler,
    CORNAfricaCrawler,
    AJOLNutritionCrawler,
    GlobalNutritionReportCrawler,
    ACTAFricaCrawler,
)

# ─── Crawler class registry ───────────────────────────────────────────────────────
# Key = Source.name (must match exactly)

CRAWLER_REGISTRY: dict[str, type] = {
    # Global
    "WHO Nutrition":                    WHONutritionCrawler,
    "PubMed Clinical Nutrition":        PubMedNutritionCrawler,
    "ESPEN Clinical Nutrition Journal": ESPENJournalCrawler,
    "The Lancet":                       LancetNutritionCrawler,
    "AJCN":                             AJCNCrawler,
    "EatRight (AND)":                   EatRightCrawler,
    "BMJ Nutrition":                    BMJNutritionCrawler,
    "Nutrition Reviews":                NutritionReviewsCrawler,
    "Nutrients (MDPI)":                 NutrientsMDPICrawler,
    "UNICEF Nutrition":                 UNICEFNutritionCrawler,
    "WFP News":                         WFPNewsCrawler,
    # Africa
    "WHO AFRO":                         WHOAFROCrawler,
    "UNICEF ESA":                       UNICEFESACrawler,
    "Malawi MoH":                       MalawiMoHCrawler,
    "Africa Nutrition Society":         AfricaNutritionSocietyCrawler,
    "SAZA":                             SAZACrawler,
    "CORN Africa / AJOL":               CORNAfricaCrawler,
    "AJOL SAJCN":                       AJOLNutritionCrawler,
    "Global Nutrition Report":          GlobalNutritionReportCrawler,
    "Action Against Hunger":            ACTAFricaCrawler,
}

# ─── Seed data ────────────────────────────────────────────────────────────────────
# Run: python manage.py seed_sources

SEED_SOURCES = [
    # ── Global ──────────────────────────────────────────────────────────────────
    {
        "name":        "WHO Nutrition",
        "url":         "https://www.who.int/nutrition",
        "feed_url":    "https://www.who.int/feeds/entity/nutrition/news/rss.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "World Health Organization Nutrition news and guidelines",
        "logo_url":    "https://www.who.int/images/default-source/infographics/who-emblem.png",
    },
    {
        "name":        "PubMed Clinical Nutrition",
        "url":         "https://pubmed.ncbi.nlm.nih.gov",
        "region":      "global",
        "source_type": "api",
        "description": "PubMed NCBI — clinical nutrition, MNT, malnutrition research",
    },
    {
        "name":        "ESPEN Clinical Nutrition Journal",
        "url":         "https://www.clinicalnutritionjournal.com",
        "feed_url":    "https://rss.sciencedirect.com/publication/science/02615614",
        "region":      "global",
        "source_type": "rss",
        "description": "Official journal of the European Society for Clinical Nutrition and Metabolism",
    },
    {
        "name":        "The Lancet",
        "url":         "https://www.thelancet.com",
        "feed_url":    "https://www.thelancet.com/action/showFeed?jc=lanpub&type=etoc&feed=rss",
        "region":      "global",
        "source_type": "rss",
        "description": "The Lancet — nutrition, global health, clinical research",
    },
    {
        "name":        "AJCN",
        "url":         "https://academic.oup.com/ajcn",
        "feed_url":    "https://academic.oup.com/rss/site_6122/advanceAccess_6122.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "American Journal of Clinical Nutrition",
    },
    {
        "name":        "EatRight (AND)",
        "url":         "https://www.eatright.org",
        "feed_url":    "https://www.eatright.org/rss/news",
        "region":      "global",
        "source_type": "rss",
        "description": "Academy of Nutrition and Dietetics — professional practice news",
    },
    {
        "name":        "BMJ Nutrition",
        "url":         "https://nutrition.bmj.com",
        "feed_url":    "https://nutrition.bmj.com/rss/current.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "BMJ Nutrition, Prevention & Health",
    },
    {
        "name":        "Nutrition Reviews",
        "url":         "https://academic.oup.com/nutritionreviews",
        "feed_url":    "https://academic.oup.com/rss/site_5127/advanceAccess_5127.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "Nutrition Reviews — systematic reviews and meta-analyses",
    },
    {
        "name":        "Nutrients (MDPI)",
        "url":         "https://www.mdpi.com/journal/nutrients",
        "feed_url":    "https://www.mdpi.com/rss/journal/nutrients",
        "region":      "global",
        "source_type": "rss",
        "description": "MDPI Nutrients — open access, broad nutrition science",
    },
    {
        "name":        "UNICEF Nutrition",
        "url":         "https://www.unicef.org/nutrition",
        "feed_url":    "https://www.unicef.org/press-releases/feed.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "UNICEF nutrition press releases and situation reports",
    },
    {
        "name":        "WFP News",
        "url":         "https://www.wfp.org/news",
        "feed_url":    "https://www.wfp.org/rss.xml",
        "region":      "global",
        "source_type": "rss",
        "description": "World Food Programme — food security and nutrition",
    },
    # ── Africa ──────────────────────────────────────────────────────────────────
    {
        "name":        "WHO AFRO",
        "url":         "https://www.afro.who.int",
        "feed_url":    "https://www.afro.who.int/news/rss.xml",
        "region":      "africa",
        "source_type": "rss",
        "description": "WHO Regional Office for Africa — nutrition and public health",
    },
    {
        "name":        "UNICEF ESA",
        "url":         "https://www.unicef.org/esa",
        "feed_url":    "https://www.unicef.org/esa/press-releases/feed.xml",
        "region":      "africa",
        "source_type": "rss",
        "description": "UNICEF Eastern and Southern Africa — child nutrition",
    },
    {
        "name":        "Africa Nutrition Society",
        "url":         "https://www.africanutritionsociety.org",
        "region":      "africa",
        "source_type": "scrape",
        "description": "Africa Nutrition Society — continental nutrition community",
    },
    {
        "name":        "SAZA",
        "url":         "https://www.saza.org.za",
        "region":      "africa",
        "source_type": "scrape",
        "description": "Southern African Nutrition Association",
    },
    {
        "name":        "AJOL SAJCN",
        "url":         "https://www.ajol.info/index.php/sajcn",
        "feed_url":    "https://www.ajol.info/index.php/sajcn/gateway/plugin/WebFeedGatewayPlugin/rss2",
        "region":      "africa",
        "source_type": "rss",
        "description": "South African Journal of Clinical Nutrition (AJOL)",
    },
    {
        "name":        "Global Nutrition Report",
        "url":         "https://globalnutritionreport.org",
        "region":      "global",
        "source_type": "scrape",
        "description": "Annual global nutrition accountability report",
    },
    {
        "name":        "Action Against Hunger",
        "url":         "https://www.actionagainsthunger.org",
        "feed_url":    "https://www.actionagainsthunger.org/feed/",
        "region":      "africa",
        "source_type": "rss",
        "description": "Action Against Hunger — humanitarian nutrition response in Africa",
    },
    # ── Malawi ──────────────────────────────────────────────────────────────────
    {
        "name":        "Malawi MoH",
        "url":         "https://www.health.gov.mw",
        "region":      "malawi",
        "source_type": "scrape",
        "description": "Malawi Ministry of Health — national nutrition policies and news",
    },
]


def get_crawler_for_source(source) -> object | None:
    """Return an instantiated crawler for a given Source, or None if unknown."""
    cls = CRAWLER_REGISTRY.get(source.name)
    if cls:
        return cls(source)
    # Fallback: if source has a feed_url, use generic RSSCrawler
    if source.feed_url:
        return RSSCrawler(source)
    return None
