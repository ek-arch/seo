# Webflow Designer — SEO Fix Checklist for kolo.xyz

**Priority:** Hreflang + Canonicals are most critical — causing 82 duplicate pages in GSC.

---

## 1. Fix Hreflang Tags (ALL pages)

Every page with locale variants (/ru/, /ua/) needs correct hreflang tags in `<head>`. Currently ALL hreflang tags point to the English URL — they must point to their own locale.

**For each page, add this pattern in Custom Code → Head Code:**

```html
<link rel="alternate" hreflang="en" href="https://kolo.xyz/{page}" />
<link rel="alternate" hreflang="ru" href="https://kolo.xyz/ru/{page}" />
<link rel="alternate" hreflang="uk" href="https://kolo.xyz/ua/{page}" />
<link rel="alternate" hreflang="x-default" href="https://kolo.xyz/{page}" />
```

**Pages to apply (8 pages × 3 locales = 24 hreflang sets):**

- `/` (home)
- `/exchanger`
- `/buy-crypto`
- `/countries`
- `/blog`
- `/cryptowallet`
- `/for-business/business`
- `/cashback` (if localized)

---

## 2. Fix Canonicals on Locale Pages

Currently /ru/ and /ua/ pages have canonical pointing to the English URL → causes "duplicate without canonical" in GSC (82 pages affected).

**Fix:** Each locale page must have a **self-referencing canonical**.

- `/ru/exchanger` → canonical = `https://kolo.xyz/ru/exchanger`
- `/ua/exchanger` → canonical = `https://kolo.xyz/ua/exchanger`
- Same for every /ru/ and /ua/ page

**In Webflow Designer:** go to each locale page → Page Settings → SEO → set the canonical URL to the page's own full URL.

---

## 3. Translate RU/UA Titles & Descriptions

Switch to each locale in Designer and update SEO fields. Only `/exchanger` and `/cryptowallet` are currently translated — the rest show English titles.

### Russian (/ru/) pages

| Page | Title | Description |
|------|-------|-------------|
| Home | Kolo — Крипто Visa Карта и USDT Кошелёк \| Траты в 60+ странах | Криптокарта Visa с кэшбэком в BTC. Мультиплатформа — iOS, Android, Telegram и веб. Низкие комиссии, мгновенные переводы USDT. |
| Buy Crypto | Купить Криптовалюту Картой — USDT, BTC, ETH \| Kolo | Мгновенная покупка криптовалюты банковской картой. Низкие комиссии, быстрое зачисление. |
| Countries | Крипто Карта в 60+ Странах — Европа, ОАЭ и Другие \| Kolo | Используйте криптокарту Kolo для оплаты в более чем 60 странах мира. Европа, Великобритания, ОАЭ, СНГ. |
| Blog | Блог о Криптокартах — Новости и Гайды \| Kolo | Новости криптовалют, руководства по использованию крипто карт и советы по экономии на комиссиях. |
| Business | Крипто для Бизнеса — B2B Платежи и Корпоративные Карты \| Kolo | Принимайте криптоплатежи, выпускайте корпоративные Visa карты. Низкие комиссии, мгновенные USDT-расчёты. |
| Cashback | BTC Кэшбэк — 2% за Каждую Покупку \| Kolo | Получайте кэшбэк в биткоинах за каждую покупку криптокартой Kolo. |

### Ukrainian (/ua/) pages

| Page | Title | Description |
|------|-------|-------------|
| Home | Kolo — Крипто Visa Картка та USDT Гаманець \| Витрати в 60+ країнах | Криптокартка Visa з кешбеком у BTC. Мультиплатформа — iOS, Android, Telegram та веб. |
| Buy Crypto | Купити Криптовалюту Карткою — USDT, BTC, ETH \| Kolo | Миттєва купівля криптовалюти банківською карткою. Низькі комісії. |
| Countries | Крипто Картка у 60+ Країнах — Європа, ОАЕ та Інші \| Kolo | Використовуйте криптокартку Kolo для оплати у понад 60 країнах світу. |
| Blog | Блог про Криптокартки — Новини та Гайди \| Kolo | Новини криптовалют, інструкції з використання крипто карток та поради. |
| Business | Крипто для Бізнесу — B2B Платежі та Корпоративні Картки \| Kolo | Приймайте криптоплатежі, випускайте корпоративні Visa картки. |
| Cashback | BTC Кешбек — 2% за Кожну Покупку \| Kolo | Отримуйте кешбек у біткоїнах за кожну покупку криптокарткою Kolo. |

---

## 4. Add JSON-LD Structured Data

Add to **Site-wide Custom Code → Head Code** (applies to all pages):

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FinancialProduct",
  "name": "Kolo Crypto Visa Card",
  "description": "Crypto Visa debit card with BTC cashback. Spend in 60+ countries.",
  "provider": {
    "@type": "Organization",
    "name": "Kolo",
    "url": "https://kolo.xyz"
  },
  "url": "https://kolo.xyz",
  "category": "Crypto Debit Card",
  "areaServed": ["Europe", "United Kingdom", "UAE", "CIS"],
  "availableChannel": {
    "@type": "ServiceChannel",
    "serviceType": "Mobile App, Web, Telegram"
  }
}
</script>
```

---

## 5. Fix Mobile Core Web Vitals

GSC shows: **Mobile = 9 poor URLs, 0 good. Desktop = 9 good, 0 poor.**

Likely causes and fixes:

- **LCP**: Hero images not using WebP / not lazy-loaded properly on mobile → serve WebP, compress hero images
- **CLS**: Missing width/height on images, font loading shifts → add explicit dimensions to all images
- **Images**: Use `loading="lazy"` for below-fold images
- **Fonts**: Add `font-display: swap` to any custom font declarations in Custom Code

---

## 6. Programmatic SEO Pages — CMS Collection Setup

The SEO agent generates ~41 long-tail landing pages (e.g. "crypto card UAE", "крипто карта Грузия"). These need to be deployed via Webflow CMS.

### Step 1: Create CMS Collection "SEO Pages"

In Webflow Designer → CMS → Add New Collection → Name: **"SEO Pages"**

**Fields to create:**

| Field Name | Type | Purpose |
|------------|------|---------|
| `Name` | Plain text (default) | Page title — auto-created by Webflow |
| `Slug` | Slug (default) | URL slug — auto-created by Webflow |
| `Primary Keyword` | Plain text | Main target keyword for the page |
| `Secondary Keywords` | Plain text | Comma-separated related keywords |
| `Language` | Option (en, ru, it, es, pl) | Content language |
| `Country` | Plain text | Target country (UAE, UK, Italy, etc.) |
| `Template Type` | Option (country_card, spend_guide, persona, ru_geo, ru_generic, comparison) | Layout template |
| `Meta Title` | Plain text | SEO title tag |
| `Meta Description` | Plain text | SEO meta description |
| `H1` | Plain text | Page heading |
| `Hero Subtitle` | Plain text | Subheading below H1 |
| `Content Body` | Rich text | Main page content (generated by Claude) |
| `FAQ Section` | Rich text | FAQ accordion content |
| `JSON-LD` | Plain text | Structured data (FinancialProduct + FAQPage schema) |
| `Hreflang Tags` | Plain text | Alternate language link tags |
| `Related Pages` | Multi-reference → SEO Pages | Internal linking to related pages |
| `Priority` | Number | Sort order (1 = highest) |

### Step 2: Create CMS Template Page

1. Design a template page bound to the "SEO Pages" collection
2. URL structure: `/crypto-card/{slug}` (set in Collection Settings → URL path prefix)
3. Bind each CMS field to the corresponding element on the template:
   - `Meta Title` → Page Settings → SEO Title
   - `Meta Description` → Page Settings → Meta Description
   - `H1` → Heading element
   - `Hero Subtitle` → Paragraph element
   - `Content Body` → Rich text element
   - `FAQ Section` → Rich text element or accordion component
   - `JSON-LD` → Page Settings → Custom Code → Head Code (use Embed element)
   - `Hreflang Tags` → Page Settings → Custom Code → Head Code (use Embed element)
   - `Related Pages` → Collection list referencing the multi-ref field

### Step 3: Design Requirements

The template should match kolo.xyz brand:
- **Colors:** Dark background (#0D0D0F), accent (#6C5CE7 purple), text (#FFFFFF)
- **Sections:** Nav bar → Breadcrumbs → Hero (H1 + subtitle) → Content → Features grid → FAQ accordion → CTA ("Get Your Card") → Related pages grid → Footer
- **Responsive:** Must work on mobile (current site has Core Web Vitals issues on mobile — avoid same mistakes)
- **CTA button:** Links to `https://kolo.xyz` or deep link to card order

### Step 4: Import Data

After the collection and template are ready, import pages via CSV:
1. SEO agent app → Programmatic SEO → Tab 4 (Build Pages) → generates `cms_import.csv`
2. In Webflow → CMS → Import → upload CSV → map fields
3. Review and publish

**CSV columns match the CMS fields above.** The app exports everything pre-formatted.

### Step 5: Sitemap & Indexing

- Webflow auto-adds CMS pages to sitemap.xml
- After publishing, submit updated sitemap to Google Search Console
- The Cloudflare Worker already merges Webflow + programmatic sitemaps at `/sitemap.xml`

---

## 7. Programmatic SEO — Page List (41 pages)

Generated from the keyword matrix. One page per country + language combo:

**English pages (~20):**
- crypto-card-uae, crypto-card-uk, crypto-card-italy, crypto-card-spain, crypto-card-poland, crypto-card-germany, crypto-card-georgia, crypto-card-cyprus, crypto-card-latvia, crypto-card-romania, crypto-card-indonesia, crypto-card-montenegro, crypto-card-europe, crypto-card-digital-nomads, crypto-card-freelancers, crypto-card-business, crypto-card-comparison-2026, crypto-card-cashback, crypto-card-usdt, crypto-card-low-fees

**Russian pages (~15):**
- kripto-karta-oae, kripto-karta-ispaniya, kripto-karta-gruziya, kripto-karta-kipr, kripto-karta-latviya, kripto-karta-armeniya, kripto-karta-uzbekistan, kripto-karta-kyrgyzstan, kripto-karta-azerbaydzhan, kripto-karta-evropa, kripto-karta-frilanserov, kripto-karta-biznes, kripto-karta-usdt, kripto-karta-sravnenie-2026, kripto-karta-keshbek

**Italian pages (~3):**
- carta-crypto-italia, carta-crypto-visa-italia, carta-crypto-commissioni-basse

**Spanish pages (~3):**
- tarjeta-crypto-espana, tarjeta-crypto-visa-espana, tarjeta-crypto-comisiones-bajas

---

## Priority Order

1. **Hreflang tags** — fixes duplicate content signals across 3 locales
2. **Canonicals on /ru/ and /ua/** — resolves 82 "duplicate without canonical" in GSC
3. **Translate RU/UA titles & descriptions** — unlocks Russian & Ukrainian organic traffic
4. **JSON-LD structured data** — improves rich results and GEO visibility
5. **Mobile Core Web Vitals** — fixes 9 poor mobile URLs
6. **CMS Collection for programmatic SEO** — deploy 41 long-tail landing pages
7. **Import CSV + publish pages** — go live with programmatic SEO
