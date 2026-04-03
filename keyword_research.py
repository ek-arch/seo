"""
keyword_research.py — Competitive keyword intelligence for Kolo SEO Agent
==========================================================================
Three data sources:
  1. Ahrefs API/MCP — competitor organic keywords, volumes, difficulty
  2. SerpAPI — "People Also Ask" + related searches (free expansion)
  3. Manual seed list — curated from market data

Builds a ranked keyword taxonomy:
  Head → Mid-tail → Long-tail → Comparison → Problem-solving
Split by market, language, and competition level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import requests


# ── Keyword Categories ───────────────────────────────────────────────────────

@dataclass
class Keyword:
    """A single keyword with all research data."""
    keyword: str
    language: str = "en"
    market: str = "global"           # ISO3 country code or "global"/"EU"
    category: str = "generic"         # head / mid_tail / long_tail / comparison / problem / b2b / branded
    intent: str = "transactional"     # transactional / informational / navigational
    # Volume & competition (from Ahrefs)
    volume: Optional[int] = None      # monthly search volume
    difficulty: Optional[int] = None  # keyword difficulty 0-100
    cpc: Optional[float] = None       # cost per click USD
    # SERP features
    has_ai_overview: bool = False
    has_featured_snippet: bool = False
    # Competitor presence
    competitor_domains: list[str] = field(default_factory=list)
    kolo_ranking: Optional[int] = None
    # GEO visibility (from Perplexity)
    ai_kolo_visible: Optional[bool] = None
    ai_competitors_mentioned: list[str] = field(default_factory=list)
    # Scoring
    priority_score: float = 0.0       # computed composite score


def classify_keyword(kw: str) -> str:
    """Auto-classify a keyword into category."""
    kw_lower = kw.lower()
    if any(w in kw_lower for w in ["vs", "versus", "comparison", "compare", "better"]):
        return "comparison"
    if any(w in kw_lower for w in ["how to", "how can", "what is the", "can i", "is there", "easiest way", "cheapest way"]):
        return "problem"
    if any(w in kw_lower for w in ["business", "corporate", "b2b", "company", "invoice"]):
        return "b2b"
    if any(w in kw_lower for w in ["kolo"]):
        return "branded"
    words = kw_lower.split()
    if len(words) <= 3:
        return "head"
    if len(words) <= 5:
        return "mid_tail"
    return "long_tail"


def detect_language(kw: str) -> str:
    """Simple language detection based on character sets."""
    if any('\u0400' <= c <= '\u04ff' for c in kw):
        return "ru"
    if any(c in kw for c in "àèéìòùç"):
        return "it"
    if any(c in kw for c in "áéíóúñ¿¡"):
        return "es"
    if any(c in kw for c in "ąćęłńóśźż"):
        return "pl"
    if any(c in kw for c in "ãõâê"):
        return "pt"
    return "en"


def detect_market(kw: str) -> str:
    """Detect target market from keyword text."""
    kw_lower = kw.lower()
    market_map = {
        "uk": "GBR", "united kingdom": "GBR", "britain": "GBR", "british": "GBR",
        "uae": "ARE", "dubai": "ARE", "emirates": "ARE", "оаэ": "ARE", "дубай": "ARE",
        "italy": "ITA", "italia": "ITA", "italian": "ITA", "италия": "ITA",
        "spain": "ESP", "españa": "ESP", "spanish": "ESP", "испания": "ESP",
        "poland": "POL", "polish": "POL", "polska": "POL", "польша": "POL",
        "europe": "EU", "european": "EU", "eu ": "EU", "европ": "EU",
        "indonesia": "IDN", "indonesian": "IDN",
        "romania": "ROU", "romanian": "ROU",
        "brazil": "BRA", "brazilian": "BRA", "brasil": "BRA",
        "germany": "DEU", "german": "DEU", "deutschland": "DEU",
        "latvia": "LVA", "latvian": "LVA",
        "georgia": "GEO", "грузия": "GEO",
        "uzbekistan": "UZB", "узбекистан": "UZB",
        "kazakhstan": "KAZ", "казахстан": "KAZ",
        "cis": "CIS", "снг": "CIS",
    }
    for term, market in market_map.items():
        if term in kw_lower:
            return market
    return "global"


def score_keyword(kw: Keyword) -> float:
    """
    Score a keyword for priority. Higher = more worth targeting.
    Factors:
      - Volume (log-scaled, max 30 pts)
      - Difficulty inversed (easy = high score, max 25 pts)
      - AI overview present (bonus 10 pts — means AI answers, GEO opportunity)
      - No Kolo ranking yet (bonus 10 pts — untapped)
      - Category bonus: comparison +10, problem +8, b2b +8, long_tail +5
      - Market LTV weight (RU markets get 2x)
    """
    import math

    score = 0.0

    # Volume (0-30)
    if kw.volume and kw.volume > 0:
        score += min(math.log10(kw.volume) * 10, 30)

    # Difficulty inverse (0-25)
    if kw.difficulty is not None:
        score += max(0, 25 - kw.difficulty * 0.25)

    # AI overview present = GEO opportunity
    if kw.has_ai_overview:
        score += 10

    # Not ranking yet = untapped
    if kw.kolo_ranking is None:
        score += 10
    elif kw.kolo_ranking > 10:
        score += 5  # ranking but not on page 1

    # Category bonus
    cat_bonus = {"comparison": 10, "problem": 8, "b2b": 8, "long_tail": 5, "mid_tail": 3, "branded": -5}
    score += cat_bonus.get(kw.category, 0)

    # Language LTV weight
    lang_multiplier = {"ru": 1.5, "en": 1.0, "it": 0.9, "es": 0.9, "pl": 0.8, "pt": 0.7, "id": 0.5, "ro": 0.8}
    score *= lang_multiplier.get(kw.language, 1.0)

    return round(score, 1)


# ── Seed Keywords ────────────────────────────────────────────────────────────
# Curated from: Kolo market data, competitor analysis, product features
# Organized by category and market for systematic expansion

SEED_KEYWORDS: list[dict] = [
    # ── HEAD TERMS (high volume, high competition) ───────────────────────
    {"q": "best crypto card 2026", "lang": "en", "market": "global"},
    {"q": "crypto debit card", "lang": "en", "market": "global"},
    {"q": "USDT Visa card", "lang": "en", "market": "global"},
    {"q": "crypto card", "lang": "en", "market": "global"},
    {"q": "best crypto card", "lang": "en", "market": "global"},

    # ── GEO-TARGETED: ENGLISH ────────────────────────────────────────────
    {"q": "crypto card Europe", "lang": "en", "market": "EU"},
    {"q": "crypto card UK", "lang": "en", "market": "GBR"},
    {"q": "best crypto card UK 2026", "lang": "en", "market": "GBR"},
    {"q": "crypto card UAE", "lang": "en", "market": "ARE"},
    {"q": "crypto Visa card Dubai", "lang": "en", "market": "ARE"},
    {"q": "crypto card digital nomad", "lang": "en", "market": "global"},
    {"q": "crypto card for freelancers", "lang": "en", "market": "global"},

    # ── GEO-TARGETED: RUSSIAN (2x LTV!) ──────────────────────────────────
    {"q": "криптокарта Visa 2026", "lang": "ru", "market": "global"},
    {"q": "лучшая крипто карта", "lang": "ru", "market": "global"},
    {"q": "USDT карта Visa", "lang": "ru", "market": "global"},
    {"q": "крипто карта Европа", "lang": "ru", "market": "EU"},
    {"q": "крипто карта ОАЭ", "lang": "ru", "market": "ARE"},
    {"q": "крипто карта Дубай", "lang": "ru", "market": "ARE"},
    {"q": "криптокарта для бизнеса", "lang": "ru", "market": "global"},
    {"q": "как потратить USDT картой", "lang": "ru", "market": "global"},
    {"q": "крипто карта с кэшбэком", "lang": "ru", "market": "global"},

    # ── GEO-TARGETED: ITALIAN ────────────────────────────────────────────
    {"q": "carta crypto Italia 2026", "lang": "it", "market": "ITA"},
    {"q": "migliore carta crypto", "lang": "it", "market": "ITA"},
    {"q": "carta Visa crypto", "lang": "it", "market": "ITA"},

    # ── GEO-TARGETED: SPANISH ────────────────────────────────────────────
    {"q": "tarjeta crypto España 2026", "lang": "es", "market": "ESP"},
    {"q": "mejor tarjeta crypto Visa", "lang": "es", "market": "ESP"},
    {"q": "tarjeta USDT Visa", "lang": "es", "market": "ESP"},

    # ── GEO-TARGETED: POLISH ─────────────────────────────────────────────
    {"q": "karta krypto Polska 2026", "lang": "pl", "market": "POL"},
    {"q": "najlepsza karta kryptowalutowa", "lang": "pl", "market": "POL"},

    # ── GEO-TARGETED: INDONESIAN ─────────────────────────────────────────
    {"q": "kartu crypto terbaik Indonesia", "lang": "id", "market": "IDN"},
    {"q": "kartu Visa USDT", "lang": "id", "market": "IDN"},

    # ── PRODUCT-SPECIFIC ─────────────────────────────────────────────────
    {"q": "TRC20 USDT card", "lang": "en", "market": "global"},
    {"q": "crypto card low fees", "lang": "en", "market": "global"},
    {"q": "crypto card BTC cashback", "lang": "en", "market": "global"},
    {"q": "multi-currency crypto wallet card", "lang": "en", "market": "global"},
    {"q": "spend stablecoins with Visa", "lang": "en", "market": "global"},

    # ── COMPARISON ───────────────────────────────────────────────────────
    {"q": "Kolo vs Wirex", "lang": "en", "market": "global"},
    {"q": "Kolo vs Crypto.com card", "lang": "en", "market": "global"},
    {"q": "Kolo vs Bybit card", "lang": "en", "market": "global"},
    {"q": "crypto card comparison 2026", "lang": "en", "market": "global"},
    {"q": "Wirex vs Binance card vs Kolo", "lang": "en", "market": "global"},

    # ── PROBLEM-SOLVING / LONG-TAIL ──────────────────────────────────────
    {"q": "how to spend USDT with a Visa card", "lang": "en", "market": "global"},
    {"q": "cheapest way to convert USDT to fiat", "lang": "en", "market": "global"},
    {"q": "can I use crypto card in Europe without KYC", "lang": "en", "market": "EU"},
    {"q": "best way to spend crypto while traveling", "lang": "en", "market": "global"},
    {"q": "crypto card that works in 60 countries", "lang": "en", "market": "global"},
    {"q": "how to get Visa card funded by cryptocurrency", "lang": "en", "market": "global"},

    # ── B2B (41% of Kolo spend, growing 7x) ──────────────────────────────
    {"q": "crypto card for business", "lang": "en", "market": "global"},
    {"q": "corporate crypto Visa card", "lang": "en", "market": "global"},
    {"q": "crypto payment solution for business Europe", "lang": "en", "market": "EU"},
    {"q": "business expenses with crypto card", "lang": "en", "market": "global"},
    {"q": "USDT corporate card", "lang": "en", "market": "global"},

    # ── CIS MARKETS (newly supported: UZB, KGZ, ARM, AZE) ───────────────
    {"q": "крипто карта Узбекистан", "lang": "ru", "market": "UZB"},
    {"q": "криптокарта Visa Кыргызстан", "lang": "ru", "market": "KGZ"},
    {"q": "крипто карта Армения", "lang": "ru", "market": "ARM"},
    {"q": "крипто карта Грузия", "lang": "ru", "market": "GEO"},
]


# ── Ahrefs Integration ───────────────────────────────────────────────────────

COMPETITOR_DOMAINS = [
    "crypto.com", "wirex.com", "bybit.com", "nexo.com",
    "oobit.com", "bitget.com", "revolut.com",
]


def fetch_ahrefs_organic_keywords(
    api_key: str,
    domain: str,
    *,
    country: str = "us",
    limit: int = 100,
) -> list[dict]:
    """
    Fetch organic keywords for a domain via Ahrefs API v3.
    Returns list of {keyword, volume, position, difficulty, cpc}.
    """
    url = "https://api.ahrefs.com/v3/site-explorer/organic-keywords"
    params = {
        "target": domain,
        "select": "keyword,volume,best_position,keyword_difficulty,cpc",
        "country": country,
        "limit": limit,
        "order_by": "volume:desc",
    }
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("keywords", data.get("items", []))


def fetch_ahrefs_keyword_overview(
    api_key: str,
    keywords: list[str],
    *,
    country: str = "us",
) -> list[dict]:
    """
    Get volume, difficulty, CPC for a batch of keywords.
    """
    url = "https://api.ahrefs.com/v3/keywords-explorer/overview"
    params = {
        "keywords": ",".join(keywords[:10]),  # API limit per request
        "country": country,
        "select": "keyword,volume,difficulty,cpc",
    }
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("keywords", data.get("items", []))


# ── SerpAPI Expansion (free keyword ideas) ───────────────────────────────────

def expand_keywords_serpapi(
    api_key: str,
    seed_query: str,
) -> dict:
    """
    Use SerpAPI to get 'People Also Ask' and 'Related Searches' for a query.
    Free way to discover long-tail keywords.
    """
    url = "https://serpapi.com/search.json"
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": seed_query,
        "num": 10,
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return {"people_also_ask": [], "related_searches": []}

    paa = [item.get("question", "") for item in data.get("related_questions", [])]
    related = [item.get("query", "") for item in data.get("related_searches", [])]

    return {
        "people_also_ask": paa,
        "related_searches": related,
    }


# ── Build Keyword Taxonomy ───────────────────────────────────────────────────

def build_taxonomy(
    seeds: Optional[list[dict]] = None,
    ahrefs_key: Optional[str] = None,
) -> list[Keyword]:
    """
    Build keyword taxonomy from seeds + optional Ahrefs enrichment.
    Returns list of Keyword objects sorted by priority score.
    """
    if seeds is None:
        seeds = SEED_KEYWORDS

    keywords = []
    for seed in seeds:
        q = seed["q"]
        lang = seed.get("lang") or detect_language(q)
        market = seed.get("market") or detect_market(q)

        kw = Keyword(
            keyword=q,
            language=lang,
            market=market,
            category=classify_keyword(q),
            intent="informational" if any(w in q.lower() for w in ["how", "what", "can", "is there"]) else "transactional",
        )
        keywords.append(kw)

    # Enrich with Ahrefs if available
    if ahrefs_key:
        _enrich_with_ahrefs(keywords, ahrefs_key)

    # Score all
    for kw in keywords:
        kw.priority_score = score_keyword(kw)

    # Sort by priority
    keywords.sort(key=lambda k: -k.priority_score)
    return keywords


def _enrich_with_ahrefs(keywords: list[Keyword], api_key: str) -> None:
    """Enrich keywords with Ahrefs volume/difficulty data in-place."""
    # Batch by language → country mapping
    lang_country = {
        "en": "us", "ru": "ru", "it": "it", "es": "es",
        "pl": "pl", "pt": "br", "id": "id", "ro": "ro",
    }

    by_lang: dict[str, list[Keyword]] = {}
    for kw in keywords:
        by_lang.setdefault(kw.language, []).append(kw)

    for lang, kws in by_lang.items():
        country = lang_country.get(lang, "us")
        batch = [kw.keyword for kw in kws]

        # Process in batches of 10
        for i in range(0, len(batch), 10):
            chunk = batch[i:i+10]
            try:
                results = fetch_ahrefs_keyword_overview(api_key, chunk, country=country)
                # Map results back to Keyword objects
                result_map = {r.get("keyword", "").lower(): r for r in results}
                for kw in kws[i:i+10]:
                    r = result_map.get(kw.keyword.lower())
                    if r:
                        kw.volume = r.get("volume")
                        kw.difficulty = r.get("difficulty")
                        kw.cpc = r.get("cpc")
            except Exception:
                pass  # Ahrefs unavailable, continue with manual scores


def get_competitor_keywords(
    ahrefs_key: str,
    competitors: Optional[list[str]] = None,
    *,
    country: str = "us",
    limit_per_competitor: int = 50,
) -> list[Keyword]:
    """
    Pull top organic keywords from competitor domains via Ahrefs.
    Returns Keyword objects for keywords Kolo doesn't rank for.
    """
    if competitors is None:
        competitors = COMPETITOR_DOMAINS

    all_kws: dict[str, Keyword] = {}

    for domain in competitors:
        try:
            results = fetch_ahrefs_organic_keywords(
                ahrefs_key, domain, country=country, limit=limit_per_competitor,
            )
            for r in results:
                q = r.get("keyword", "")
                if not q or q.lower() in all_kws:
                    continue
                # Filter: only crypto/card related
                if not any(term in q.lower() for term in ["crypto", "card", "usdt", "visa", "debit", "wallet", "stablecoin", "bitcoin"]):
                    continue
                kw = Keyword(
                    keyword=q,
                    language=detect_language(q),
                    market=detect_market(q),
                    category=classify_keyword(q),
                    volume=r.get("volume"),
                    difficulty=r.get("keyword_difficulty") or r.get("difficulty"),
                    cpc=r.get("cpc"),
                    competitor_domains=[domain],
                )
                all_kws[q.lower()] = kw
        except Exception:
            continue

    keywords = list(all_kws.values())
    for kw in keywords:
        kw.priority_score = score_keyword(kw)
    keywords.sort(key=lambda k: -k.priority_score)
    return keywords


# ── Export helpers ────────────────────────────────────────────────────────────

def taxonomy_to_dicts(keywords: list[Keyword]) -> list[dict]:
    """Convert Keyword list to list of dicts for DataFrame."""
    return [
        {
            "keyword": kw.keyword,
            "language": kw.language,
            "market": kw.market,
            "category": kw.category,
            "intent": kw.intent,
            "volume": kw.volume,
            "difficulty": kw.difficulty,
            "cpc": kw.cpc,
            "ai_overview": kw.has_ai_overview,
            "kolo_ranking": kw.kolo_ranking,
            "ai_kolo_visible": kw.ai_kolo_visible,
            "priority_score": kw.priority_score,
        }
        for kw in keywords
    ]


def filter_keywords(
    keywords: list[Keyword],
    *,
    language: Optional[str] = None,
    market: Optional[str] = None,
    category: Optional[str] = None,
    min_score: float = 0,
) -> list[Keyword]:
    """Filter keywords by criteria."""
    result = keywords
    if language:
        result = [k for k in result if k.language == language]
    if market:
        result = [k for k in result if k.market == market]
    if category:
        result = [k for k in result if k.category == category]
    if min_score > 0:
        result = [k for k in result if k.priority_score >= min_score]
    return result
