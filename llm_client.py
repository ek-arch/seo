"""
llm_client.py — Anthropic Claude API wrapper for Kolo SEO Agent
================================================================
Handles press release generation, translation, and monthly plan
recommendation.  Every other module imports from here rather than
calling the SDK directly.
"""

from __future__ import annotations

import json
import time
from typing import Optional

from anthropic import Anthropic, RateLimitError

# ── Language maps ──────────────────────────────────────────────────────────────

LANG_NAMES: dict[str, str] = {
    "en": "English",
    "ru": "Russian",
    "it": "Italian",
    "es": "Spanish",
    "pl": "Polish",
    "pt": "Brazilian Portuguese",
    "id": "Indonesian",
    "ro": "Romanian",
}

# ── System prompts ─────────────────────────────────────────────────────────────

_SYSTEM_GENERATE = """\
You are a crypto fintech PR writer for Kolo (kolo.in) — a Telegram-based
crypto Visa card & wallet.  Write in *journalistic, third-person* style.

Rules:
- Include at least 3 specific data points or product facts.
- NO marketing fluff or superlatives ("revolutionary", "game-changing").
- Structure: headline → lead paragraph → body (3-5 sections) → boiler-plate.
- Use subheadings (##) for sections.
- Mention USDT/TRC20 top-up, Visa card, Telegram mini-app where relevant.
- Target audience: {audience}.
- Target word count: ~{word_count} words.
- Primary keyword: "{keyword}" — weave it in naturally 3-5 times.
- Output format: Markdown.
"""

_SYSTEM_TRANSLATE = """\
You are a professional translator specialising in crypto/fintech content.
Translate the following press release from English to {target_lang}.

Rules:
- Preserve ALL proper nouns: Kolo, USDT, TRC20, Visa, Telegram, MasterCard.
- Adapt idioms and phrases naturally for the target locale.
- Do NOT add, remove, or editorialize content.
- Maintain the exact same Markdown structure (headings, bullet points).
- Output ONLY the translated text, no commentary.
"""

_SYSTEM_RECOMMEND = """\
You are a data-driven SEO strategist for Kolo (kolo.in), a crypto Visa card.

Given last month's performance data and available publication outlets, recommend
next month's SEO publication plan.

Respond with valid JSON matching this schema:
{{
  "recommended_outlets": [
    {{"outlet": "domain.com", "lang": "en", "price": 100, "rationale": "..."}}
  ],
  "content_angles": [
    {{"title": "...", "lang": "en", "market": "GBR", "keyword": "...", "priority": "High"}}
  ],
  "pillar_budgets": {{"English": 420, "Russian": 500, "Local": 650}},
  "reasoning": "2-3 paragraph analysis of what worked, what didn't, and why this plan is better"
}}

Rules:
- Stay within the provided budget.
- Prioritise languages/outlets that outperformed last month.
- Suggest alternatives for underperformers.
- Use actual ROI data to justify every recommendation.
- Include at least one new outlet not used last month.
"""


# ── Client helper ──────────────────────────────────────────────────────────────

def _client(api_key: str) -> Anthropic:
    return Anthropic(api_key=api_key)


def _call_with_retry(client: Anthropic, *, max_retries: int = 3, **kwargs):
    """Call messages.create with exponential backoff on rate-limit errors."""
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt * 30  # 30s, 60s, 120s
            time.sleep(wait)


# ── Generation ─────────────────────────────────────────────────────────────────

def generate_press_release(
    api_key: str,
    brief: dict,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Generate an English press release from an article brief.

    ``brief`` keys: Title, Lang, Market, KW, Words, Priority, angle (optional),
    hooks (optional).
    """
    audience = f"{brief.get('Market', 'Global')} readers interested in crypto cards"
    system = _SYSTEM_GENERATE.format(
        audience=audience,
        word_count=brief.get("Words", 1200),
        keyword=brief.get("KW", "crypto card"),
    )
    user_msg = (
        f"Write a press release based on this brief:\n\n"
        f"**Title:** {brief['Title']}\n"
        f"**Market:** {brief.get('Market', 'Global')}\n"
        f"**Primary keyword:** {brief.get('KW', '')}\n"
        f"**Word count:** ~{brief.get('Words', 1200)}\n"
    )
    if brief.get("angle"):
        user_msg += f"**Angle:** {brief['angle']}\n"
    if brief.get("hooks"):
        user_msg += f"**Hooks to include:** {brief['hooks']}\n"

    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


# ── Revision ──────────────────────────────────────────────────────────────────

def revise_press_release(
    api_key: str,
    current_draft: str,
    instructions: str,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> str:
    """Revise a press release based on user instructions."""
    system = (
        "You are a crypto fintech PR editor for Kolo (kolo.in). "
        "Revise the press release according to the user's instructions. "
        "Return the FULL revised article in Markdown — not just the changes. "
        "Preserve proper nouns: Kolo, USDT, TRC20, Visa, Telegram."
    )
    user_msg = (
        f"## Current Draft\n\n{current_draft}\n\n---\n\n"
        f"## Revision Instructions\n\n{instructions}"
    )
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.5,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


# ── Translation ────────────────────────────────────────────────────────────────

def translate_press_release(
    api_key: str,
    en_text: str,
    target_lang: str,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> str:
    """Translate an English press release to *target_lang* (e.g. "ru", "it")."""
    lang_name = LANG_NAMES.get(target_lang, target_lang)
    system = _SYSTEM_TRANSLATE.format(target_lang=lang_name)
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": en_text}],
    )
    return resp.content[0].text


# ── Monthly plan recommendation ───────────────────────────────────────────────

def recommend_monthly_plan(
    api_key: str,
    last_month_results: dict,
    available_outlets: list[dict],
    budget: float,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> dict:
    """Analyse last-month performance and recommend next month's plan.

    Returns parsed JSON dict with keys: recommended_outlets,
    content_angles, pillar_budgets, reasoning.
    """
    user_msg = (
        f"## Last Month Results\n```json\n{json.dumps(last_month_results, indent=2, default=str)}\n```\n\n"
        f"## Available Outlets\n```json\n{json.dumps(available_outlets[:60], indent=2, default=str)}\n```\n\n"
        f"## Budget\n${budget:,.0f}\n\n"
        f"Generate the JSON plan."
    )
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.5,
        system=_SYSTEM_RECOMMEND,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = resp.content[0].text
    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]
    return json.loads(raw.strip())
