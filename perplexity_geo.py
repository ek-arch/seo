"""
perplexity_geo.py — Perplexity API for GEO (AI citation) visibility
=====================================================================
Sends prompts to Perplexity's sonar model and checks whether Kolo
appears in the AI-generated answer or cited sources.
Cost: ~$0.005/query (sonar model).
"""

from __future__ import annotations

import requests
import time
from typing import Optional

PERPLEXITY_CHAT_API = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_SEARCH_API = "https://api.perplexity.ai/search"

KOLO_DOMAINS = {"kolo.in", "kolo.xyz", "kolo.io"}
KOLO_TERMS = {"kolo", "kolo card", "kolo crypto", "kolo visa", "kolo wallet"}

COMPETITORS = {
    "crypto.com": "Crypto.com",
    "coinbase.com": "Coinbase",
    "binance.com": "Binance",
    "wirex.com": "Wirex",
    "bybit.com": "Bybit",
    "nexo.com": "Nexo",
    "oobit.com": "Oobit",
    "revolut.com": "Revolut",
    "bitget.com": "Bitget",
    "metamask.io": "MetaMask",
    "gnosis-pay.com": "Gnosis Pay",
    "holyheld.com": "Holyheld",
    "club-swan.com": "Club Swan",
}


def query_perplexity(
    api_key: str,
    prompt: str,
    *,
    model: str = "sonar",
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict:
    """Send a prompt to Perplexity chat API and return raw response with citations."""
    resp = requests.post(
        PERPLEXITY_CHAT_API,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Answer concisely. Include specific product names and companies."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def analyze_perplexity_response(response: dict) -> dict:
    """
    Parse Perplexity response for Kolo and competitor presence.
    Returns structured analysis.
    """
    citations = response.get("citations", [])
    content = ""
    if response.get("choices"):
        content = response["choices"][0].get("message", {}).get("content", "")
    content_lower = content.lower()

    # Check Kolo in answer text
    kolo_in_text = any(term in content_lower for term in KOLO_TERMS)

    # Check Kolo in cited sources
    kolo_in_citations = any(
        any(d in url.lower() for d in KOLO_DOMAINS)
        for url in citations
    )

    # Check competitors in text
    competitors_mentioned = []
    for domain, name in COMPETITORS.items():
        if name.lower() in content_lower or domain in content_lower:
            competitors_mentioned.append(name)

    # Check competitors in citations
    competitors_cited = []
    for url in citations:
        url_lower = url.lower()
        for domain, name in COMPETITORS.items():
            if domain in url_lower and name not in competitors_cited:
                competitors_cited.append(name)

    # Check search_results for Kolo (chat API returns these)
    search_results = response.get("search_results", [])
    source_urls = [sr.get("url", "") for sr in search_results]
    kolo_in_search_results = any(
        any(d in url.lower() for d in KOLO_DOMAINS)
        for url in source_urls
    )

    # Usage & cost
    usage = response.get("usage", {})
    cost = usage.get("cost", {})

    return {
        "kolo_in_text": kolo_in_text,
        "kolo_in_citations": kolo_in_citations,
        "kolo_in_search_results": kolo_in_search_results,
        "kolo_visible": kolo_in_text or kolo_in_citations or kolo_in_search_results,
        "competitors_mentioned": competitors_mentioned,
        "competitors_cited": competitors_cited,
        "citations": citations,
        "source_urls": source_urls,
        "citation_count": len(citations),
        "answer_preview": content[:500],
        "tokens_used": usage.get("total_tokens", 0),
        "cost_usd": cost.get("total_cost", 0),
    }


def audit_prompt(api_key: str, prompt: str) -> dict:
    """
    Audit a single prompt: query Perplexity, check Kolo visibility,
    identify competitors. Returns structured result.
    """
    try:
        raw = query_perplexity(api_key, prompt)
        analysis = analyze_perplexity_response(raw)
        return {
            "prompt": prompt,
            "error": None,
            **analysis,
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "error": str(e),
            "kolo_in_text": False,
            "kolo_in_citations": False,
            "kolo_visible": False,
            "competitors_mentioned": [],
            "competitors_cited": [],
            "citations": [],
            "citation_count": 0,
            "answer_preview": "",
            "tokens_used": 0,
        }


def run_geo_audit(
    api_key: str,
    prompts: list[str],
    *,
    delay: float = 0.5,
) -> list[dict]:
    """
    Run GEO visibility audit across multiple prompts.
    Adds a small delay between requests to be polite.
    Cost: ~$0.005 × len(prompts).
    """
    results = []
    for prompt in prompts:
        result = audit_prompt(api_key, prompt)
        results.append(result)
        if delay > 0:
            time.sleep(delay)
    return results


def summarize_geo_audit(results: list[dict]) -> dict:
    """Summarize GEO audit results into metrics."""
    total = len(results)
    errors = sum(1 for r in results if r.get("error"))
    valid = max(total - errors, 1)

    kolo_in_text = sum(1 for r in results if r.get("kolo_in_text"))
    kolo_in_citations = sum(1 for r in results if r.get("kolo_in_citations"))
    kolo_visible = sum(1 for r in results if r.get("kolo_visible"))

    # Competitor frequency in AI answers
    competitor_counts = {}
    for r in results:
        for c in r.get("competitors_mentioned", []):
            competitor_counts[c] = competitor_counts.get(c, 0) + 1

    top_competitors = sorted(competitor_counts.items(), key=lambda x: -x[1])

    # Estimated cost
    total_tokens = sum(r.get("tokens_used", 0) for r in results)
    est_cost = (total - errors) * 0.005 + total_tokens * 0.000001  # search fee + token cost

    return {
        "total_prompts": total,
        "errors": errors,
        "kolo_in_text_count": kolo_in_text,
        "kolo_in_text_pct": round(kolo_in_text / valid * 100, 1),
        "kolo_in_citations_count": kolo_in_citations,
        "kolo_in_citations_pct": round(kolo_in_citations / valid * 100, 1),
        "kolo_visible_count": kolo_visible,
        "kolo_visible_pct": round(kolo_visible / valid * 100, 1),
        "top_competitors_in_ai": top_competitors[:5],
        "estimated_cost_usd": round(est_cost, 3),
    }


# ── Default GEO Prompts ─────────────────────────────────────────────────────
# These are AI-native prompts (how people ask AI, not how they Google)

DEFAULT_GEO_PROMPTS = [
    # Head prompts (high competition, AI definitely answers)
    "What are the best crypto debit cards in 2026?",
    "Which crypto card has the lowest fees?",
    "What is the best way to spend USDT?",

    # Geo-specific (AI gives localized answers)
    "What crypto cards work in Europe?",
    "Best crypto Visa card for UK residents",
    "Which crypto cards can I use in the UAE?",
    "Лучшие крипто карты для оплаты в Европе 2026",  # RU
    "Лучшая USDT карта для ОАЭ",  # RU-ARE
    "Quale carta crypto conviene in Italia?",  # IT

    # Long-tail specific (GEO gold — AI loves answering these)
    "How can I spend TRC20 USDT with a Visa card?",
    "What crypto card gives cashback in Bitcoin?",
    "Is there a crypto card that works in 60 countries?",
    "Best crypto card for digital nomads who travel frequently",
    "How to convert USDT to fiat and spend with a card",

    # Comparison prompts
    "Kolo vs Wirex vs Crypto.com card comparison",
    "What's better for USDT spending: Kolo or Bybit card?",
    "Compare crypto Visa cards for European freelancers",

    # Problem-solving prompts
    "I have USDT on TRC20, what's the easiest way to spend it?",
    "Can I get a crypto card without KYC in Europe?",
    "What's the cheapest way to use cryptocurrency for everyday purchases?",

    # B2B prompts (41% of Kolo spend)
    "Best crypto card for business expenses",
    "How to manage corporate crypto spending with Visa cards",
    "Crypto payment solutions for small businesses in Europe",
]


# ── Geo-Targeted Prompt Templates ────────────────────────────────────────────
# Generate prompts per market — the way real local users ask AI

GEO_MARKETS = {
    "GBR": {"name": "UK",          "lang": "en", "local_name": "United Kingdom", "currency": "GBP"},
    "ARE": {"name": "UAE",          "lang": "en", "local_name": "Dubai / UAE",    "currency": "AED"},
    "ITA": {"name": "Italy",        "lang": "it", "local_name": "Italia",         "currency": "EUR"},
    "ESP": {"name": "Spain",        "lang": "es", "local_name": "España",         "currency": "EUR"},
    "POL": {"name": "Poland",       "lang": "pl", "local_name": "Polska",         "currency": "PLN"},
    "DEU": {"name": "Germany",      "lang": "en", "local_name": "Deutschland",    "currency": "EUR"},
    "IDN": {"name": "Indonesia",    "lang": "en", "local_name": "Indonesia",      "currency": "IDR"},
    "LVA": {"name": "Latvia",       "lang": "en", "local_name": "Latvia",         "currency": "EUR"},
    "ROU": {"name": "Romania",      "lang": "en", "local_name": "Romania",        "currency": "RON"},
    "MNE": {"name": "Montenegro",   "lang": "en", "local_name": "Montenegro",     "currency": "EUR"},
    "GEO": {"name": "Georgia",      "lang": "en", "local_name": "Georgia",        "currency": "GEL"},
    "UZB": {"name": "Uzbekistan",   "lang": "ru", "local_name": "Узбекистан",     "currency": "UZS"},
    "KGZ": {"name": "Kyrgyzstan",   "lang": "ru", "local_name": "Кыргызстан",     "currency": "KGS"},
    "ARM": {"name": "Armenia",      "lang": "ru", "local_name": "Армения",        "currency": "AMD"},
    "CYP": {"name": "Cyprus",       "lang": "en", "local_name": "Cyprus",         "currency": "EUR"},
}

# Templates per category — {market} and {local} get replaced
GEO_PROMPT_TEMPLATES_EN = {
    "head": [
        "Best crypto card in {market} 2026",
        "Best crypto Visa card for {market} residents",
    ],
    "long_tail": [
        "What is the best crypto card for someone living in {market}?",
        "Can I use a USDT Visa card in {market} for daily purchases?",
        "Best way to spend cryptocurrency in {market} with low fees",
        "Crypto card for expats in {market}",
        "Crypto card for freelancers working in {market}",
    ],
    "problem": [
        "I live in {market}, what's the easiest way to spend my USDT?",
        "How to convert crypto to {currency} in {market}?",
        "Which crypto cards actually work in {market} with no hidden fees?",
    ],
    "comparison": [
        "Best crypto cards available in {market} compared",
        "Cheapest crypto card in {market} vs traditional banks",
    ],
    "b2b": [
        "Best crypto card for businesses in {market}",
        "Corporate crypto spending card for {market} companies",
    ],
}

GEO_PROMPT_TEMPLATES_RU = {
    "head": [
        "Лучшая крипто карта в {local} 2026",
        "Лучшая криптокарта Visa для жителей {local}",
    ],
    "long_tail": [
        "Какая крипто карта лучше всего работает в {local}?",
        "Можно ли расплачиваться USDT картой в {local} каждый день?",
        "Лучший способ потратить криптовалюту в {local} с низкими комиссиями",
        "Крипто карта для экспатов в {local}",
        "Крипто карта для фрилансеров в {local}",
    ],
    "problem": [
        "Я живу в {local}, как проще всего потратить USDT?",
        "Как конвертировать крипту в {local}?",
        "Какие крипто карты реально работают в {local} без скрытых комиссий?",
    ],
    "b2b": [
        "Крипто карта для бизнеса в {local}",
        "Корпоративная криптокарта для компаний в {local}",
    ],
}

GEO_PROMPT_TEMPLATES_IT = {
    "head": [
        "Migliore carta crypto in Italia 2026",
        "Carta Visa crypto per residenti italiani",
    ],
    "long_tail": [
        "Qual è la migliore carta crypto per chi vive in Italia?",
        "Si può usare una carta USDT Visa in Italia per acquisti quotidiani?",
        "Come spendere criptovalute in Italia con commissioni basse",
    ],
}

GEO_PROMPT_TEMPLATES_ES = {
    "head": [
        "Mejor tarjeta crypto en España 2026",
        "Tarjeta Visa crypto para residentes españoles",
    ],
    "long_tail": [
        "¿Cuál es la mejor tarjeta crypto para vivir en España?",
        "¿Se puede usar una tarjeta USDT Visa en España para compras diarias?",
        "Cómo gastar criptomonedas en España con comisiones bajas",
    ],
}


def generate_geo_prompts(
    markets: Optional[list[str]] = None,
    *,
    categories: Optional[list[str]] = None,
    include_local_lang: bool = True,
) -> list[dict]:
    """
    Generate geo-targeted prompts for selected markets.
    Returns list of {prompt, market, language, category}.
    """
    if markets is None:
        markets = list(GEO_MARKETS.keys())
    if categories is None:
        categories = ["head", "long_tail", "problem", "comparison", "b2b"]

    results = []

    for market_code in markets:
        info = GEO_MARKETS.get(market_code)
        if not info:
            continue

        # English prompts for all markets
        for cat in categories:
            templates = GEO_PROMPT_TEMPLATES_EN.get(cat, [])
            for tmpl in templates:
                prompt = tmpl.format(
                    market=info["name"],
                    local=info["local_name"],
                    currency=info["currency"],
                )
                results.append({
                    "prompt": prompt,
                    "market": market_code,
                    "language": "en",
                    "category": cat,
                })

        # Local language prompts
        if include_local_lang:
            lang = info["lang"]
            local_templates = {}
            if lang == "ru" or market_code in ("UZB", "KGZ", "ARM", "GEO", "LVA", "MNE", "CYP"):
                local_templates = GEO_PROMPT_TEMPLATES_RU
            elif lang == "it" or market_code == "ITA":
                local_templates = GEO_PROMPT_TEMPLATES_IT
            elif lang == "es" or market_code == "ESP":
                local_templates = GEO_PROMPT_TEMPLATES_ES

            for cat in categories:
                templates = local_templates.get(cat, [])
                for tmpl in templates:
                    prompt = tmpl.format(
                        market=info["name"],
                        local=info["local_name"],
                        currency=info["currency"],
                    )
                    results.append({
                        "prompt": prompt,
                        "market": market_code,
                        "language": lang,
                        "category": cat,
                    })

    return results


def run_geo_market_audit(
    api_key: str,
    markets: list[str],
    *,
    categories: Optional[list[str]] = None,
    include_local_lang: bool = True,
    max_per_market: int = 5,
    delay: float = 0.5,
) -> list[dict]:
    """
    Run geo-targeted AI audit for selected markets.
    Generates prompts per market, queries Perplexity, analyzes results.
    Returns results grouped by market.
    """
    prompts = generate_geo_prompts(
        markets, categories=categories, include_local_lang=include_local_lang,
    )

    # Limit per market
    market_counts: dict[str, int] = {}
    filtered = []
    for p in prompts:
        mc = p["market"]
        if market_counts.get(mc, 0) < max_per_market:
            filtered.append(p)
            market_counts[mc] = market_counts.get(mc, 0) + 1

    results = []
    for p in filtered:
        result = audit_prompt(api_key, p["prompt"])
        result["market"] = p["market"]
        result["language"] = p["language"]
        result["category"] = p["category"]
        results.append(result)
        if delay > 0:
            time.sleep(delay)

    return results


def summarize_by_market(results: list[dict]) -> dict:
    """Summarize geo audit results grouped by market."""
    by_market: dict[str, list] = {}
    for r in results:
        m = r.get("market", "unknown")
        by_market.setdefault(m, []).append(r)

    summaries = {}
    for market, market_results in by_market.items():
        total = len(market_results)
        kolo_visible = sum(1 for r in market_results if r.get("kolo_visible"))
        errors = sum(1 for r in market_results if r.get("error"))

        # Top competitors in this market
        comp_counts: dict[str, int] = {}
        for r in market_results:
            for c in r.get("competitors_mentioned", []):
                comp_counts[c] = comp_counts.get(c, 0) + 1
        top_comps = sorted(comp_counts.items(), key=lambda x: -x[1])

        summaries[market] = {
            "market": market,
            "market_name": GEO_MARKETS.get(market, {}).get("name", market),
            "prompts_tested": total,
            "kolo_visible": kolo_visible,
            "kolo_pct": round(kolo_visible / max(total - errors, 1) * 100, 1),
            "errors": errors,
            "top_competitors": top_comps[:3],
            "results": market_results,
        }

    return summaries
