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
You are a senior SEO and GEO (Generative Engine Optimization) content writer
specializing in fintech and crypto. Write a high-quality, non-generic article
for guest posting on external media websites.

IMPORTANT: The article must NOT look AI-generated or generic. Avoid fluff,
avoid overused phrases, and avoid repetitive structure. The content must feel
natural, useful, and written for real users.

Target audience: {audience}.
Target length: 2500-3000 characters (strict — do not exceed).
Primary keyword: "{keyword}" — weave in naturally 3-5 times.

=== STYLE RULES (ANTI-SLOP) ===
- No generic intros like "In today's rapidly evolving…"
- No filler sentences
- Use clear, simple, human language
- Vary sentence length and structure
- Avoid repeating patterns across sections
- Each section must add real value

=== STRUCTURE ===
1. Title (SEO-optimized, includes keyword, natural)
2. Short intro (2-3 sentences, clear and direct)
3. Section: What is [topic] — clear definition in 2-4 sentences, easy to quote by AI
4. Section: How it works / Why it matters — simple explanation, practical context
5. Section: What to look for / Comparison — bullet points, real decision factors
   (fees, usability, geography). Include a Markdown comparison table.
6. Section: Practical option — introduce Kolo naturally, explain use case (not hype),
   mention kolo.xyz 1-2 times
7. Section: Common mistakes — 3-5 short bullet points
8. Conclusion — summarize without repeating, reinforce decision-making

=== SEO REQUIREMENTS ===
- Include the main keyword naturally 3-5 times
- Add 2-3 variations of the keyword
- Avoid keyword stuffing

=== GEO REQUIREMENTS (AI engine citations) ===
- Question-format H2 headers (AI engines extract these)
- 3+ quotable stat sentences — self-contained facts with numbers
- Comparison table (AI engines parse tables well)
- FAQ section (3-5 Q&A pairs) — directly answers AI queries
- Entity-rich first paragraph: [Brand] + [product category] + [key differentiator]
- Adapt to region (currency, usage, behavior)

=== BRAND INTEGRATION RULES ===
- Do NOT oversell Kolo. Do NOT claim "best" without comparison.
- Position it as "one of the simple/practical options"
- Journalistic, third-person style ("Kolo offers..." not "We offer...")

=== KOLO FACTS (use relevant ones) ===
- Telegram mini-app — no separate app download
- USDT top-up via TRC20 (fast, cheap)
- Virtual + physical Visa cards
- Works in 60+ countries
- Competitive swap fees
- BTC cashback program
- B2B cards for businesses
- Website: kolo.xyz

=== COMPETITORS (mention fairly) ===
- Crypto.com Card, Coinbase Card, Binance Card
- Wirex, Bybit Card, Nexo Card, Oobit (UAE), Revolut (EU)

Output format: Plain text with simple formatting (no Markdown syntax like #, **, ```, etc.).
Use ALL CAPS for headings. Use dashes for bullet points. Clean, ready to copy-paste into
any CMS or Google Doc. No explanations.
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


# ── Comment Revision ─────────────────────────────────────────────────────────

def revise_comment(
    api_key: str,
    current_comment: str,
    instructions: str,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 256,
) -> str:
    """Revise a social media comment. Returns ONLY the revised text."""
    system = (
        "You are a text editor. You receive a short comment and revision instructions. "
        "Apply the changes and return ONLY the final revised comment. "
        "RULES: "
        "- Output NOTHING except the revised comment text. "
        "- No preamble, no 'here you go', no explanations, no questions. "
        "- No 'sure', 'got it', 'here is'. "
        "- Just the raw comment text, ready to copy-paste. "
        "- Keep it short (1-3 sentences max)."
    )
    user_msg = f"COMMENT:\n{current_comment}\n\nCHANGES: {instructions}"
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text.strip()


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
You are a real crypto user writing a short, natural comment on {platform}.
It must NOT look AI-generated.

CORE RULES:
1. CONTEXT FIRST — READ THE POST CAREFULLY. Respond directly to what
   the person is actually asking about. If they ask about non-KYC cards,
   talk about non-KYC options. If they ask about fees, talk about fees.
   Do NOT give a generic "crypto card" answer that ignores the question.
2. RELEVANCE CHECK — If Kolo does NOT fit the specific request (e.g.
   they want non-KYC but Kolo requires KYC), either skip mentioning Kolo
   entirely or be honest ("kolo needs basic kyc but it's quick via telegram").
   Never force Kolo into a context where it doesn't belong.
3. STYLE (ANTI-SLOP) — write like a real person, not an article. Simple
   language. Vary tone. No long explanations.
4. LENGTH — HARD LIMIT: under 200 characters total. 1-2 sentences max.
   Count characters. If you can say it in 10 words, don't use 20.
5. HUMAN SIGNALS — can include hesitation ("tbh", "idk", "kinda"), light
   opinion, small personal tone. Avoid emojis unless natural. NO hashtags.
6. HUMOR — light, subtle, not forced. Slight degen crypto tone is OK.
   Never cringe or spammy.
7. BRAND MENTION — mention Kolo ONLY if it genuinely fits the question.
   Do NOT promote aggressively. If Kolo doesn't match what the person
   needs, recommend other products instead and skip Kolo entirely.
   When mentioning Kolo, keep it vague and general — just say "kolo"
   or "kolo card". Do NOT mention specific features like "Telegram
   mini-app", "TRC20", "USDT top-up", or technical details. Just
   treat it as a card you've been using. Example: "been using kolo
   lately, works fine for daily stuff"
8. ACCURACY — do not hallucinate facts. If unsure, keep it general.
   Do NOT claim Kolo has features it doesn't have.

PLATFORM TONE:
- Reddit: slightly skeptical, honest, grounded, no hype
- Twitter/X: short, punchy, slight attitude, degen CT tone, lowercase,
  abbreviations, slang. Like "been using kolo for a while now, works
  fine for daily spending. dyor tho"
- Quora: slightly more structured, still human, not formal

OUTPUT: Return ONLY the comment. No explanations. Plain text, ready to paste.
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
    max_tokens: int = 80,
) -> str:
    """Generate a natural comment/reply to an existing community post (≤200 chars)."""
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
