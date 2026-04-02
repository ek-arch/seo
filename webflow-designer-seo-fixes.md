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

## Priority Order

1. **Hreflang tags** — fixes duplicate content signals across 3 locales
2. **Canonicals on /ru/ and /ua/** — resolves 82 "duplicate without canonical" in GSC
3. **Translate RU/UA titles & descriptions** — unlocks Russian & Ukrainian organic traffic
4. **JSON-LD structured data** — improves rich results and GEO visibility
5. **Mobile Core Web Vitals** — fixes 9 poor mobile URLs
