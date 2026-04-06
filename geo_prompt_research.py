"""
geo_prompt_research.py — AI Prompt Discovery & GEO Tracking (Semrush-style)
============================================================================
Discovers what prompts real users ask AI about crypto cards, then tracks
whether Kolo appears in AI-generated answers.

Two engines:
  1. Prompt Discovery — uses Claude to generate realistic AI prompts
     that real users would type into ChatGPT/Perplexity/Google AI
  2. Prompt Monitoring — queries Perplexity with each prompt, checks
     Kolo mention/citation, counts brands & sources

Cost: ~$0.003/prompt (Perplexity sonar) + ~$0.001/batch (Claude Haiku for discovery)
"""
from __future__ import annotations

import json
import time
import os
import re
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict

import requests

# ── Constants ────────────────────────────────────────────────────────────────

PERPLEXITY_CHAT_API = "https://api.perplexity.ai/chat/completions"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

KOLO_DOMAINS = {"kolo.in", "kolo.xyz", "kolo.io"}
KOLO_TERMS = {"kolo", "kolo card", "kolo crypto", "kolo visa", "kolo wallet", "kolo.in", "kolo.xyz"}

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
    "redotpay.com": "RedotPay",
    "paywithmoon.com": "Moon",
}

# ── Prompt Discovery Categories ─────────────────────────────────────────────

DISCOVERY_CATEGORIES = {
    "product_comparison": {
        "label": "Product Comparison",
        "description": "Users comparing crypto cards, asking which is best",
        "example": "What's the best crypto Visa card for spending USDT in Europe?",
    },
    "how_to": {
        "label": "How-To / Problem Solving",
        "description": "Users asking how to accomplish something with crypto",
        "example": "How can I spend my TRC20 USDT at regular stores?",
    },
    "geo_specific": {
        "label": "Geo-Specific",
        "description": "Users asking about crypto cards in a specific country/region",
        "example": "Which crypto cards actually work in Italy for daily purchases?",
    },
    "use_case": {
        "label": "Use Case",
        "description": "Specific use cases: travel, freelancing, business expenses",
        "example": "Best crypto card for digital nomads who need to pay in multiple currencies",
    },
    "cost_fees": {
        "label": "Cost & Fees",
        "description": "Users asking about fees, costs, hidden charges",
        "example": "Which crypto card has no monthly fees and lowest conversion rates?",
    },
    "trust_safety": {
        "label": "Trust & Safety",
        "description": "Users asking about security, regulation, legitimacy",
        "example": "Is it safe to use a crypto Visa card? Are they regulated?",
    },
    "onboarding": {
        "label": "Onboarding",
        "description": "Users asking how to get started, sign up, requirements",
        "example": "How do I get a crypto card without extensive KYC?",
    },
    "b2b": {
        "label": "B2B / Business",
        "description": "Business users looking for corporate crypto card solutions",
        "example": "What crypto card can my company use for business travel expenses?",
    },
}

# Markets to generate geo-specific prompts for
TARGET_MARKETS = {
    "UAE": {"langs": ["en", "ru"], "local": "ОАЭ"},
    "UK": {"langs": ["en"], "local": "UK"},
    "Italy": {"langs": ["en", "it"], "local": "Italia"},
    "Spain": {"langs": ["en", "ru", "es"], "local": "España"},
    "Poland": {"langs": ["en", "pl"], "local": "Polska"},
    "Georgia": {"langs": ["en", "ru"], "local": "Грузия"},
    "Cyprus": {"langs": ["en", "ru"], "local": "Кипр"},
    "Germany": {"langs": ["en"], "local": "Deutschland"},
    "Latvia": {"langs": ["en", "ru"], "local": "Латвия"},
    "Romania": {"langs": ["en"], "local": "Romania"},
    "Indonesia": {"langs": ["en"], "local": "Indonesia"},
    "Armenia": {"langs": ["ru"], "local": "Армения"},
    "Uzbekistan": {"langs": ["ru"], "local": "Узбекистан"},
    "Kyrgyzstan": {"langs": ["ru"], "local": "Кыргызстан"},
    "Azerbaijan": {"langs": ["ru"], "local": "Азербайджан"},
}


# ── Pre-built Prompt Database (no API needed) ───────────────────────────────

BUILTIN_PROMPTS = [
    # Product Comparison — EN
    {"prompt": "What are the best crypto debit cards in 2026?", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "Which crypto card has the lowest fees?", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "Best crypto Visa card for spending USDT", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto.com vs wirex vs bybit card comparison", "category": "product_comparison", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "best crypto card with cashback 2026", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "what crypto card gives the best exchange rate", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "cheapest crypto card no monthly fees", "category": "product_comparison", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "compare all crypto visa cards available in europe", "category": "product_comparison", "language": "en", "market": "global", "intent": "informational"},
    # Product Comparison — RU
    {"prompt": "лучшие криптокарты 2026 года", "category": "product_comparison", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "какая крипто карта самая выгодная", "category": "product_comparison", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "сравнение криптокарт visa для USDT", "category": "product_comparison", "language": "ru", "market": "global", "intent": "informational"},
    {"prompt": "криптокарта с кэшбэком в биткоинах", "category": "product_comparison", "language": "ru", "market": "global", "intent": "transactional"},

    # How-To — EN
    {"prompt": "How can I spend TRC20 USDT with a Visa card?", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "how to convert USDT to fiat and spend with a card", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "what's the easiest way to spend cryptocurrency at regular stores", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "I have USDT on Tron and need to pay rent in EUR", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "how to use crypto for everyday purchases without high fees", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "can I pay with USDT at a supermarket", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "how to get a crypto debit card step by step", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "how to top up a crypto card with bitcoin", "category": "how_to", "language": "en", "market": "global", "intent": "informational"},
    # How-To — RU
    {"prompt": "как потратить USDT TRC20 картой Visa", "category": "how_to", "language": "ru", "market": "global", "intent": "informational"},
    {"prompt": "как конвертировать крипту в евро и потратить", "category": "how_to", "language": "ru", "market": "global", "intent": "informational"},
    {"prompt": "как расплатиться криптовалютой в обычном магазине", "category": "how_to", "language": "ru", "market": "global", "intent": "informational"},
    {"prompt": "у меня USDT на трон как проще всего потратить", "category": "how_to", "language": "ru", "market": "global", "intent": "informational"},

    # Geo-Specific — UAE
    {"prompt": "best crypto card for UAE residents 2026", "category": "geo_specific", "language": "en", "market": "UAE", "intent": "transactional"},
    {"prompt": "can I use a crypto visa card in Dubai for daily purchases", "category": "geo_specific", "language": "en", "market": "UAE", "intent": "informational"},
    {"prompt": "crypto card for expats in Dubai", "category": "geo_specific", "language": "en", "market": "UAE", "intent": "transactional"},
    {"prompt": "which crypto cards actually work in UAE", "category": "geo_specific", "language": "en", "market": "UAE", "intent": "transactional"},
    {"prompt": "лучшая крипто карта для ОАЭ", "category": "geo_specific", "language": "ru", "market": "UAE", "intent": "transactional"},
    {"prompt": "какой криптокартой расплачиваться в Дубае", "category": "geo_specific", "language": "ru", "market": "UAE", "intent": "transactional"},
    {"prompt": "крипто карта для экспатов в Дубае 2026", "category": "geo_specific", "language": "ru", "market": "UAE", "intent": "transactional"},
    # Geo-Specific — UK
    {"prompt": "best crypto card UK 2026", "category": "geo_specific", "language": "en", "market": "UK", "intent": "transactional"},
    {"prompt": "crypto visa card for UK residents", "category": "geo_specific", "language": "en", "market": "UK", "intent": "transactional"},
    {"prompt": "which crypto cards work in the UK with GBP", "category": "geo_specific", "language": "en", "market": "UK", "intent": "transactional"},
    {"prompt": "cheapest crypto card in UK compared to banks", "category": "geo_specific", "language": "en", "market": "UK", "intent": "informational"},
    # Geo-Specific — Italy
    {"prompt": "migliore carta crypto in Italia 2026", "category": "geo_specific", "language": "it", "market": "Italy", "intent": "transactional"},
    {"prompt": "carta visa crypto per residenti italiani", "category": "geo_specific", "language": "it", "market": "Italy", "intent": "transactional"},
    {"prompt": "come spendere criptovalute in Italia con commissioni basse", "category": "geo_specific", "language": "it", "market": "Italy", "intent": "informational"},
    {"prompt": "best crypto card for Italy", "category": "geo_specific", "language": "en", "market": "Italy", "intent": "transactional"},
    # Geo-Specific — Spain
    {"prompt": "лучшая криптокарта для жизни в Испании", "category": "geo_specific", "language": "ru", "market": "Spain", "intent": "transactional"},
    {"prompt": "крипто карта для русских в Испании", "category": "geo_specific", "language": "ru", "market": "Spain", "intent": "transactional"},
    {"prompt": "mejor tarjeta crypto en España 2026", "category": "geo_specific", "language": "es", "market": "Spain", "intent": "transactional"},
    {"prompt": "tarjeta visa crypto para residentes españoles", "category": "geo_specific", "language": "es", "market": "Spain", "intent": "transactional"},
    # Geo-Specific — Poland
    {"prompt": "best crypto card Poland 2026", "category": "geo_specific", "language": "en", "market": "Poland", "intent": "transactional"},
    {"prompt": "crypto card for freelancers in Poland", "category": "geo_specific", "language": "en", "market": "Poland", "intent": "transactional"},
    # Geo-Specific — Georgia
    {"prompt": "crypto card for expats in Georgia Tbilisi", "category": "geo_specific", "language": "en", "market": "Georgia", "intent": "transactional"},
    {"prompt": "крипто карта для жизни в Грузии", "category": "geo_specific", "language": "ru", "market": "Georgia", "intent": "transactional"},
    {"prompt": "лучшая криптокарта в Тбилиси 2026", "category": "geo_specific", "language": "ru", "market": "Georgia", "intent": "transactional"},
    # Geo-Specific — CIS
    {"prompt": "крипто карта для Узбекистана", "category": "geo_specific", "language": "ru", "market": "Uzbekistan", "intent": "transactional"},
    {"prompt": "криптокарта visa для Армении", "category": "geo_specific", "language": "ru", "market": "Armenia", "intent": "transactional"},
    {"prompt": "крипто карта в Кыргызстане 2026", "category": "geo_specific", "language": "ru", "market": "Kyrgyzstan", "intent": "transactional"},
    {"prompt": "криптокарта для Азербайджана", "category": "geo_specific", "language": "ru", "market": "Azerbaijan", "intent": "transactional"},
    # Geo-Specific — Cyprus/Latvia
    {"prompt": "крипто карта для жизни на Кипре", "category": "geo_specific", "language": "ru", "market": "Cyprus", "intent": "transactional"},
    {"prompt": "криптокарта visa для Латвии", "category": "geo_specific", "language": "ru", "market": "Latvia", "intent": "transactional"},

    # Use Case — EN
    {"prompt": "best crypto card for digital nomads who travel frequently", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto card for freelancers who get paid in USDT", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "best way to pay for travel with crypto", "category": "use_case", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "can I use a crypto card for subscription payments like Netflix", "category": "use_case", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "crypto card that works with Apple Pay", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto card for online shopping worldwide", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "best crypto card for remote workers paid in stablecoins", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto card I can use to withdraw cash at ATMs", "category": "use_case", "language": "en", "market": "global", "intent": "transactional"},
    # Use Case — RU
    {"prompt": "криптокарта для фрилансера который получает в USDT", "category": "use_case", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "крипто карта для путешествий по Европе", "category": "use_case", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "криптокарта для оплаты подписок и онлайн покупок", "category": "use_case", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "как снять наличные с криптокарты в банкомате", "category": "use_case", "language": "ru", "market": "global", "intent": "informational"},

    # Cost & Fees — EN
    {"prompt": "crypto card with no hidden fees", "category": "cost_fees", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "what are the fees for crypto visa cards", "category": "cost_fees", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "cheapest way to spend crypto with a card", "category": "cost_fees", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "crypto card conversion fees compared", "category": "cost_fees", "language": "en", "market": "global", "intent": "informational"},
    # Cost & Fees — RU
    {"prompt": "криптокарта без скрытых комиссий", "category": "cost_fees", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "какие комиссии у крипто карт visa", "category": "cost_fees", "language": "ru", "market": "global", "intent": "informational"},

    # Trust & Safety — EN
    {"prompt": "is it safe to use a crypto visa card", "category": "trust_safety", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "are crypto debit cards regulated in Europe", "category": "trust_safety", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "can I trust a crypto card with my money", "category": "trust_safety", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "crypto card scams to avoid 2026", "category": "trust_safety", "language": "en", "market": "global", "intent": "informational"},

    # Onboarding — EN
    {"prompt": "how to get a crypto card without KYC", "category": "onboarding", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "fastest crypto card to sign up for", "category": "onboarding", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto card instant virtual card no wait", "category": "onboarding", "language": "en", "market": "global", "intent": "transactional"},
    # Onboarding — RU
    {"prompt": "как получить криптокарту быстро без верификации", "category": "onboarding", "language": "ru", "market": "global", "intent": "informational"},
    {"prompt": "криптокарта с моментальной виртуальной картой", "category": "onboarding", "language": "ru", "market": "global", "intent": "transactional"},

    # B2B — EN
    {"prompt": "best crypto card for business expenses", "category": "b2b", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "corporate crypto spending card for companies", "category": "b2b", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "crypto payment solution for small business in Europe", "category": "b2b", "language": "en", "market": "global", "intent": "transactional"},
    {"prompt": "how to manage corporate crypto spending with visa cards", "category": "b2b", "language": "en", "market": "global", "intent": "informational"},
    {"prompt": "crypto card for paying remote contractors", "category": "b2b", "language": "en", "market": "global", "intent": "transactional"},
    # B2B — RU
    {"prompt": "крипто карта для бизнеса в Европе", "category": "b2b", "language": "ru", "market": "global", "intent": "transactional"},
    {"prompt": "корпоративная криптокарта для компании", "category": "b2b", "language": "ru", "market": "global", "intent": "transactional"},
]


def get_builtin_prompts(
    categories: Optional[List[str]] = None,
    markets: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
) -> List[dict]:
    """Return filtered built-in prompts (no API call needed)."""
    results = BUILTIN_PROMPTS
    if categories:
        results = [p for p in results if p["category"] in categories]
    if markets:
        results = [p for p in results if p["market"] in markets or p["market"] == "global"]
    if languages:
        results = [p for p in results if p["language"] in languages]
    return results


# ── Prompt Discovery via Claude ─────────────────────────────────────────────

DISCOVERY_SYSTEM_PROMPT = """You are an AI prompt researcher. Your job is to generate realistic prompts
that REAL users would type into ChatGPT, Perplexity, or Google AI when looking for crypto card solutions.

Rules:
- Write prompts exactly as a real person would type them — natural, conversational
- Include typos, informal language, incomplete sentences where realistic
- Mix question formats: "What's the best...", "How do I...", "Can I...", "I need a..."
- Include prompts in the specified language
- Each prompt should be distinct in intent — no near-duplicates
- Focus on prompts where a crypto Visa card product COULD be mentioned in the answer
- Think about what problems users are trying to solve, not just product names
- Include some very specific long-tail prompts (these are GEO gold)

Output format: Return ONLY a JSON array of objects, each with:
{"prompt": "...", "category": "...", "language": "...", "market": "...or global", "intent": "informational|transactional|navigational"}

No markdown, no explanation — just the JSON array."""


def discover_prompts_claude(
    api_key: str,
    *,
    categories: Optional[List[str]] = None,
    markets: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    count_per_category: int = 10,
    existing_prompts: Optional[List[str]] = None,
) -> List[dict]:
    """
    Use Claude to generate realistic AI prompts that users would ask
    about crypto cards. Returns list of prompt dicts.
    """
    if categories is None:
        categories = list(DISCOVERY_CATEGORIES.keys())
    if markets is None:
        markets = list(TARGET_MARKETS.keys())[:5]  # Top 5 by default
    if languages is None:
        languages = ["en", "ru"]

    cat_descriptions = "\n".join(
        f"- {k}: {v['description']} (e.g. \"{v['example']}\")"
        for k, v in DISCOVERY_CATEGORIES.items()
        if k in categories
    )

    market_list = ", ".join(markets)
    lang_list = ", ".join(languages)

    dedup_block = ""
    if existing_prompts:
        sample = existing_prompts[:30]
        dedup_block = f"\n\nAVOID duplicating these existing prompts:\n" + "\n".join(f"- {p}" for p in sample)

    user_msg = f"""Generate {count_per_category} realistic AI prompts per category for crypto card products.

Categories:
{cat_descriptions}

Target markets: {market_list}
Languages: {lang_list}
Total prompts needed: ~{count_per_category * len(categories)}

For geo-specific category, generate prompts in LOCAL languages where specified.
For other categories, use the specified languages.

Make prompts natural — the way real people type into ChatGPT or Perplexity.
Include a mix of:
- Short queries ("best crypto card italy")
- Full questions ("What's the best way to spend USDT in Dubai without high fees?")
- Problem statements ("I have USDT on Tron and need to pay rent in EUR")
- Comparison requests ("crypto.com vs wirex vs bybit card which is cheapest")
{dedup_block}

Return ONLY the JSON array."""

    resp = requests.post(
        ANTHROPIC_API,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 4096,
            "system": DISCOVERY_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_msg}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["content"][0]["text"]

    # Parse JSON from response
    try:
        # Try direct parse first
        prompts = json.loads(text)
    except json.JSONDecodeError:
        # Extract JSON array from text
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            prompts = json.loads(match.group())
        else:
            prompts = []

    return prompts


# ── Prompt Monitoring via Perplexity ─────────────────────────────────────────

@dataclass
class PromptResult:
    prompt: str
    category: str
    language: str
    market: str
    intent: str
    # Results
    mentioned: str = "0/1"  # "1/1" if Kolo appears
    kolo_in_text: bool = False
    kolo_in_citations: bool = False
    kolo_visible: bool = False
    brands_count: int = 0
    brands_list: List[str] = field(default_factory=list)
    sources_count: int = 0
    sources_list: List[str] = field(default_factory=list)
    competitors_in_text: List[str] = field(default_factory=list)
    answer_preview: str = ""
    error: Optional[str] = None
    timestamp: str = ""

    def to_dict(self):
        return asdict(self)


def monitor_prompt(
    perplexity_key: str,
    prompt: str,
    *,
    model: str = "sonar",
) -> dict:
    """
    Query Perplexity with a prompt, analyze for Kolo and competitor presence.
    Returns raw analysis dict.
    """
    try:
        resp = requests.post(
            PERPLEXITY_CHAT_API,
            headers={
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Answer concisely with specific product names, companies, and websites. Include pros and cons."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    # Extract answer text
    content = ""
    if data.get("choices"):
        content = data["choices"][0].get("message", {}).get("content", "")
    content_lower = content.lower()

    # Citations
    citations = data.get("citations", [])
    search_results = data.get("search_results", [])
    source_urls = [sr.get("url", "") for sr in search_results]
    all_sources = list(set(citations + source_urls))

    # Kolo detection
    kolo_in_text = any(term in content_lower for term in KOLO_TERMS)
    kolo_in_citations = any(
        any(d in url.lower() for d in KOLO_DOMAINS)
        for url in all_sources
    )

    # Competitor detection
    competitors_in_text = []
    competitors_in_sources = []
    all_brands = []

    for domain, name in COMPETITORS.items():
        in_text = name.lower() in content_lower or domain in content_lower
        in_src = any(domain in url.lower() for url in all_sources)
        if in_text:
            competitors_in_text.append(name)
            all_brands.append(name)
        if in_src and name not in competitors_in_sources:
            competitors_in_sources.append(name)
            if name not in all_brands:
                all_brands.append(name)

    # Add Kolo to brands if present
    if kolo_in_text or kolo_in_citations:
        all_brands.insert(0, "Kolo")

    return {
        "kolo_in_text": kolo_in_text,
        "kolo_in_citations": kolo_in_citations,
        "kolo_visible": kolo_in_text or kolo_in_citations,
        "brands_count": len(all_brands),
        "brands_list": all_brands,
        "sources_count": len(all_sources),
        "sources_list": all_sources,
        "competitors_in_text": competitors_in_text,
        "answer_preview": content[:600],
        "error": None,
    }


def monitor_prompts_batch(
    perplexity_key: str,
    prompts: List[dict],
    *,
    delay: float = 0.5,
    progress_callback=None,
) -> List[PromptResult]:
    """
    Monitor a batch of prompts. Each prompt dict should have:
    {prompt, category, language, market, intent}
    """
    results = []
    total = len(prompts)

    for i, p in enumerate(prompts):
        prompt_text = p.get("prompt", "")
        analysis = monitor_prompt(perplexity_key, prompt_text)

        result = PromptResult(
            prompt=prompt_text,
            category=p.get("category", "unknown"),
            language=p.get("language", "en"),
            market=p.get("market", "global"),
            intent=p.get("intent", "informational"),
            mentioned="1/1" if analysis.get("kolo_visible") else "0/1",
            kolo_in_text=analysis.get("kolo_in_text", False),
            kolo_in_citations=analysis.get("kolo_in_citations", False),
            kolo_visible=analysis.get("kolo_visible", False),
            brands_count=analysis.get("brands_count", 0),
            brands_list=analysis.get("brands_list", []),
            sources_count=analysis.get("sources_count", 0),
            sources_list=analysis.get("sources_list", []),
            competitors_in_text=analysis.get("competitors_in_text", []),
            answer_preview=analysis.get("answer_preview", ""),
            error=analysis.get("error"),
            timestamp=datetime.utcnow().isoformat(),
        )
        results.append(result)

        if progress_callback:
            progress_callback(i + 1, total, result)

        if delay > 0 and i < total - 1:
            time.sleep(delay)

    return results


# ── Analysis & Reporting ─────────────────────────────────────────────────────

def summarize_results(results: List[PromptResult]) -> dict:
    """Semrush-style summary of monitoring results."""
    total = len(results)
    errors = sum(1 for r in results if r.error)
    valid = max(total - errors, 1)

    kolo_visible = sum(1 for r in results if r.kolo_visible)
    kolo_in_text = sum(1 for r in results if r.kolo_in_text)
    kolo_in_citations = sum(1 for r in results if r.kolo_in_citations)

    # Competitor frequency
    comp_counts = {}
    for r in results:
        for c in r.competitors_in_text:
            comp_counts[c] = comp_counts.get(c, 0) + 1

    # By category
    by_category = {}
    for r in results:
        cat = r.category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "visible": 0}
        by_category[cat]["total"] += 1
        if r.kolo_visible:
            by_category[cat]["visible"] += 1

    # By market
    by_market = {}
    for r in results:
        m = r.market
        if m not in by_market:
            by_market[m] = {"total": 0, "visible": 0}
        by_market[m]["total"] += 1
        if r.kolo_visible:
            by_market[m]["visible"] += 1

    # By language
    by_lang = {}
    for r in results:
        lang = r.language
        if lang not in by_lang:
            by_lang[lang] = {"total": 0, "visible": 0}
        by_lang[lang]["total"] += 1
        if r.kolo_visible:
            by_lang[lang]["visible"] += 1

    return {
        "total_prompts": total,
        "errors": errors,
        "kolo_visible": kolo_visible,
        "kolo_visible_pct": round(kolo_visible / valid * 100, 1),
        "kolo_in_text": kolo_in_text,
        "kolo_in_citations": kolo_in_citations,
        "missing": valid - kolo_visible,
        "missing_pct": round((valid - kolo_visible) / valid * 100, 1),
        "top_competitors": sorted(comp_counts.items(), key=lambda x: -x[1])[:10],
        "avg_brands_per_prompt": round(sum(r.brands_count for r in results if not r.error) / valid, 1),
        "avg_sources_per_prompt": round(sum(r.sources_count for r in results if not r.error) / valid, 1),
        "by_category": by_category,
        "by_market": by_market,
        "by_language": by_lang,
    }


def find_opportunities(results: List[PromptResult]) -> List[dict]:
    """
    Find prompts where Kolo is NOT mentioned but competitors ARE.
    These are the best opportunities for GEO improvement.
    """
    opportunities = []
    for r in results:
        if not r.kolo_visible and r.brands_count > 0 and not r.error:
            opportunities.append({
                "prompt": r.prompt,
                "category": r.category,
                "market": r.market,
                "language": r.language,
                "competitors_present": r.competitors_in_text,
                "brands_count": r.brands_count,
                "sources_count": r.sources_count,
                "priority": "high" if r.brands_count >= 3 else "medium",
            })

    # Sort: more competitors = higher priority
    opportunities.sort(key=lambda x: -x["brands_count"])
    return opportunities


# ── Persistence ──────────────────────────────────────────────────────────────

CACHE_DIR = os.path.join(os.path.dirname(__file__), "geo_cache")


def save_results(results: List[PromptResult], filename: Optional[str] = None):
    """Save monitoring results to JSON cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    if filename is None:
        filename = f"geo_monitor_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(CACHE_DIR, filename)
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_results(filename: str) -> List[PromptResult]:
    """Load monitoring results from JSON cache."""
    path = os.path.join(CACHE_DIR, filename)
    with open(path) as f:
        data = json.load(f)
    results = []
    for d in data.get("results", []):
        r = PromptResult(
            prompt=d["prompt"],
            category=d.get("category", ""),
            language=d.get("language", "en"),
            market=d.get("market", "global"),
            intent=d.get("intent", "informational"),
            mentioned=d.get("mentioned", "0/1"),
            kolo_in_text=d.get("kolo_in_text", False),
            kolo_in_citations=d.get("kolo_in_citations", False),
            kolo_visible=d.get("kolo_visible", False),
            brands_count=d.get("brands_count", 0),
            brands_list=d.get("brands_list", []),
            sources_count=d.get("sources_count", 0),
            sources_list=d.get("sources_list", []),
            competitors_in_text=d.get("competitors_in_text", []),
            answer_preview=d.get("answer_preview", ""),
            error=d.get("error"),
            timestamp=d.get("timestamp", ""),
        )
        results.append(r)
    return results


def list_cached_results() -> List[dict]:
    """List all cached result files."""
    if not os.path.exists(CACHE_DIR):
        return []
    files = []
    for f in sorted(os.listdir(CACHE_DIR), reverse=True):
        if f.endswith(".json"):
            path = os.path.join(CACHE_DIR, f)
            try:
                with open(path) as fh:
                    data = json.load(fh)
                files.append({
                    "filename": f,
                    "timestamp": data.get("timestamp", ""),
                    "count": data.get("count", 0),
                })
            except Exception:
                pass
    return files
