# Webflow Designer Brief — Programmatic SEO Pages for kolo.xyz

**For:** Webflow Designer with Designer-level access to kolo.xyz
**From:** SEO Agent App (kolo-seo.streamlit.app)
**Goal:** Publish ~41 auto-generated landing pages targeting long-tail crypto card keywords
**Time:** ~30 minutes of Designer work
**URL pattern:** `kolo.xyz/crypto-card/{slug}` (e.g. kolo.xyz/crypto-card/uae)

---

## What You'll Receive From Us

A ZIP folder called `pages/` containing:

```
pages/
├── cms_import.csv         ← Upload this to Webflow CMS (all pages in one file)
├── manifest.json          ← Master list with all page data
├── sitemap_fragment.xml   ← Sitemap entries for the new pages
└── DESIGNER_BRIEF.md      ← This document
```

The CSV has all content pre-written — titles, descriptions, H1s, body content, FAQ, structured data. You don't need to write anything.

---

## Step 1: Create CMS Collection (5 min)

1. Open **Webflow Designer** → **CMS** → **+ New Collection**
2. Name: **Crypto Card Pages**
3. In Collection Settings → **URL Structure** → set prefix to `crypto-card`
   - This makes pages appear at `kolo.xyz/crypto-card/{slug}`

4. Add these fields:

| # | Field Name | Field Type | Required |
|---|-----------|------------|----------|
| 1 | Name | Plain Text | ✅ (auto-created) |
| 2 | Slug | Slug | ✅ (auto-created) |
| 3 | SEO Title | Plain Text | ✅ |
| 4 | SEO Description | Plain Text | ✅ |
| 5 | H1 | Plain Text | ✅ |
| 6 | Hero Subtitle | Plain Text | ✅ |
| 7 | Body Content | Rich Text | ✅ |
| 8 | FAQ Content | Rich Text | |
| 9 | Language | Option | ✅ — Options: `en`, `ru`, `it`, `es`, `pl` |
| 10 | Country | Plain Text | |
| 11 | Primary Keyword | Plain Text | |
| 12 | JSON-LD Code | Plain Text | |
| 13 | Hreflang Tags | Plain Text | |
| 14 | Related Pages | Multi-reference → Crypto Card Pages | |

5. Save the collection

---

## Step 2: Design the CMS Template Page (15 min)

Go to **CMS Collection Pages** → click **Crypto Card Pages Template**

Build the layout with these sections top-to-bottom:

### Navigation
- Use the existing kolo.xyz nav component (copy from homepage)

### Breadcrumbs
- Simple text: `Home > Crypto Card > {Country}`
- Bind `{Country}` to the **Country** CMS field

### Hero Section
- Dark background (`#0D0D0F`)
- **H1** element → bind to **H1** CMS field
- **Subtitle** paragraph → bind to **Hero Subtitle** CMS field
- CTA button: "Get Your Kolo Card" → link to `https://kolo.xyz`
- Style: large white text, centered, padding 80px top/bottom

### Content Section
- **Rich Text** element → bind to **Body Content** CMS field
- Max width: 720px, centered
- Style: white text on dark background, comfortable line height (1.7)

### FAQ Section
- **Rich Text** element → bind to **FAQ Content** CMS field
- Style as accordion if possible, or simple Q&A format

### CTA Banner
- Full-width dark section with accent color (`#6C5CE7`)
- Text: "Ready to spend crypto anywhere?"
- Button: "Get Your Card" → `https://kolo.xyz`

### Related Pages
- **Collection List** → filter by same Language OR same Country
- Show 3-4 related pages as cards with title + country
- Or bind to **Related Pages** multi-reference field

### Footer
- Use the existing kolo.xyz footer component (copy from homepage)

### SEO Settings (on the template page)
- **Title Tag** → bind to **SEO Title** field
- **Meta Description** → bind to **SEO Description** field
- **Open Graph Title** → bind to **SEO Title** field
- **Open Graph Description** → bind to **SEO Description** field

### Custom Code (Head)
Add two **Embed** elements in the page `<head>` section:
- One for **JSON-LD Code** field (structured data)
- One for **Hreflang Tags** field (language alternates)

```html
<!-- In Custom Code → Head Code, add these as dynamic embeds: -->
<script type="application/ld+json">{JSON-LD Code field}</script>
{Hreflang Tags field}
```

---

## Step 3: Import Content via CSV (5 min)

1. Go to **CMS** → **Crypto Card Pages** → click **Import**
2. Upload `cms_import.csv` from the pages folder
3. Map CSV columns to CMS fields:

| CSV Column | → CMS Field |
|-----------|-------------|
| Name | Name |
| Slug | Slug |
| SEO Title | SEO Title |
| SEO Description | SEO Description |
| H1 | H1 |
| Hero Subtitle | Hero Subtitle |
| Body Content | Body Content |
| FAQ Content | FAQ Content |
| Language | Language |
| Country | Country |
| Primary Keyword | Primary Keyword |
| JSON-LD Code | JSON-LD Code |
| Hreflang Tags | Hreflang Tags |

4. Click **Import** — all ~41 pages created at once

---

## Step 4: Review & Publish (5 min)

1. Open a few pages in the Editor to verify content looks right:
   - `kolo.xyz/crypto-card/uae`
   - `kolo.xyz/crypto-card/uk`
   - `kolo.xyz/crypto-card/kripto-karta-oae` (Russian)
2. Check mobile responsiveness
3. **Publish** all changes

---

## Step 5: Post-Publish Checklist

- [ ] Verify pages load: `kolo.xyz/crypto-card/uae`
- [ ] Check mobile layout
- [ ] Verify sitemap includes new pages: `kolo.xyz/sitemap.xml`
- [ ] Submit updated sitemap to Google Search Console (`sc-domain:kolo.xyz`)
- [ ] Spot-check JSON-LD with Google Rich Results Test

---

## Design Reference

Match the existing kolo.xyz brand:

| Element | Value |
|---------|-------|
| Background | `#0D0D0F` (near black) |
| Text | `#FFFFFF` (white) |
| Accent / CTA | `#6C5CE7` (purple) |
| Font | Same as kolo.xyz (Inter or system) |
| Max content width | 720px |
| Button style | Rounded, purple background, white text |

---

## Page Inventory (~41 pages)

### English (~20 pages)
| Slug | Target Keyword | Country |
|------|---------------|---------|
| `uae` | crypto card UAE | UAE |
| `uk` | crypto card UK | United Kingdom |
| `italy` | crypto card Italy | Italy |
| `spain` | crypto card Spain | Spain |
| `poland` | crypto card Poland | Poland |
| `germany` | crypto card Germany | Germany |
| `georgia` | crypto card Georgia | Georgia |
| `cyprus` | crypto card Cyprus | Cyprus |
| `latvia` | crypto card Latvia | Latvia |
| `romania` | crypto card Romania | Romania |
| `indonesia` | crypto card Indonesia | Indonesia |
| `montenegro` | crypto card Montenegro | Montenegro |
| `europe` | crypto card Europe | Europe |
| `digital-nomads` | crypto card digital nomads | Global |
| `freelancers` | crypto card freelancers | Global |
| `business` | crypto card for business | Global |
| `comparison-2026` | crypto card comparison 2026 | Global |
| `cashback` | crypto card cashback bitcoin | Global |
| `usdt-card` | USDT Visa card | Global |
| `low-fees` | crypto card low fees | Global |

### Russian (~15 pages)
| Slug | Target Keyword | Country |
|------|---------------|---------|
| `ru/oae` | крипто карта ОАЭ | UAE |
| `ru/ispaniya` | крипто карта Испания | Spain |
| `ru/gruziya` | крипто карта Грузия | Georgia |
| `ru/kipr` | крипто карта Кипр | Cyprus |
| `ru/latviya` | крипто карта Латвия | Latvia |
| `ru/armeniya` | крипто карта Армения | Armenia |
| `ru/uzbekistan` | крипто карта Узбекистан | Uzbekistan |
| `ru/kyrgyzstan` | крипто карта Кыргызстан | Kyrgyzstan |
| `ru/azerbaydzhan` | крипто карта Азербайджан | Azerbaijan |
| `ru/evropa` | крипто карта Европа | Europe |
| `ru/frilanserov` | крипто карта фрилансеров | Global |
| `ru/biznes` | крипто карта для бизнеса | Global |
| `ru/usdt` | USDT карта Visa | Global |
| `ru/sravnenie` | сравнение крипто карт 2026 | Global |
| `ru/keshbek` | крипто карта кэшбэк | Global |

### Italian (~3 pages)
| Slug | Target Keyword |
|------|---------------|
| `it/italia` | carta crypto Italia |
| `it/visa-italia` | carta crypto Visa Italia |
| `it/commissioni` | carta crypto commissioni basse |

### Spanish (~3 pages)
| Slug | Target Keyword |
|------|---------------|
| `es/espana` | tarjeta crypto España |
| `es/visa-espana` | tarjeta crypto Visa España |
| `es/comisiones` | tarjeta crypto comisiones bajas |

---

## Notes
- **Do NOT create pages for:** US, Russia, Belarus, Turkey, Israel, Kazakhstan, China, India — Kolo cannot issue cards there
- **kolo.in and kolo.xyz are the same site** — kolo.in redirects to kolo.xyz
- All content is AI-generated and SEO-optimized — no editing needed unless you spot errors
- The CSV is generated by the SEO agent app at kolo-seo.streamlit.app → Programmatic SEO → Tab 4
- Questions? Contact the SEO team

---

*Generated by Kolo SEO Agent*
