"""
programmatic_seo.py — Long-Tail Keyword Discovery & Programmatic Page Generator
================================================================================
Pipeline:
  1. Generate keyword matrix from Kolo's country/crypto/use-case data (free)
  2. Validate via Google Autocomplete API (free, unlimited)
  3. Score competition via SerpAPI (only validated keywords — saves quota)
  4. Generate page specs ready for deployment

Cost: ~0 for steps 1-2. ~1 SerpAPI credit per competition check in step 3.
"""

import requests
import time
import json
import re
from typing import Optional
from urllib.parse import quote_plus
from dataclasses import dataclass, field, asdict

# ── Keyword Matrix Seeds ──────────────────────────────────────────────────────

# Countries where Kolo CAN issue cards (human-readable names + lang)
COUNTRIES = {
    # Tier 1 revenue
    "ARE": {"name": "UAE", "aliases": ["Dubai", "Abu Dhabi"], "langs": ["en", "ru"], "tier": 1},
    "GBR": {"name": "UK", "aliases": ["United Kingdom", "Britain", "England"], "langs": ["en"], "tier": 1},
    "ITA": {"name": "Italy", "aliases": ["Italia"], "langs": ["en", "it"], "tier": 1},
    "ESP": {"name": "Spain", "aliases": ["España"], "langs": ["ru", "es"], "tier": 1},
    "POL": {"name": "Poland", "aliases": ["Polska"], "langs": ["en", "pl"], "tier": 1},
    "PRT": {"name": "Portugal", "aliases": [], "langs": ["en"], "tier": 1},
    "IDN": {"name": "Indonesia", "aliases": [], "langs": ["en", "id"], "tier": 1},
    "LVA": {"name": "Latvia", "aliases": [], "langs": ["en", "ru"], "tier": 1},
    # Tier 2 growth
    "DEU": {"name": "Germany", "aliases": ["Deutschland"], "langs": ["en"], "tier": 2},
    "FRA": {"name": "France", "aliases": [], "langs": ["en"], "tier": 2},
    "CZE": {"name": "Czech Republic", "aliases": ["Czechia"], "langs": ["en"], "tier": 2},
    "ROU": {"name": "Romania", "aliases": [], "langs": ["en", "ro"], "tier": 2},
    "BGR": {"name": "Bulgaria", "aliases": [], "langs": ["en"], "tier": 2},
    "GEO": {"name": "Georgia", "aliases": ["Грузия"], "langs": ["en", "ru"], "tier": 2},
    "BRA": {"name": "Brazil", "aliases": ["Brasil"], "langs": ["en", "pt"], "tier": 2},
    "THA": {"name": "Thailand", "aliases": [], "langs": ["en"], "tier": 2},
    "UZB": {"name": "Uzbekistan", "aliases": [], "langs": ["ru", "en"], "tier": 2},
    "KGZ": {"name": "Kyrgyzstan", "aliases": [], "langs": ["ru"], "tier": 2},
    "ARM": {"name": "Armenia", "aliases": [], "langs": ["ru", "en"], "tier": 2},
    "AZE": {"name": "Azerbaijan", "aliases": [], "langs": ["ru", "en"], "tier": 2},
    "MDA": {"name": "Moldova", "aliases": [], "langs": ["ru"], "tier": 2},
    "SRB": {"name": "Serbia", "aliases": [], "langs": ["en"], "tier": 2},
    "MNE": {"name": "Montenegro", "aliases": [], "langs": ["en", "ru"], "tier": 2},
    "CHE": {"name": "Switzerland", "aliases": ["Schweiz"], "langs": ["en"], "tier": 2},
    "CYP": {"name": "Cyprus", "aliases": [], "langs": ["en", "ru"], "tier": 2},
    "LTU": {"name": "Lithuania", "aliases": [], "langs": ["en", "ru"], "tier": 2},
    # Tier 3 — select high-value
    "ARG": {"name": "Argentina", "aliases": [], "langs": ["es"], "tier": 3},
    "COL": {"name": "Colombia", "aliases": [], "langs": ["es"], "tier": 3},
    "MEX": {"name": "Mexico", "aliases": [], "langs": ["es"], "tier": 3},
    "SGP": {"name": "Singapore", "aliases": [], "langs": ["en"], "tier": 3},
    "AUS": {"name": "Australia", "aliases": [], "langs": ["en"], "tier": 3},
}

CRYPTOS = ["crypto", "USDT", "Bitcoin", "BTC", "stablecoin", "TRON", "TRC20"]

USE_CASES = [
    "card", "Visa card", "debit card", "prepaid card",
    "wallet", "spend", "pay", "exchange", "convert",
]

MODIFIERS = [
    "best", "cheapest", "low fees", "no KYC", "instant",
    "2026", "comparison", "review",
]

PERSONAS = [
    "digital nomad", "freelancer", "remote worker", "expat",
    "business", "B2B", "corporate",
]

# Russian-language seeds (RU speakers = 2x LTV)
RU_PATTERNS = [
    "крипто карта {country}",
    "USDT карта {country}",
    "криптовалютная карта Visa {country}",
    "как потратить крипту {country}",
    "крипто кошелек с картой",
    "карта для криптовалюты",
    "USDT Visa карта",
    "лучшая крипто карта 2026",
    "крипто карта для фрилансера",
    "крипто карта без KYC",
]

RU_COUNTRIES = {
    "ARE": "ОАЭ", "ESP": "Испания", "GEO": "Грузия",
    "ARM": "Армения", "UZB": "Узбекистан", "KGZ": "Кыргызстан",
    "MDA": "Молдова", "CYP": "Кипр", "MNE": "Черногория",
    "LVA": "Латвия", "LTU": "Литва", "POL": "Польша",
}


# ── Step 1: Matrix Generation ────────────────────────────────────────────────

def generate_keyword_matrix(
    tiers: list[int] = [1, 2],
    include_ru: bool = True,
    max_combos: int = 5000,
) -> list[dict]:
    """
    Generate all candidate long-tail keywords from combinatorial seeds.
    Returns list of {"keyword": str, "lang": str, "country": str, "pattern": str, "tier": int}
    """
    keywords = []

    # English patterns
    en_patterns = [
        "{crypto} {use_case} {country}",          # "USDT Visa card UAE"
        "{modifier} {crypto} {use_case} {country}",  # "best crypto card UK"
        "{crypto} {use_case} for {persona}",       # "crypto card for digital nomad"
        "how to {use_case} {crypto} in {country}", # "how to spend USDT in Italy"
        "{crypto} to fiat {country}",              # "crypto to fiat Germany"
        "{use_case} {crypto} in {country}",        # "spend Bitcoin in Spain"
        "{modifier} {crypto} {use_case}",          # "cheapest crypto debit card"
    ]

    filtered_countries = {k: v for k, v in COUNTRIES.items() if v["tier"] in tiers}

    for code, cdata in filtered_countries.items():
        country_names = [cdata["name"]] + cdata["aliases"]
        for cname in country_names:
            for crypto in CRYPTOS[:4]:  # top 4
                for use_case in USE_CASES[:5]:  # top 5
                    kw = f"{crypto} {use_case} {cname}"
                    keywords.append({
                        "keyword": kw.lower(),
                        "lang": "en",
                        "country": code,
                        "pattern": "crypto+usecase+country",
                        "tier": cdata["tier"],
                    })
            for modifier in MODIFIERS[:4]:
                for use_case in USE_CASES[:3]:
                    kw = f"{modifier} crypto {use_case} {cname}"
                    keywords.append({
                        "keyword": kw.lower(),
                        "lang": "en",
                        "country": code,
                        "pattern": "modifier+crypto+usecase+country",
                        "tier": cdata["tier"],
                    })
            # Persona patterns (no country needed)
            for persona in PERSONAS[:3]:
                kw = f"crypto card for {persona} {cname}"
                keywords.append({
                    "keyword": kw.lower(),
                    "lang": "en",
                    "country": code,
                    "pattern": "crypto+persona+country",
                    "tier": cdata["tier"],
                })

    # Global (no country) patterns
    for crypto in CRYPTOS:
        for use_case in USE_CASES:
            kw = f"{crypto} {use_case}"
            keywords.append({
                "keyword": kw.lower(),
                "lang": "en",
                "country": "global",
                "pattern": "crypto+usecase",
                "tier": 0,
            })
        for modifier in MODIFIERS:
            kw = f"{modifier} {crypto} card"
            keywords.append({
                "keyword": kw.lower(),
                "lang": "en",
                "country": "global",
                "pattern": "modifier+crypto+card",
                "tier": 0,
            })

    # Russian patterns
    if include_ru:
        for pattern in RU_PATTERNS:
            if "{country}" in pattern:
                for code, ru_name in RU_COUNTRIES.items():
                    if COUNTRIES.get(code, {}).get("tier", 99) in tiers:
                        kw = pattern.format(country=ru_name)
                        keywords.append({
                            "keyword": kw,
                            "lang": "ru",
                            "country": code,
                            "pattern": "ru_geo",
                            "tier": COUNTRIES[code]["tier"],
                        })
            else:
                keywords.append({
                    "keyword": pattern,
                    "lang": "ru",
                    "country": "global",
                    "pattern": "ru_generic",
                    "tier": 0,
                })

    # Deduplicate
    seen = set()
    unique = []
    for kw in keywords:
        key = kw["keyword"]
        if key not in seen:
            seen.add(key)
            unique.append(kw)

    return unique[:max_combos]


# ── Step 2: Google Autocomplete Validation (FREE) ────────────────────────────

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"

def check_autocomplete(query: str, lang: str = "en", country: str = "") -> list[str]:
    """
    Query Google Autocomplete API. FREE & unlimited.
    Returns list of suggested completions. If query appears in suggestions → real demand.
    """
    params = {
        "client": "firefox",  # returns JSON
        "q": query,
        "hl": lang,
    }
    if country:
        params["gl"] = country.lower()

    try:
        resp = requests.get(AUTOCOMPLETE_URL, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Format: [query, [suggestions]]
            if len(data) >= 2 and isinstance(data[1], list):
                return data[1]
    except Exception:
        pass
    return []


def validate_keywords_autocomplete(
    keywords: list[dict],
    delay: float = 0.15,  # be polite to Google
    progress_callback=None,
) -> list[dict]:
    """
    Filter keywords through Google Autocomplete.
    A keyword is 'validated' if Google suggests it (or a close variant).
    Returns keywords with added 'autocomplete_hits' and 'validated' fields.
    """
    results = []
    total = len(keywords)

    for i, kw in enumerate(keywords):
        query = kw["keyword"]
        lang = kw["lang"]
        country_code = kw.get("country", "")
        gl = country_code if country_code != "global" else ""

        suggestions = check_autocomplete(query, lang=lang, country=gl)

        # Check if our query (or close prefix) appears in suggestions
        query_lower = query.lower()
        hits = [s for s in suggestions if query_lower in s.lower() or s.lower() in query_lower]

        kw_result = {**kw}
        kw_result["autocomplete_suggestions"] = suggestions[:5]
        kw_result["autocomplete_hits"] = len(hits)
        kw_result["validated"] = len(hits) > 0 or len(suggestions) > 0
        # If Google returns ANY suggestions for this prefix, there's related demand
        kw_result["demand_signal"] = (
            "strong" if len(hits) > 0 else
            "medium" if len(suggestions) > 3 else
            "weak" if len(suggestions) > 0 else
            "none"
        )
        results.append(kw_result)

        if progress_callback:
            progress_callback(i + 1, total)

        time.sleep(delay)

    return results


# ── Step 3: Competition Scoring via SerpAPI ───────────────────────────────────

def check_serp_competition(keyword: str, serpapi_key: str, lang: str = "en", country: str = "") -> dict:
    """
    Check SERP competition for a keyword. Costs 1 SerpAPI credit.
    Returns competition score + opportunity analysis.
    """
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": serpapi_key,
        "num": 10,
        "hl": lang,
    }
    if country and country != "global":
        params["gl"] = country.lower()

    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"error": str(e), "competition_score": None}

    organic = data.get("organic_results", [])

    # Analyze top 10
    big_domains = {
        "crypto.com", "coinbase.com", "binance.com", "revolut.com",
        "bybit.com", "nexo.com", "wirex.com", "forbes.com",
        "investopedia.com", "cointelegraph.com", "coindesk.com",
    }

    dr_estimates = []  # rough DR buckets
    big_count = 0
    forum_count = 0
    weak_count = 0
    kolo_present = False

    for r in organic[:10]:
        link = r.get("link", "")
        domain = r.get("displayed_link", "").split("/")[0].replace("www.", "").lower() if r.get("displayed_link") else ""

        if any(d in link for d in ["kolo.in", "kolo.xyz"]):
            kolo_present = True
        if any(d in domain for d in big_domains):
            big_count += 1
        if any(d in domain for d in ["reddit.com", "quora.com", "medium.com", "youtube.com"]):
            forum_count += 1
        # Weak = small blog, listicle, or thin content
        snippet = r.get("snippet", "")
        title = r.get("title", "")
        if len(snippet) < 80 or any(w in domain for w in ["blogspot", "wordpress", "wixsite", "substack"]):
            weak_count += 1

    # Competition score: 0 (easy) to 10 (impossible)
    score = min(10, big_count * 2 + max(0, 5 - forum_count - weak_count))

    # Opportunity = inverse of competition + presence of weak results
    opportunity = "high" if score <= 3 else "medium" if score <= 6 else "low"

    return {
        "keyword": keyword,
        "competition_score": score,
        "opportunity": opportunity,
        "big_players": big_count,
        "forums_ugc": forum_count,
        "weak_results": weak_count,
        "kolo_present": kolo_present,
        "total_results": data.get("search_information", {}).get("total_results", 0),
        "featured_snippet": "answer_box" in data,
        "people_also_ask": len(data.get("related_questions", [])),
        "related_searches": [r.get("query", "") for r in data.get("related_searches", [])[:5]],
        "top_3_domains": [
            r.get("displayed_link", "").split("/")[0].replace("www.", "")
            for r in organic[:3]
        ],
    }


def batch_competition_check(
    keywords: list[dict],
    serpapi_key: str,
    max_checks: int = 30,
    delay: float = 2.0,
    progress_callback=None,
) -> list[dict]:
    """
    Check competition for top validated keywords. Limits SerpAPI usage.
    """
    results = []
    to_check = keywords[:max_checks]

    for i, kw in enumerate(to_check):
        serp = check_serp_competition(
            kw["keyword"],
            serpapi_key,
            lang=kw.get("lang", "en"),
            country=kw.get("country", ""),
        )
        result = {**kw, **serp}
        results.append(result)

        if progress_callback:
            progress_callback(i + 1, len(to_check))

        if i < len(to_check) - 1:
            time.sleep(delay)

    return results


# ── Step 4: Page Spec Generator ───────────────────────────────────────────────

@dataclass
class PageSpec:
    """Specification for an auto-generated programmatic SEO page."""
    slug: str
    keyword: str
    lang: str
    country: str
    title: str
    meta_description: str
    h1: str
    template: str  # which template to use
    variables: dict = field(default_factory=dict)
    competition_score: Optional[int] = None
    opportunity: str = ""
    demand_signal: str = ""

    def to_dict(self):
        return asdict(self)


# Country data for templates
COUNTRY_DETAILS = {
    "ARE": {"currency": "AED", "currency_name": "UAE Dirham", "region": "Middle East"},
    "GBR": {"currency": "GBP", "currency_name": "British Pound", "region": "Europe"},
    "ITA": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "ESP": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "POL": {"currency": "PLN", "currency_name": "Polish Zloty", "region": "Europe"},
    "PRT": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "IDN": {"currency": "IDR", "currency_name": "Indonesian Rupiah", "region": "Asia Pacific"},
    "DEU": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "FRA": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "BRA": {"currency": "BRL", "currency_name": "Brazilian Real", "region": "Latin America"},
    "THA": {"currency": "THB", "currency_name": "Thai Baht", "region": "Asia Pacific"},
    "GEO": {"currency": "GEL", "currency_name": "Georgian Lari", "region": "Caucasus"},
    "ARM": {"currency": "AMD", "currency_name": "Armenian Dram", "region": "Caucasus"},
    "UZB": {"currency": "UZS", "currency_name": "Uzbek Som", "region": "Central Asia"},
    "KGZ": {"currency": "KGS", "currency_name": "Kyrgyz Som", "region": "Central Asia"},
    "ROU": {"currency": "RON", "currency_name": "Romanian Leu", "region": "Europe"},
    "SRB": {"currency": "RSD", "currency_name": "Serbian Dinar", "region": "Europe"},
    "MNE": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "MDA": {"currency": "MDL", "currency_name": "Moldovan Leu", "region": "Europe"},
    "CYP": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "LTU": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "LVA": {"currency": "EUR", "currency_name": "Euro", "region": "Europe"},
    "CHE": {"currency": "CHF", "currency_name": "Swiss Franc", "region": "Europe"},
    "BGR": {"currency": "BGN", "currency_name": "Bulgarian Lev", "region": "Europe"},
    "CZE": {"currency": "CZK", "currency_name": "Czech Koruna", "region": "Europe"},
    "AZE": {"currency": "AZN", "currency_name": "Azerbaijani Manat", "region": "Caucasus"},
    "SGP": {"currency": "SGD", "currency_name": "Singapore Dollar", "region": "Asia Pacific"},
    "AUS": {"currency": "AUD", "currency_name": "Australian Dollar", "region": "Asia Pacific"},
    "ARG": {"currency": "ARS", "currency_name": "Argentine Peso", "region": "Latin America"},
    "COL": {"currency": "COP", "currency_name": "Colombian Peso", "region": "Latin America"},
    "MEX": {"currency": "MXN", "currency_name": "Mexican Peso", "region": "Latin America"},
}


def generate_page_specs(scored_keywords: list[dict], min_opportunity: str = "medium") -> list[PageSpec]:
    """
    Convert scored keywords into page specifications.
    Only includes keywords with sufficient opportunity.
    """
    opp_order = {"high": 3, "medium": 2, "low": 1, "": 0}
    min_opp = opp_order.get(min_opportunity, 0)

    specs = []
    seen_slugs = set()

    for kw in scored_keywords:
        opp = opp_order.get(kw.get("opportunity", ""), 0)
        if opp < min_opp:
            continue

        keyword = kw["keyword"]
        country = kw.get("country", "global")
        lang = kw.get("lang", "en")

        # Generate slug
        slug = re.sub(r'[^a-z0-9]+', '-', keyword.lower()).strip('-')
        if slug in seen_slugs:
            slug = f"{slug}-{country.lower()}"
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        # Get country details
        cdetails = COUNTRY_DETAILS.get(country, {})
        country_name = COUNTRIES.get(country, {}).get("name", country)

        # Determine template
        if country != "global" and "card" in keyword.lower():
            template = "country_card"
        elif "spend" in keyword.lower() or "pay" in keyword.lower():
            template = "spend_guide"
        elif any(p in keyword.lower() for p in ["freelancer", "nomad", "expat", "business"]):
            template = "persona"
        elif lang == "ru":
            template = "ru_generic"
        else:
            template = "generic_comparison"

        # Build title & meta
        if template == "country_card":
            title = f"Crypto Visa Card in {country_name} — Spend USDT, BTC & ETH | Kolo"
            meta = f"Get a crypto Visa card in {country_name}. Convert USDT, Bitcoin & ETH to {cdetails.get('currency', 'local currency')} instantly. Works at 60M+ merchants. No bank account needed."
            h1 = f"Crypto Visa Card in {country_name}"
        elif template == "spend_guide":
            title = f"How to Spend Crypto in {country_name} — USDT & Bitcoin Guide 2026 | Kolo"
            meta = f"Complete guide to spending cryptocurrency in {country_name}. Convert USDT or Bitcoin to {cdetails.get('currency_name', 'local currency')} with Kolo Visa card. Low fees, instant conversion."
            h1 = f"How to Spend Crypto in {country_name}"
        elif template == "persona":
            persona = next((p for p in PERSONAS if p in keyword.lower()), "crypto user")
            title = f"Best Crypto Card for {persona.title()}s — Spend Anywhere | Kolo"
            meta = f"The best crypto Visa card for {persona}s. Spend USDT, BTC, ETH in 60+ countries with low fees. Instant conversion, no bank account required."
            h1 = f"Best Crypto Card for {persona.title()}s"
        else:
            title = f"{keyword.title()} — Kolo Crypto Visa Card"
            meta = f"{keyword.title()}. Kolo offers instant crypto-to-fiat conversion with a Visa card in 60+ countries. Low fees, multi-currency wallet."
            h1 = keyword.title()

        spec = PageSpec(
            slug=slug,
            keyword=keyword,
            lang=lang,
            country=country,
            title=title,
            meta_description=meta,
            h1=h1,
            template=template,
            variables={
                "country_name": country_name,
                "currency": cdetails.get("currency", ""),
                "currency_name": cdetails.get("currency_name", ""),
                "region": cdetails.get("region", ""),
            },
            competition_score=kw.get("competition_score"),
            opportunity=kw.get("opportunity", ""),
            demand_signal=kw.get("demand_signal", ""),
        )
        specs.append(spec)

    return specs


# ── HTML Template Generator ───────────────────────────────────────────────────

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="https://kolo.xyz/{slug}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://kolo.xyz/{slug}">
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FinancialProduct",
        "name": "Kolo Crypto Visa Card",
        "description": "{meta_description}",
        "provider": {{
            "@type": "Organization",
            "name": "Kolo",
            "url": "https://kolo.xyz"
        }},
        "url": "https://kolo.xyz/{slug}",
        "category": "Cryptocurrency Card",
        "areaServed": "{country_name}",
        "availableChannel": {{
            "@type": "ServiceChannel",
            "serviceUrl": "https://kolo.xyz"
        }}
    }}
    </script>
</head>
<body>
    <h1>{h1}</h1>
    {content_blocks}
    <p><a href="https://kolo.xyz">Get your Kolo Crypto Visa Card →</a></p>
</body>
</html>
"""


def generate_html_page(spec: PageSpec, content_blocks: str = "") -> str:
    """Generate a basic HTML page from a PageSpec. Content blocks can be added by Claude API."""
    if not content_blocks:
        content_blocks = _default_content_blocks(spec)

    return PAGE_TEMPLATE.format(
        lang=spec.lang,
        title=spec.title,
        meta_description=spec.meta_description,
        slug=spec.slug,
        h1=spec.h1,
        country_name=spec.variables.get("country_name", ""),
        content_blocks=content_blocks,
    )


def _default_content_blocks(spec: PageSpec) -> str:
    """Generate template-based content blocks (no LLM needed)."""
    country = spec.variables.get("country_name", "your country")
    currency = spec.variables.get("currency_name", "local currency")
    region = spec.variables.get("region", "")

    if spec.template == "country_card":
        return f"""
    <section>
        <h2>Why Use a Crypto Card in {country}?</h2>
        <p>Spending cryptocurrency in {country} is now as simple as using a regular Visa card.
        Kolo converts your USDT, Bitcoin, or Ethereum to {currency} instantly at the point of sale —
        no manual exchange, no bank transfers, no delays.</p>
        <h3>How It Works</h3>
        <ol>
            <li>Load your Kolo wallet with USDT (TRC-20), BTC, or ETH</li>
            <li>Your Kolo Visa card is linked to your wallet balance</li>
            <li>Pay at any Visa-accepting merchant in {country}</li>
            <li>Crypto converts to {currency} automatically at competitive rates</li>
        </ol>
        <h3>Supported Cryptocurrencies</h3>
        <ul>
            <li>USDT (TRC-20 & ERC-20)</li>
            <li>Bitcoin (BTC)</li>
            <li>Ethereum (ETH)</li>
            <li>TRON (TRX)</li>
        </ul>
        <h3>Available in {country}</h3>
        <p>Kolo cards are fully supported in {country}. Apply through the Kolo app
        (available on iOS, Android, Telegram, and web), complete verification, and
        receive your virtual card instantly. Physical cards are also available.</p>
    </section>"""
    elif spec.template == "spend_guide":
        return f"""
    <section>
        <h2>Spending Crypto in {country}: Your Complete Guide</h2>
        <p>Want to use your Bitcoin or USDT for everyday purchases in {country}?
        Here's everything you need to know about converting crypto to {currency}.</p>
        <h3>Option 1: Crypto Visa Card (Recommended)</h3>
        <p>A crypto Visa card like Kolo lets you spend directly at any of the 60M+
        Visa merchants worldwide, including all shops and restaurants in {country}.
        Your crypto converts to {currency} at the moment of payment.</p>
        <h3>Option 2: P2P Exchange</h3>
        <p>Peer-to-peer platforms let you sell crypto for {currency}, but involve
        manual transfers and counterparty risk. Not ideal for everyday spending.</p>
        <h3>Option 3: Centralized Exchange Withdrawal</h3>
        <p>Sell crypto on an exchange and withdraw to a bank account. Takes 1-3 days
        and involves exchange + withdrawal fees.</p>
        <h3>Why a Crypto Card Wins</h3>
        <ul>
            <li>Instant conversion — no waiting for bank transfers</li>
            <li>Works everywhere Visa is accepted</li>
            <li>Low fees compared to P2P or exchange withdrawal</li>
            <li>Keep your crypto until you actually spend it</li>
        </ul>
    </section>"""
    elif spec.template == "persona":
        return f"""
    <section>
        <h2>The Best Crypto Card for Your Lifestyle</h2>
        <p>Whether you're earning in crypto, holding stablecoins, or just want a backup
        payment method that works globally — Kolo's Visa card is built for you.</p>
        <h3>Key Features</h3>
        <ul>
            <li>Works in 60+ countries across {region or "multiple regions"}</li>
            <li>Instant USDT/BTC/ETH to fiat conversion</li>
            <li>Virtual card issued instantly — physical card available</li>
            <li>Multi-currency wallet in the app</li>
            <li>No traditional bank account required</li>
        </ul>
        <h3>Get Started</h3>
        <p>Download Kolo on iOS, Android, or use the Telegram mini-app.
        Complete verification and get your card in minutes.</p>
    </section>"""
    else:
        return f"""
    <section>
        <h2>{spec.h1}</h2>
        <p>Kolo offers a crypto Visa card that works in 60+ countries. Convert USDT,
        Bitcoin, and Ethereum to local currency instantly at the point of sale.</p>
        <h3>Why Choose Kolo?</h3>
        <ul>
            <li>Low conversion fees</li>
            <li>Instant virtual card issuance</li>
            <li>Multi-currency crypto wallet</li>
            <li>Available on iOS, Android, Telegram, and web</li>
            <li>No bank account required</li>
        </ul>
    </section>"""


# ── Export Utilities ──────────────────────────────────────────────────────────

def export_specs_json(specs: list[PageSpec], filepath: str):
    """Export page specs as JSON for deployment pipeline."""
    data = [s.to_dict() for s in specs]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return len(data)


def export_specs_csv(specs: list[PageSpec], filepath: str):
    """Export page specs as CSV for review."""
    import csv
    fields = ["slug", "keyword", "lang", "country", "title", "meta_description",
              "template", "competition_score", "opportunity", "demand_signal"]
    with open(filepath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in specs:
            d = s.to_dict()
            w.writerow({k: d.get(k, "") for k in fields})
    return len(specs)
