# Oasis Nutrition News API

Clinical nutrition news & updates crawler with REST API endpoints, built for Oasis CNST.  
**Stack:** Python · Django · Django REST Framework · APScheduler · SQLite · BeautifulSoup4 · feedparser

---

## Quick Start 

```bash
# Clone / copy project into Termux
cd ~/storage/shared   # or anywhere in Termux

bash setup_termux.sh  # one-time setup

# Start server
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

API root: `http://localhost:8000/`

---

## API Endpoints

### Articles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/articles/` | List articles (paginated, filtered) |
| GET | `/api/v1/articles/{id}/` | Article detail |
| GET | `/api/v1/articles/latest/` | 10 most recent articles |
| GET | `/api/v1/articles/featured/` | Featured articles |
| GET | `/api/v1/articles/malawi/` | Malawi-region articles |
| GET | `/api/v1/articles/africa/` | Africa + Malawi articles |
| GET | `/api/v1/articles/categories/` | Article counts by category |
| GET | `/api/v1/articles/stats/` | Dashboard stats snapshot |

### Sources

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sources/` | List all active sources |
| GET | `/api/v1/sources/{id}/` | Source detail |
| GET | `/api/v1/sources/regions/` | Source counts by region |

### Crawler Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crawl/trigger/` | Trigger crawl (async) |
| GET | `/api/v1/crawl/status/` | Scheduler & crawl status |
| GET | `/api/v1/crawl/logs/` | Recent crawl logs |

---

## Filtering & Search

```
# Filter by category
GET /api/v1/articles/?category=clinical_nutrition

# Filter by region
GET /api/v1/articles/?region=malawi
GET /api/v1/articles/?region=africa

# Full-text search
GET /api/v1/articles/?search=malnutrition+RUTF

# Filter by source
GET /api/v1/articles/?source=2

# By tag
GET /api/v1/articles/?tag=enteral+nutrition

# Date range
GET /api/v1/articles/?published_after=2024-01-01&published_before=2024-12-31

# Min relevance score (0–1)
GET /api/v1/articles/?min_relevance=0.3

# Combine filters
GET /api/v1/articles/?category=pediatric&region=africa&search=MUAC

# Ordering
GET /api/v1/articles/?ordering=-relevance_score
GET /api/v1/articles/?ordering=-published_at

# Pagination
GET /api/v1/articles/?page=2&page_size=10
```

### Available Categories

| Value | Label |
|-------|-------|
| `clinical_nutrition` | Clinical Nutrition |
| `dietetics` | Dietetics Practice |
| `research` | Research & Evidence |
| `public_health` | Public Health Nutrition |
| `pediatric` | Pediatric Nutrition |
| `malnutrition` | Malnutrition & Wasting |
| `food_security` | Food Security |
| `policy` | Policy & Guidelines |
| `education` | Nutrition Education |

### Regions

| Value | Description |
|-------|-------------|
| `global` | Global sources (WHO, PubMed, Lancet, etc.) |
| `africa` | Africa-wide sources (WHO AFRO, ANS, SAZA, etc.) |
| `malawi` | Malawi-specific (MoH Malawi) |

---

## Crawl Trigger API

```json
// POST /api/v1/crawl/trigger/

// Crawl all sources
{}

// Crawl a specific source
{ "source_id": 3 }
```

Response:
```json
{
  "status": "triggered",
  "message": "Full crawl started for all active sources",
  "async": true
}
```

---

## Sources Bundled

### Global (11 sources)
- WHO Nutrition
- PubMed Clinical Nutrition (E-utilities API, no key needed)
- ESPEN Clinical Nutrition Journal
- The Lancet
- AJCN (American Journal of Clinical Nutrition)
- EatRight / AND
- BMJ Nutrition
- Nutrition Reviews
- Nutrients (MDPI)
- UNICEF Nutrition
- WFP News

### Africa (7 sources)
- WHO AFRO
- UNICEF Eastern & Southern Africa
- Africa Nutrition Society
- SAZA (Southern African Nutrition Association)
- AJOL SAJCN (South African Journal of Clinical Nutrition)
- Action Against Hunger
- Global Nutrition Report

### Malawi (1 source)
- Malawi Ministry of Health

---

## Integrating with Oasis CNST (vanilla JS)

```javascript
// oasis-nutrition-news.js

const NEWS_API = 'http://localhost:8000/api/v1';

async function fetchLatestNews({ category, region, search, page = 1 } = {}) {
  const params = new URLSearchParams({ page });
  if (category) params.set('category', category);
  if (region)   params.set('region', region);
  if (search)   params.set('search', search);

  const resp = await fetch(`${NEWS_API}/articles/?${params}`);
  if (!resp.ok) throw new Error('News API error');
  return resp.json();  // { count, next, previous, results: [...] }
}

async function fetchMalawiNews() {
  const resp = await fetch(`${NEWS_API}/articles/malawi/`);
  return resp.json();
}

async function fetchStats() {
  const resp = await fetch(`${NEWS_API}/articles/stats/`);
  return resp.json();
}

// Trigger a crawl from Oasis admin
async function triggerCrawl(sourceId = null) {
  const body = sourceId ? { source_id: sourceId } : {};
  const resp = await fetch(`${NEWS_API}/crawl/trigger/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return resp.json();
}
```

---

## Management Commands

```bash
# Seed sources into DB
python manage.py seed_sources

# Crawl all sources now
python manage.py crawl_now

# Crawl one source
python manage.py crawl_now --source-id 1

# List sources with IDs
python manage.py crawl_now --list

# Django admin
python manage.py createsuperuser
# → http://localhost:8000/admin/
```

---

## Project Structure

```
oasis_nutrition_api/
├── manage.py
├── requirements.txt
├── setup_termux.sh
├── .env.example
├── oasis_nutrition_api/        # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── articles/                   # Models, API views, serializers
│   ├── models.py               # Source, Article, CrawlLog
│   ├── serializers.py
│   ├── views.py                # ArticleViewSet, SourceViewSet
│   ├── urls.py
│   └── admin.py
├── crawler/                    # Crawling engine
│   ├── base.py                 # BaseCrawler + keyword classifier
│   ├── registry.py             # Source → class mapping + SEED_SOURCES
│   ├── scheduler.py            # APScheduler background jobs
│   ├── views.py                # Crawl trigger / status / logs
│   ├── urls.py
│   ├── apps.py                 # Auto-starts scheduler
│   └── sources/
│       ├── global_sources.py   # 11 global crawlers
│       └── africa_sources.py   # 8 Africa/Malawi crawlers
└── logs/
    └── oasis_crawler.log
```

---

## Deployment Options

### Termux (development / local)
```bash
python manage.py runserver 0.0.0.0:8000
```
Access from Oasis CNST PWA via `http://localhost:8000/api/v1/`

### Render / Railway (production)
Set `DEBUG=False`, `ALLOWED_HOSTS=your-domain.com`, switch to PostgreSQL if desired.  
`gunicorn oasis_nutrition_api.wsgi:application --bind 0.0.0.0:$PORT`

### Cloudflare Tunnel (expose Termux to internet)
```bash
pkg install cloudflared
cloudflared tunnel --url http://localhost:8000
```
