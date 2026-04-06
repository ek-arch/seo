# Next Session Brief — April 6, 2026

## What Was Done Recently

### April 6 — GEO Tracker (Semrush-style AI Visibility Monitor)
- Built `geo_prompt_research.py` — AI prompt discovery engine using Claude + Perplexity monitoring
- Added **GEO Tracker** page to app (Growth → GEO Tracker) with 4 tabs:
  - Tab 1: Discover Prompts — Claude generates realistic AI prompts across 8 categories × 15 markets × 5 languages
  - Tab 2: Monitor — queries Perplexity for each prompt, checks Kolo mention/citation
  - Tab 3: Results — Semrush-style table (Mentioned, Brands, Sources), competitor leaderboard, visibility by market, opportunity finder
  - Tab 4: History — cached scans for comparison over time
- Auto-loads Perplexity API key from Streamlit secrets (`PERPLEXITY_KEY`)

### April 2–5 — Programmatic SEO Infrastructure
- Built full pipeline: `programmatic_seo.py` (keyword matrix + 5-dim scoring) + `seo_builder.py` (clustering + Claude content + HTML assembly)
- 1500+ keyword combos → score/filter → ~41 pages (1 per country+language)
- Added **Programmatic SEO** page to app (Growth → Programmatic SEO) with 4 tabs
- HTML template with JSON-LD, hreflang, internal links, FAQ accordion
- Cloudflare Worker updated for `/crypto-card/*` route serving from KV

### April 2 — Webflow SEO Changes
- Published 7 optimized titles & descriptions via Webflow Editor
- Deployed sitemap fix via Cloudflare Worker
- Created Notion audit page and Webflow Designer brief

---

## What Needs to Be Done Next

### Priority 1: Run GEO Tracker
- Add `PERPLEXITY_KEY` to Streamlit Cloud secrets
- Run first AI visibility scan: discover prompts → monitor → identify gaps
- Baseline: which competitors dominate AI answers for crypto card queries?

### Priority 2: Run Programmatic SEO Pipeline
- Generate all ~41 pages via Tab 4 (Build Pages) in Streamlit app
- Requires working Anthropic API key (pending account restoration)
- Get Webflow Designer access for deployment

### Priority 3: Webflow Designer (needs Designer access, not Editor)
Full brief in `/Users/ek/SEO agent/webflow-designer-seo-fixes.md`. Summary:

1. **Fix hreflang tags** — ALL pages point hreflang to EN URL instead of locale URLs
2. **Fix canonicals on /ru/ and /ua/ pages** — causes 82 "duplicate without canonical" in GSC
3. **Translate RU/UA titles & descriptions** — most /ru/ and /ua/ pages show English titles
4. **Add JSON-LD structured data** — FinancialProduct schema in site-wide head code
5. **Fix mobile Core Web Vitals** — 9 poor mobile URLs, 0 good

### Priority 4: Content & Distribution
- Generate and publish April PR articles via the SEO agent app
- Target markets: ARE (ru), GBR (en), ITA (it), ESP (ru — not en!), POL (pl)
- New CIS markets now supported: UZB, KGZ, ARM, AZE — consider RU content

### Priority 5: App Improvements
- Ahrefs MCP integration (`ahrefs_hook.py` is stubbed)
- Add GSC API integration for automated indexing requests

### Pending
- Anthropic account: "elena's Individual Org" deletion requested to be cancelled (emailed support@anthropic.com April 6). Must be restored before Apr 13.

---

## Key Reminders
- **kolo.in redirects to kolo.xyz** — same site, two domains
- **NOT "in Telegram"** — Kolo is multi-platform (iOS, Android, Telegram, web)
- **RU speakers = 2x LTV** ($6,975 vs $3,502 EN) — always prioritize RU content
- **ARE-ru = $21,640/user** — Dubai Russian expats are #1 ROI target
- **ESP should target RU speakers** ($7,302/user) not EN ($4,233/user)
- **B2B = 41% of spend**, growing 7x faster than B2C
- **Cannot issue cards:** RUS, BLR, VEN, CUB, IRN, SYR, PRK, UKR, TUR, ISR, CHN, IND, VNM, NPL, IRQ, KAZ
- **US is NOT supported**
- Webflow Editor login: via knock.app link (ask user)
- GSC property: `sc-domain:kolo.xyz`
