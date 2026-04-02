# Kolo SEO & GEO Intelligence Agent — App Context

**URL:** https://kolo-seo.streamlit.app
**Repo:** `/Users/ek/SEO agent/`
**Stack:** Streamlit (st.navigation), Python 3, Anthropic Claude API, Google Sheets, Notion API, SerpAPI, Collaborator.pro API
**Deployed:** Streamlit Cloud

---

## Architecture

Single-page Streamlit app (`app.py`, ~2631 lines) with 11 pages via `st.navigation()`. All business data in `data_sources.py`. Modular helpers in separate files.

### Files

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | 2631 | Main Streamlit app — all 11 pages, UI, charts, forms |
| `data_sources.py` | ~800 | Static market data from Hex BigQuery (countries, P&L, LTV, segments). Scoring functions for outlets. |
| `collaborator_outlets.py` | ~250 | Scraped Collaborator.pro outlet catalog. 5-dim scoring model (DR, search%, price/DR, category, traffic). Raw outlets for EN, RU, IT, ES, PL, PT, ID, RO. |
| `publication_roi.py` | ~300 | 4-layer ROI model: direct referral + SEO compound + GEO/AI citation + revenue. LTV by language & market-language combo. CTR by SERP position. |
| `llm_client.py` | ~400 | Anthropic Claude wrapper. Generates press releases (SEO+GEO optimized), revises, translates, recommends monthly plans, generates social comments. Anti-slop system prompts. |
| `geo_visibility.py` | ~200 | SerpAPI-powered GEO visibility tracker. 15 default queries (branded, generic, geo-targeted). Checks Kolo presence + competitor detection in SERPs. |
| `sheets_client.py` | ~200 | Google Sheets integration (gspread). Push comments, audit results, publications. Load/save content plan. Sheet ID: `1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k`. |
| `notion_writer.py` | ~250 | Notion REST API writes. Creates content plan entries, PR draft pages, monthly plan pages, logs publication results. |
| `monthly_cycle.py` | ~250 | Monthly evaluation + planning cycle. Dataclasses for PublicationResult, MonthlyEvaluation, MonthlyPlan. Orchestrates eval → plan → Notion push. |
| `ahrefs_hook.py` | 70 | Ahrefs stub — defines interface (domain metrics, backlink profile, keyword rankings). Returns empty data. Ready for MCP connection. |
| `requirements.txt` | 7 | streamlit, pandas, altair, requests, anthropic, gspread, google-auth |

### Pages (st.navigation)

| # | Page | Function | What it does |
|---|------|----------|-------------|
| 0 | Dashboard | `page_dashboard` | Weekly action checklist, quick start guide |
| 1 | Market Intel | `page_market_intel` | Competitor map by market, language LTV analysis, market priorities |
| 2 | Kolo Metrics | `page_kolo_metrics` | Platform stats (pre/post cashback), P&L, country breakdown, revenue segments |
| 3 | Content Plan | `page_content_plan` | Content calendar with Notion + Google Sheets sync |
| 4 | Outlet Matching | `page_outlet_matching` | Live Collaborator.pro API search, 5-dim outlet scoring, price/DR analysis |
| 5 | Publication ROI | `page_publication_roi` | Per-publication ROI calculator (4-layer model), batch ROI across outlets |
| 6 | PR Generator | `page_pr_generator` | Claude-powered article generation, revision, translation (8 languages), track publications |
| 7 | Distribution | `page_content_distribution` | Reddit/Quora/Twitter comment drafting, post finder, comment tracker, Google Sheets sync |
| 8 | GEO Visibility | `page_geo_visibility` | SerpAPI audit of 15 queries, Kolo SERP presence, competitor tracking, AI citation detection |
| 9 | Monthly Eval | `page_monthly_eval` | Evaluate past month's publications (actual vs projected ROI), Ahrefs enrichment hook |
| 10 | Monthly Planner | `page_monthly_planner` | Claude-powered next-month plan generation, budget allocation, Notion push |

### API Keys (sidebar)

| Key | Service | Purpose |
|-----|---------|---------|
| Hex API token | app.hex.tech | BigQuery data refresh |
| Collaborator.pro token | collaborator.pro | Live outlet catalog search |
| Notion token | Notion API | Write content plans, PR drafts, monthly plans |
| Anthropic API key | Claude API | Article generation, translation, planning |
| SerpAPI key | serpapi.com | GEO visibility audits (100 free/month) |
| Google Sheets creds | gspread | Comment tracking, audit logs, publications |

### Key Data Constants

**Target Keywords** (from `geo_visibility.py` DEFAULT_QUERIES):
- Generic: "best crypto card 2026", "crypto debit card", "USDT Visa card", "spend crypto with Visa card", "best way to spend USDT"
- Geo: "crypto card Europe", "crypto card UK", "crypto card Italy", "carta crypto Italia 2026", "crypto card UAE", "crypto card digital nomad"
- Product: "Telegram crypto wallet card", "TRC20 USDT card", "crypto card low fees", "crypto card comparison 2026"

**Competitors tracked:** Crypto.com, Coinbase, Binance, Wirex, Bybit, Nexo, Oobit, Revolut, Bitget, MetaMask, Gnosis Pay

**Languages supported:** EN, RU, IT, ES, PL, PT (Brazilian), ID, RO

**LTV by language:** RU $6,975 (highest), EN $3,502, ES $3,100, IT $2,850, PL $2,400, RO $2,200, PT $1,601, ID $900

**Top market-language combos:** ARE-ru $21,640/user, ISR-ru $53,000/user (hidden whale), KAZ-ru $8,597/user

### External Integrations

| Service | Status | ID/Config |
|---------|--------|-----------|
| Notion MCP | Connected | Workspace 42771b89-42ad-492f-9108-9d62c8c71869 |
| Hex.tech | Connected | Project 019bd11e-3c00-7004-a038-424c20e9281a |
| Collaborator.pro | Connected | Token-based API |
| Ahrefs MCP | Stub only | UUID 098cb32a-ba21-4770-97dd-78bb54655419 |
| Google Sheets | Connected | Sheet 1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k |
| Cloudflare Worker | Deployed | kolo-proxy.ek-3ff.workers.dev (CORS proxy for Hex/Collaborator APIs) |
| Streamlit Cloud | Deployed | Secrets: SerpAPI key + gsheets service account |

### Scoring Models

**Outlet Scoring (5-dim, 0-15 for catalog; 6-dim, 0-18 for march_outlets):**
1. Search traffic % (organic vs paid)
2. Domain Rating (DR)
3. Price/DR efficiency
4. Category fit (crypto/finance)
5. Monthly traffic volume
6. (March only) GEO AI citability

**Publication ROI (4-layer):**
1. Direct referral traffic (UTM-trackable)
2. SEO compound traffic (backlink → ranking improvement, 90-day window)
3. GEO/AI citation traffic (AI engines citing outlet)
4. Revenue = total visits x conversion rate x LTV

---

## Cloudflare Worker (kolo-proxy)

**Account:** 3ff8191356080bd0d901586d6098dcde
**URL:** kolo-proxy.ek-3ff.workers.dev
**Routes:**
- `/sitemap.xml` — proxies kolo.xyz sitemap with correct `application/xml` content-type (Webflow serves `application/rss+xml`)
- `/hex/run` — proxy to Hex API
- `/hex/thread` — proxy to Hex API
- `/collaborator/sites` — proxy to Collaborator.pro API
- All routes include CORS headers + OPTIONS handler
