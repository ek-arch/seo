"""
llm_client.py — Anthropic Claude API wrapper for Kolo SEO & GEO Agent
======================================================================
Handles press release generation (SEO+GEO optimized), translation, and
monthly plan recommendation.  Every other module imports from here rather
than calling the SDK directly.
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
Optimize for both SEO (search engines) and GEO (AI engine citations).

SEO Rules:
- Include at least 3 specific data points or product facts.
- NO marketing fluff or superlatives ("revolutionary", "game-changing").
- Target audience: {audience}.
- Target word count: ~{word_count} words.
- Primary keyword: "{keyword}" — weave it in naturally 3-5 times.

GEO Rules (Generative Engine Optimization):
- Use question-format H2 headers (e.g. "How Does Kolo's Crypto Card Work?").
- Write 3+ quotable stat sentences — clear, self-contained facts with numbers
  that AI engines can extract and cite (e.g. "Kolo supports USDT spending in 99 countries").
- Include a comparison table (Markdown) where relevant — AI engines parse tables well.
- End with an FAQ section (## Frequently Asked Questions) with 3-5 Q&A pairs.
- First paragraph must be entity-rich: [Brand] + [product category] + [key differentiator].

Structure: headline → entity-rich lead → body (3-5 sections with question headers)
→ comparison table (if applicable) → FAQ → boiler-plate.

- Mention USDT/TRC20 top-up, Visa card, Telegram mini-app where relevant.
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
You are a data-driven SEO & GEO strategist for Kolo (kolo.in), a crypto Visa card.

Given last month's performance data and available publication outlets, recommend
next month's SEO + GEO publication plan.

Respond with valid JSON matching this schema:
{{
  "recommended_outlets": [
    {{"outlet": "domain.com", "lang": "en", "price": 100, "rationale": "..."}}
  ],
  "content_angles": [
    {{"title": "...", "lang": "en", "market": "GBR", "keyword": "...", "priority": "High"}}
  ],
  "geo_tactics": [
    {{"query": "best crypto card 2026", "target_article": "...", "optimization": "Add FAQ + comparison table"}}
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
- GEO: Recommend which articles to restructure for AI citability (FAQ sections,
  question headers, stat-dense paragraphs). Identify 3-5 AI queries where Kolo
  should aim to appear in ChatGPT/Perplexity/Google AI Overviews.
- Prefer outlets with higher AI citability (frequently cited by AI engines).
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


# ── Distribution post generation ─────────────────────────────────────────────

_SYSTEM_COMMENT = """\
You are a crypto community member who genuinely uses Kolo (kolo.in) — a
Telegram-based crypto Visa card.  Draft a helpful REPLY / COMMENT on an
existing community post.

Rules:
- Sound like a REAL USER answering a question, NOT a marketer.
- Platform: {platform}
- First ANSWER the person's question with useful information.
- Then mention Kolo naturally as ONE option among others (not the only one).
- No affiliate links or shilling language.  No "check out" or "you should try".
- Include a specific personal detail (country, use case, amount range).
- If the post has a URL you want to reference, weave it in naturally.
- Reddit comment: 30-60 words MAX, casual, one short paragraph.
- Quora answer: 60-100 words MAX, concise and direct.
- HN comment: 20-40 words MAX, technical and terse.
- Twitter/X reply: 15-30 words MAX, degen CT (crypto twitter) tone.
  Use lowercase, abbreviations, slang. Like "been using kolo via tg,
  loads usdt and works everywhere. no kyc hassle. dyor tho"
- Forum reply: 30-50 words MAX, brief helpful reply.
- CRITICAL: Keep it SHORT. Real users don't write essays in comments.
- Output: plain text (no Markdown headers), ready to paste.
"""


def generate_comment_reply(
    api_key: str,
    post_title: str,
    post_body: str,
    platform: str,
    subreddit: str = "",
    article_url: str = "",
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
) -> str:
    """Generate a natural comment/reply to an existing community post."""
    system = _SYSTEM_COMMENT.format(platform=platform)
    user_msg = (
        f"Write a helpful reply to this {platform} post.\n\n"
        f"**Post title:** {post_title}\n"
    )
    if subreddit:
        user_msg += f"**Community:** {subreddit}\n"
    if post_body:
        user_msg += f"**Post body (excerpt):** {post_body[:500]}\n"
    if article_url:
        user_msg += f"**Article you can reference (optional):** {article_url}\n"
    user_msg += (
        "\nReply naturally as someone who has experience with crypto cards. "
        "Be genuinely helpful first — mentioning Kolo should feel incidental."
    )
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.8,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text
