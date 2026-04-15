# Kolo Website Visibility Report
## SEO/GEO Technical Fixes — April 7, 2026

---

## Executive Summary

Comprehensive technical SEO audit and fixes for kolo.xyz (redirects from kolo.in). Work covered Webflow on-site SEO, Google Search Console submissions, Cloudflare investigation, and LLMs.txt for GEO (Generative Engine Optimization).

---

## 1. Issues Found & Fixed

### 1.1 Hreflang Tags — FIXED in Webflow Designer
**Problem:** All hreflang tags on every locale page pointed to the English URL instead of their own locale. This caused Google to see 82+ duplicate pages and misattribute locale content.

**Fix applied:** Correct self-referencing hreflang tags added to all 8 pages x 3 locales (en, ru, uk + x-default) via Webflow Designer Custom Code > Head Code.

**Verified live:** Yes — WebFetch confirmed correct hreflang on production.

### 1.2 Canonical Tags — FIXED in Webflow Designer
**Problem:** Missing or incorrect self-referencing canonical tags. Each locale page needs to declare itself as canonical to avoid duplicate content signals.

**Fix applied:** Self-referencing canonicals set per locale in Webflow page SEO settings.

**Additional fix:** Old Home page and Test Page canonicals set to `https://kolo.xyz` via Webflow Editor to redirect any residual SEO value to homepage.

**Verified live:** Yes.

### 1.3 JSON-LD Structured Data — VERIFIED
**Status:** Already present on production pages. Organization schema with correct branding info confirmed via WebFetch.

### 1.4 LLMs.txt — CREATED & DEPLOYED
**Problem:** No LLMs.txt file existed. AI engines (ChatGPT, Perplexity, Claude) had no structured product description to reference, hurting GEO visibility.

**Fix applied:** Created comprehensive `/llms.txt` file containing:
- Key facts (product, platforms, 40+ country coverage, cashback, 160+ assets, FX rates, B2B)
- 5 use cases
- Comparison table (Kolo vs Crypto.com vs Binance Card vs Revolut)
- Full page list with URLs

**Deployed:** Uploaded to Webflow Dashboard (custom file hosting). Live at `https://kolo.xyz/llms.txt`.

**Verified live:** Yes — WebFetch confirmed accessible and correct content.

### 1.5 Sitemap — RESUBMITTED (issue persists)
**Problem:** Google Search Console shows "Couldn't fetch" for `https://kolo.xyz/sitemap.xml`. Status: Unknown, 0 discovered pages.

**Root cause identified:** Webflow serves the sitemap with wrong MIME type:
- **Actual:** `content-type: application/rss+xml; charset=utf-8`
- **Required:** `content-type: application/xml` or `text/xml`

Google's sitemap parser rejects the RSS content-type even though the XML is perfectly valid (356 URLs, proper format with hreflang alternates for all locales).

**Sitemap resubmitted:** Apr 7, 2026 — but will likely fail again until MIME type is corrected.

**Attempted fix via Cloudflare Worker:** A `kolo-proxy` Worker already exists in the Cloudflare account (ek@kolo.xyz) with sitemap proxy code that serves correct `application/xml` headers. However:
- kolo.xyz and kolo.in DNS zones are NOT in this Cloudflare account (no domains found)
- Both domains use Cloudflare nameservers (`sima.ns.cloudflare.com`, `nitin.ns.cloudflare.com`) but are managed from a different account (likely Webflow's integrated Cloudflare or another team account)
- Without the domain zone, we cannot attach Worker routes to intercept `/sitemap.xml` requests

**Worker endpoint verified working:** `https://kolo-proxy.ek-3ff.workers.dev/sitemap.xml` returns correct `application/xml` content-type. Just needs a route.

### 1.6 Old/Junk Pages in Sitemap — ALREADY HANDLED
Sitemap contained junk pages (old-home, test-page, quiz pages). User confirmed sitemap cleanup was already done previously. Old Home and Test Page canonicals now point to homepage as additional safety measure.

---

## 2. Google Search Console Actions

### 2.1 Sitemap Resubmission
- Resubmitted `https://kolo.xyz/sitemap.xml` on Apr 7, 2026
- Status remains "Couldn't fetch" due to MIME type issue (see 1.5)

### 2.2 Indexing Requested for 7 Key Pages
All pages successfully submitted for priority crawl via URL Inspection > Request Indexing:

| Page | Status |
|------|--------|
| `https://kolo.xyz/` | Indexing requested |
| `https://kolo.xyz/exchanger` | Indexing requested |
| `https://kolo.xyz/buy-crypto` | Indexing requested |
| `https://kolo.xyz/countries` | Indexing requested |
| `https://kolo.xyz/cryptowallet` | Indexing requested |
| `https://kolo.xyz/for-business/business` | Indexing requested |
| `https://kolo.xyz/blog` | Indexing requested |

All pages showed "URL is on Google" / "Page is indexed" status before re-requesting. The re-indexing request ensures Google picks up the new hreflang, canonical, and LLMs.txt changes.

---

## 3. Webflow Dashboard Settings Applied

- **Global canonical URL:** Set in Webflow Dashboard SEO settings
- **LLMs.txt:** Uploaded as custom file, accessible at `/llms.txt`

---

## 4. Webflow Designer Brief Document

Full technical brief created at: `webflow-designer-seo-fixes.md`

Contains:
1. Hreflang tag fix instructions (all pages x all locales)
2. Canonical tag fix instructions
3. RU/UA meta title & description translations (ready to apply)
4. JSON-LD structured data template
5. Webflow Dashboard SEO settings checklist
6. Programmatic SEO CMS Collection setup (16 CMS fields, template design, CSV import)
7. Programmatic SEO page list (41 pages: ~20 EN, ~15 RU, ~3 IT, ~3 ES)

---

## 5. Outstanding Items (Not Urgent for SEO/GEO)

| Task | Priority | Notes |
|------|----------|-------|
| **Fix sitemap MIME type** | Medium | Requires access to the Cloudflare account managing kolo.xyz DNS, OR adding kolo.xyz as zone to current CF account to attach Worker route |
| **Translate RU/UA meta titles** | Low | CTR optimization — translations ready in brief doc |
| **Mobile Core Web Vitals** | Low | 9 poor mobile URLs; minor ranking signal |
| **CMS Collection for programmatic SEO** | Future | 41 long-tail pages; requires Webflow Designer + content generation |

---

## 6. Architecture Notes

- **kolo.in** → 301 redirects to **kolo.xyz** (all paths)
- Both domains use Cloudflare nameservers but zones are NOT in the `ek@kolo.xyz` Cloudflare account
- **kolo.xyz** is hosted on Webflow (confirmed by `x-wf-region: us-east-1` header)
- Cloudflare Worker `kolo-proxy` exists at `kolo-proxy.ek-3ff.workers.dev` — handles CORS proxy for Hex.tech/Collaborator.pro APIs + sitemap MIME type fix, but has no routes attached to kolo.xyz
- Webflow Editor access: `https://kolo.xyz?edit=1` (requires invitation)

---

## 7. Verification Commands

```bash
# Check hreflang tags
curl -s https://kolo.xyz/ | grep -i hreflang

# Check canonical
curl -s https://kolo.xyz/ | grep -i canonical

# Check LLMs.txt
curl -s https://kolo.xyz/llms.txt | head -20

# Check sitemap content-type (the problem)
curl -sI https://kolo.xyz/sitemap.xml | grep content-type
# Returns: application/rss+xml (WRONG — should be application/xml)

# Check Worker sitemap fix (correct but not routed)
curl -sI https://kolo-proxy.ek-3ff.workers.dev/sitemap.xml | grep content-type
# Returns: application/xml (CORRECT)

# Check DNS
dig +short NS kolo.xyz
# Returns: sima.ns.cloudflare.com / nitin.ns.cloudflare.com
```

---

*Report generated: April 7, 2026*
*Session work by: SEO Agent (Claude)*
