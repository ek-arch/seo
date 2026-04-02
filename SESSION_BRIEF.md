# Next Session Brief — April 2, 2026

## What Was Done This Session

### Webflow Editor — Published 7 SEO Changes
All titles & descriptions optimized with target keywords from the SEO agent app and published live:

| Page | New Title |
|------|-----------|
| Home | Kolo — Crypto Visa Card & USDT Wallet \| Spend in 60+ Countries |
| Exchanger | Crypto Exchange — Buy & Sell USDT, BTC, ETH Instantly \| Kolo |
| Buy Crypto | Buy Crypto with Card — USDT, BTC, ETH \| Kolo |
| Countries | Crypto Card in 60+ Countries — Europe, UK, UAE & More \| Kolo |
| Blog | Crypto Card Blog — News, Guides & Tips \| Kolo |
| Cryptowallet | Crypto Wallet — USDT, BTC, ETH Multi-Currency \| Kolo |
| Business | Crypto for Business — B2B Payments & Corporate Visa Cards \| Kolo |

### Cloudflare Worker Fix
Deployed updated `kolo-proxy` worker with `/sitemap.xml` route that proxies kolo.xyz sitemap with correct `application/xml` content-type (Webflow bug: serves as `application/rss+xml`).

### Notion Audit Page
Created "kolo.xyz SEO/GEO Audit — April 2026" page (ID: `335255c3-552c-81c9-abeb-fd00e1f177dd`) under SEO Agent Hub with full findings.

### Webflow Designer Brief
Created `webflow-designer-seo-fixes.md` — complete task list for Designer access work.

---

## What Needs to Be Done Next

### Priority 1: Webflow Designer (needs Designer access, not Editor)
Full brief in `/Users/ek/SEO agent/webflow-designer-seo-fixes.md`. Summary:

1. **Fix hreflang tags** — ALL pages point hreflang to EN URL instead of locale URLs. Add correct `<link rel="alternate">` for en/ru/uk/x-default on all 8 pages x 3 locales.
2. **Fix canonicals on /ru/ and /ua/ pages** — All locale pages canonical to English URL. Must self-reference. This causes 82 "duplicate without canonical" pages in GSC.
3. **Translate RU/UA titles & descriptions** — Only /exchanger and /cryptowallet have translations. All other /ru/ and /ua/ pages show English titles. Full copy provided in the brief.
4. **Add JSON-LD structured data** — FinancialProduct schema in site-wide head code.
5. **Fix mobile Core Web Vitals** — 9 poor mobile URLs, 0 good. Desktop is fine (9 good).

### Priority 2: GSC Follow-up
- Request indexing for the 7 updated pages (new titles/descriptions are live)
- Monitor sitemap status (was "Couldn't fetch" — likely CDN cache, should resolve)
- Check if 82 duplicate pages decrease after hreflang/canonical fix

### Priority 3: Content & Distribution
- Generate and publish April PR articles via the SEO agent app
- Target markets: ARE (ru), GBR (en), ITA (it), ESP (ru — not en!), POL (pl)
- New CIS markets now supported: UZB, KGZ, ARM, AZE — consider RU content
- Use app's Publication ROI calculator to prioritize outlets

### Priority 4: App Improvements
- Ahrefs MCP integration (`ahrefs_hook.py` is stubbed, ready for implementation)
- Add GSC API integration for automated indexing requests
- Content plan sync with Notion needs testing

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
