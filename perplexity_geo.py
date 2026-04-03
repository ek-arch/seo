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
