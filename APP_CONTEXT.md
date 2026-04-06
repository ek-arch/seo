# Kolo SEO & GEO Intelligence Agent — App Context

**URL:** https://kolo-seo.streamlit.app
**Repo:** `/Users/ek/SEO agent/` → github.com/ek-arch/seo
**Stack:** Streamlit (st.navigation), Python 3, Anthropic Claude API, Perplexity API, Google Sheets, Notion API, SerpAPI, Collaborator.pro API
**Deployed:** Streamlit Cloud
**Last updated:** April 6, 2026

---

## Architecture

Single-page Streamlit app (`app.py`, ~3800+ lines) with 12 pages via `st.navigation()`. All business data in `data_sources.py`. Modular helpers in separate files.

### Files

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~3800 | Main Streamlit app — all 12 pages, UI, charts, forms |
| `data_sources.py` | ~800 | Static market data from Hex BigQuery (countries, P&L, LTV, segments). Scoring functions for outlets. |
| `collaborator_outlets.py` | ~250 | Scraped Collaborator.pro outlet catalog. 5-dim scoring model (DR, search%, price/DR, category, traffic). Raw outlets for EN, RU, IT, ES, PL, PT, ID, RO. |
| `publication_roi.py` | ~300 | 4-layer ROI model: direct referral + SEO compound + GEO/AI citation + revenue. LTV by language & market-language combo. CTR by SERP position. |
| `llm_client.py` | ~400 | Anthropic Claude wrapper. Generates press releases (SEO+GEO optimized), revises, translates, recommends monthly plans, generates social comments. Anti-slop system prompts. |
| `geo_visibility.py` | ~200 | SerpAPI-powered GEO visibility tracker. 15 default queries (branded, generic, geo-targeted). Checks Kolo presence + competitor detection in SERPs. |
| `perplexity_geo.py` | ~490 | Perplexity API for AI citation visibility. 23 default GEO prompts. Geo-targeted prompt templates (EN/RU/IT/ES) for 15 markets. Market-level audit & summary. |
| `geo_prompt_research.py` | ~550 | Semrush-style AI prompt discovery & monitoring. Claude-powered prompt generation across 8 categories. Perplexity monitoring with brand/source counting. Opportunity finder. Result caching. |
| `programmatic_seo.py` | ~900 | Long-tail keyword matrix generation, 5-dimension quality scoring (intent, naturalness, scalability, market, SERP viability), autocomplete validation, SERP competition check. 30+ countries, RU patterns. |
| `seo_builder.py` | ~400 | Page clustering (1 page per country+language), Claude content generation (Haiku ~$0.002/page), HTML assembly with JSON-LD + hreflang + breadcrumbs, local export. |
| `seo_deploy.py` | ~180 | Cloudflare Workers KV deployment (prepared, not actively used — Webflow CMS preferred). |
| `keyword_research.py` | — | Keyword taxonomy, classification, multi-source discovery (autocomplete, Perplexity, SerpAPI). |
| `sheets_client.py` | ~200 | Google Sheets integration (gspread). Push comments, audit results, publications. Load/save content plan. |
| `notion_writer.py` | ~250 | Notion REST API writes. Creates content plan entries, PR draft pages, monthly plan pages, logs publication results. |
| `monthly_cycle.py` | ~250 | Monthly evaluation + planning cycle. Dataclasses for PublicationResult, MonthlyEvaluation, MonthlyPlan. Orchestrates eval → plan → Notion push. |
| `ahrefs_hook.py` | 70 | Ahrefs stub — defines interface (domain metrics, backlink profile, keyword rankings). Returns empty data. Ready for MCP connection. |
| `templates/base.html` | — | Responsive HTML template for programmatic SEO pages (nav, breadcrumbs, hero, content, FAQ accordion, CTA, related pages, footer). Kolo brand CSS. |
| `worker/kolo-proxy.js` | ~140 | Cloudflare Worker: `/crypto-card/*` (KV pages), `/sitemap.xml` (merged sitemap), `/hex/*`, `/collaborator/*` |
| `requirements.txt` | — | streamlit, pandas, altair, requests, anthropic, gspread, google-auth |

### Pages (st.navigation)

| Section | Page | Function | What it does |
|---------|------|----------|-------------|
| — | Dashboard | `page_dashboard` | Weekly action checklist, quick start guide |
| Stages | Kolo Metrics | `page_kolo_metrics` | Platform stats (pre/post cashback), P&L, country breakdown, revenue segments |
| Stages | Content Plan | `page_content_plan` | Content calendar with Notion + Google Sheets sync |
| Stages | Outlet Matching | `page_outlet_matching` | Live Collaborator.pro API search, 5-dim outlet scoring, price/DR analysis |
| Stages | Publication ROI | `page_publication_roi` | Per-publication ROI calculator (4-layer model), batch ROI across outlets |
| Actions | PR Generator | `page_pr_generator` | Claude-powered article generation, revision, translation (8 languages), track publications |
| Actions | Distribution | `page_content_distribution` | Reddit/Quora/Twitter comment drafting, post finder, comment tracker, Google Sheets sync |
| Actions | Monthly Eval | `page_monthly_eval` | Evaluate past month's publications (actual vs projected ROI), Ahrefs enrichment hook |
| Actions | Monthly Planner | `page_monthly_planner` | Claude-powered next-month plan generation, budget allocation, Notion push |
| Growth | Keyword Intel | `page_keyword_intel` | Keyword taxonomy, multi-source discovery (autocomplete, Perplexity, SerpAPI), geo audit, AI audit |
| Growth | Programmatic SEO | `page_programmatic_seo` | 4-tab pipeline: keyword matrix → autocomplete validation → SERP competition → page building (cluster → Claude content → HTML export) |
| Growth | GEO Tracker | `page_geo_tracker` | Semrush-style AI visibility monitor: discover prompts via Claude → monitor Kolo mentions in Perplexity answers → track competitors & sources → find opportunities |

### API Keys (sidebar, auto-loaded from Streamlit secrets)

| Key | Secret Name | Service | Purpose |
|-----|-------------|---------|---------|
| Hex API token | — | app.hex.tech | BigQuery data refresh |
| Collaborator.pro token | — | collaborator.pro | Live outlet catalog search |
| Notion token | `NOTION_TOKEN` | Notion API | Write content plans, PR drafts, monthly plans |
| Anthropic API key | `ANTHROPIC_API_KEY` | Claude API | Article generation, content generation, prompt discovery |
| SerpAPI key | `SERPAPI_KEY` | serpapi.com | GEO visibility audits, SERP competition (100 free/month) |
| Perplexity API key | `PERPLEXITY_KEY` | perplexity.ai | AI answer monitoring, GEO tracking (~$0.005/query) |
| Google Sheets creds | `gsheets` | gspread | Comment tracking, audit logs, publications |

### Key Data Constants

**Target Keywords** (from `geo_visibility.py` DEFAULT_QUERIES):
- Generic: "best crypto card 2026", "crypto debit card", "USDT Visa card", "spend crypto with Visa card", "best way to spend USDT"
- Geo: "crypto card Europe", "crypto card UK", "crypto card Italy", "carta crypto Italia 2026", "crypto card UAE", "crypto card digital nomad"
- Product: "Telegram crypto wallet card", "TRC20 USDT card", "crypto card low fees", "crypto card comparison 2026"

**GEO Prompt Categories** (from `geo_prompt_research.py`):
- Product Comparison, How-To, Geo-Specific, Use Case, Cost & Fees, Trust & Safety, Onboarding, B2B

**Competitors tracked:** Crypto.com, Coinbase, Binance, Wirex, Bybit, Nexo, Oobit, Revolut, Bitget, MetaMask, Gnosis Pay, Holyheld, Club Swan, RedotPay, Moon

**Languages supported:** EN, RU, IT, ES, PL, PT (Brazilian), ID, RO

**LTV by language:** RU $6,975 (highest), EN $3,502, ES $3,100, IT $2,850, PL $2,400, RO $2,200, PT $1,601, ID $900

**Top market-language combos:** ARE-ru $21,640/user, ISR-ru $53,000/user (hidden whale), KAZ-ru $8,597/user

### External Integrations

| Service | Status | ID/Config |
|---------|--------|-----------|
| Notion MCP | Connected | Workspace 42771b89-42ad-492f-9108-9d62c8c71869 |
| Hex.tech | Connected | Project 019bd11e-3c00-7004-a038-424c20e9281a |
| Collaborator.pro | Connected | Token-based API |
| Perplexity API | Connected | sonar model, ~$0.005/query |
| Ahrefs MCP | Stub only | UUID 098cb32a-ba21-4770-97dd-78bb54655419 |
| Google Sheets | Connected | Sheet 1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k |
| Cloudflare Worker | Deployed | kolo-proxy.ek-3ff.workers.dev (CORS proxy + programmatic SEO pages) |
| Streamlit Cloud | Deployed | Auto-loads secrets: ANTHROPIC_API_KEY, NOTION_TOKEN, SERPAPI_KEY, PERPLEXITY_KEY, gsheets |

### Scoring Models

**Keyword Quality Scoring (5-dim, 0-1.0)** (from `programmatic_seo.py`):
1. Intent (0-0.3) — search intent signals
2. Naturalness (0-0.15) — rejects robotic patterns
3. Scalability (0-0.15) — pattern template potential
4. Market existence (0-0.15) — Kolo operates in this market
5. SERP viability (0-0.25) — weak domains, forums in top results

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

## Programmatic SEO Pipeline

**Goal:** Auto-generate ~41 landing pages targeting long-tail keywords like "crypto card for freelancers in UAE".

**Pipeline:** Keyword matrix (1500+ combos) → Score & filter (5-dim) → Autocomplete validation (free) → SERP competition (SerpAPI) → Cluster to pages (1 per country+language) → Claude content generation (Haiku, ~$0.002/page) → HTML assembly (JSON-LD, hreflang, internal links) → Export (HTML files + manifest + sitemap)

**Deployment options:** Webflow CMS (preferred, needs Designer access) or Cloudflare Workers KV (prepared).

---

## GEO Tracker (Semrush-style)

**Goal:** Track whether Kolo appears in AI-generated answers when users ask about crypto cards.

**Pipeline:** Claude discovers realistic prompts (8 categories × 15 markets × 5 languages) → Perplexity monitors each prompt → Tracks Kolo mention, competitor brands, source count → Identifies opportunities (prompts where competitors appear but Kolo doesn't)

**Metrics:** Mentioned (0/1 or 1/1), Brands count, Sources count, Competitor leaderboard, Visibility by market/category

---

## ⛔ CRITICAL: Infrastructure Safety Rule
**BEFORE any destructive action (delete org, revoke key, disable service, change DNS, remove worker), MUST:**
1. List all features/services that depend on the component being changed
2. State explicitly what will break
3. Present risk to user and get confirmation
4. Prefer non-destructive alternatives (rename, create new, etc.)

**Incident log:** Anthropic Individual Org deleted on bad advice → API key invalidated → broke: content generation, prompt discovery, programmatic SEO builder, GEO Tracker Claude mode. Required support ticket + 7-day recovery window.

---

## Cloudflare Worker (kolo-proxy)

**Account:** 3ff8191356080bd0d901586d6098dcde
**URL:** kolo-proxy.ek-3ff.workers.dev
**Routes:**
- `/crypto-card/*` — serves programmatic SEO pages from KV
- `/sitemap.xml` — merged sitemap (Webflow + programmatic pages), correct `application/xml` content-type
- `/hex/run` — proxy to Hex API
- `/hex/thread` — proxy to Hex API
- `/collaborator/sites` — proxy to Collaborator.pro API
- All routes include CORS headers + OPTIONS handler
