# X/Twitter Distribution Feature — Implementation Brief for Tron Command Center

> **Purpose:** Give this entire file to Claude Code. It contains everything needed to add a new "X Distribution" page to the **Allbridge x TRON Command Center** Streamlit app (https://tron-command-center.streamlit.app/). The page will: search X/Twitter for tweets matching TRON/bridge/USDT keywords via SerpAPI, generate natural reply comments via Claude API, manage a draft queue, and push results to Google Sheets.

---

## Context: The Existing App

The **Allbridge x TRON Command Center** is a Streamlit app with `st.navigation()` and these existing pages:

| Section | Page | What it does |
|---------|------|-------------|
| STRATEGY | Dashboard | KPIs: 38% Tron volume, $1B+ bridged, SEO rankings, forum posts |
| STRATEGY | Competitors | Fee comparison, bridge ecosystem depth, user paths to Tron |
| STRATEGY | SEO Targets | Keyword opportunities ranked by competition weakness |
| STRATEGY | Hot Trends | Trending topics to ride |
| TARGETS | Twitter Accounts | Tiered target accounts (@trondao, @justinsuntron, ecosystem) |
| TARGETS | Ecosystem | TRON ecosystem projects and integration angles |
| CONTENT | Tweet Drafts | Pre-written tweet threads with Copy buttons (Milestone Pin, @avelykyy, Weekly Templates, News Reactions, Quick Replies) |
| CONTENT | Blog Plan | Blog content calendar |
| CONTENT | Forum & TBL | TronDAO forum + TBL (TRON Builder League) strategy |
| OUTREACH | Shillers Playbook | Target accounts + comment templates by tier + keyword hunting queries |
| OUTREACH | SMM Guide | Weekly Twitter schedule, Reddit plan, Forum plan, Engagement targets, Trend calendar |
| OUTREACH | AMA / Spaces | AMA and Twitter Spaces planning |
| BUILD | Dev Ideas (Fundable) | TRON Builder League project ideas |
| PITCH | (scrolled off) | Pitch-related content |

**Key difference from other apps:** The existing Tron Command Center is entirely **static** — hardcoded data, Copy buttons, no API calls, no AI generation. The new X Distribution page will be the **first dynamic/API-powered page** in the app.

### Brand Context
- **Product:** Allbridge Core (cross-chain bridge, core.allbridge.io)
- **Twitter handle:** @Allbridge_io
- **Founder:** @avelykyy
- **Key narrative:** Allbridge = 38% of all TRON volume, $1B+ USDT bridged. Largest non-EVM bridge to TRON.
- **Competitors:** Symbiosis, Rubic, deBridge, Stargate, Rhino.fi, Defiway
- **Differentiators:** Non-EVM route diversity (Stellar, SUI, Algorand), LP positive slippage, Energy system (cheapest USDT transfers)
- **Ecosystem partners to tag:** @trondao, @justinsuntron, @TRONSCAN_ORG, @defi_sunio, @DeFi_JUST, @TronLinkWallet

### Proven Tweet Formula (from existing app)
> TAG @trondao + SHARE A NUMBER + RIDE A NARRATIVE = 10-25x reach

### Rules of Engagement (from existing Shillers Playbook)
1. Never shill under negative/hack/exploit posts
2. Add value first — data or insight, then mention Allbridge
3. Max 3-4 replies per account per week (don't spam)
4. Always tag @trondao when relevant
5. Match the tone of the original post

---

## What to Build: New "X Distribution" Page

Add a new page under the **OUTREACH** section called **"X Distribution"** with 3 tabs:

1. **Find Tweets** — search X/Twitter for tweets matching TRON/bridge/USDT keywords via SerpAPI
2. **Draft Replies** — fetch tweet context, generate natural replies via Claude API
3. **Queue** — review, edit, revise comments; mark as posted; export CSV; push to Google Sheets

### Where it fits in navigation
```python
# Add to st.navigation() under OUTREACH section, after "Shillers Playbook":
# OUTREACH
#   Shillers Playbook
#   X Distribution    <-- NEW
#   SMM Guide
#   AMA / Spaces
```

---

## New Dependencies to Add

```
# Add to requirements.txt (keep existing deps)
anthropic>=0.40.0
gspread>=6.0.0
google-auth>=2.0.0
```

### New API Keys (add to Streamlit secrets or sidebar)
| Key | Purpose |
|-----|---------|
| `SERPAPI_KEY` | Search X/Twitter via Google (100 free/month at serpapi.com) |
| `ANTHROPIC_API_KEY` | Claude API for comment generation (~$0.01 per batch of 10 comments) |
| `gsheets` | Google Sheets service account JSON (optional, for tracking) |

---

## Implementation: `llm_client.py` — Claude Comment Generator

Create a new file `llm_client.py` (or add to existing if there is one):

### System Prompt (CRITICAL — anti-slop, anti-spam, Allbridge-specific)

```python
_SYSTEM_COMMENT = """\
You are a real DeFi user / bridge power user writing a short, natural reply on Twitter.
You reply from the perspective of someone who uses Allbridge Core for cross-chain transfers.
It must NOT look AI-generated.

CORE RULES:
1. CONTEXT FIRST — READ THE TWEET CAREFULLY. Respond directly to what
   the person is actually discussing. If they're talking about fees, talk fees.
   If about speed, talk speed. If about USDT supply, talk USDT flows.
   Do NOT give a generic bridge answer that ignores the question.
2. RELEVANCE CHECK — If Allbridge does NOT fit the specific discussion
   (e.g. they're comparing L2 bridges and Allbridge isn't one), either
   skip mentioning Allbridge entirely or pivot to a relevant data point.
   Never force Allbridge into a context where it doesn't belong.
3. STYLE (ANTI-SLOP) — write like a real DeFi user, not a marketing bot.
   Simple language. Casual crypto tone. No long explanations.
4. LENGTH — HARD LIMIT: under 240 characters total. 1-2 sentences max.
   Count characters. Short and punchy wins on X.
5. HUMAN SIGNALS — can include "tbh", "ngl", "fwiw", light takes,
   personal experience tone. Light emojis OK (max 1). NO hashtags.
6. DATA-DRIVEN — whenever possible, include a real number from Allbridge:
   "$1B+ bridged to TRON", "38% of Tron volume", "avg transfer $4,259",
   "$5M+ weekly to TRON". Numbers get 10-25x more reach.
7. TAG @trondao — when the conversation is about TRON ecosystem, tag
   @trondao naturally. This amplifies reach significantly.
8. BRAND MENTION — mention "Allbridge" or "Allbridge Core" naturally.
   Don't say "check out" or "you should try". Frame as personal experience:
   "we bridge X weekly through Allbridge Core" or "Allbridge handles this route".
9. ACCURACY — do NOT hallucinate numbers or features. Stick to known facts:
   - $1B+ USDT bridged to TRON all-time
   - 38% of total TRON bridge volume
   - Supports: Ethereum, Solana, BNB Chain, Stellar, SUI, Algorand → TRON
   - Energy system = cheapest USDT transfers on TRON
   - Avg transfer ~$4,259 (serious capital, not retail)
   - Non-EVM routes nobody else offers (Stellar↔TRON, SUI↔TRON, Algorand↔TRON)

BANNED PATTERNS:
- "I've been using X and I love it" (too obvious shill)
- "Check out X!" / "You should try X" (too promotional)
- "Game changer" / "Highly recommend" / "Best thing ever" (slop)
- Starting with "As someone who..." (AI pattern)
- Emoji chains (🚀🔥💯)
- Hashtag spam (#TRON #DeFi #Bridge)
- "Not financial advice" disclaimers

GOOD EXAMPLES:
- "allbridge core handles this route — $1B+ bridged to tron already. @trondao"
- "fwiw we move USDT through allbridge weekly, the energy system makes tron transfers basically free"
- "ngl the stellar→tron route is underrated. allbridge is the only bridge doing non-evm↔tron"
- "38% of tron bridge volume goes through allbridge core. numbers speak"
- "avg transfer is like $4K+ through allbridge to tron. serious capital moving"
"""
```

### Functions

```python
import time
from anthropic import Anthropic, RateLimitError

def _client(api_key: str) -> Anthropic:
    return Anthropic(api_key=api_key)

def _call_with_retry(client: Anthropic, *, max_retries: int = 3, **kwargs):
    """Call messages.create with exponential backoff on rate-limit errors."""
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except RateLimitError:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt * 30  # 30s, 60s, 120s
            time.sleep(wait)

def generate_comment_reply(
    api_key: str,
    post_title: str,
    post_body: str,
    platform: str = "Twitter",
    author: str = "",
    article_url: str = "",
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 100,
) -> str:
    """Generate a natural reply to a tweet (≤240 chars). Returns reply text."""
    system = _SYSTEM_COMMENT
    user_msg = (
        f"Write a helpful reply to this tweet.\n\n"
        f"**Tweet title/text:** {post_title}\n"
    )
    if author:
        user_msg += f"**Author:** {author}\n"
    if post_body:
        user_msg += f"**Tweet body (excerpt):** {post_body[:500]}\n"
    if article_url:
        user_msg += f"**Blog post you can reference (optional):** {article_url}\n"
    user_msg += (
        "\nReply naturally as someone who uses bridges and DeFi daily. "
        "Be genuinely helpful first — mentioning Allbridge should feel natural, not forced."
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

def revise_comment(
    api_key: str,
    current_comment: str,
    instructions: str,
    *,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 256,
) -> str:
    """Revise a tweet reply. Returns ONLY the revised text."""
    system = (
        "You are a text editor. You receive a short tweet reply and revision instructions. "
        "Apply the changes and return ONLY the final revised reply. "
        "RULES: "
        "- Output NOTHING except the revised reply text. "
        "- No preamble, no 'here you go', no explanations. "
        "- Just the raw reply text, ready to copy-paste. "
        "- Keep it under 240 characters."
    )
    user_msg = f"REPLY:\n{current_comment}\n\nCHANGES: {instructions}"
    resp = _call_with_retry(
        _client(api_key),
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text.strip()
```

---

## Implementation: `sheets_client.py` — Google Sheets Integration

```python
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"  # Replace with your actual sheet ID

def _get_client(creds_json: str) -> gspread.Client:
    if isinstance(creds_json, str):
        creds_info = json.loads(creds_json)
    else:
        creds_info = creds_json
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)

def push_comments(creds_json: str, comments: list[dict], sheet_name: str = "X Replies") -> int:
    """
    Append NEW comments to Google Sheet (append-only, never erases).
    Creates sheet tab if missing. Skips duplicates by URL.
    Returns number of NEW rows added.
    """
    gc = _get_client(creds_json)
    spreadsheet = gc.open_by_key(SHEET_ID)

    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
        ws.update("A1:G1", [["Date", "Tweet URL", "Tweet Text", "Author", "Our Reply", "Status", "Keyword"]])
        ws.format("A1:G1", {"textFormat": {"bold": True}})

    existing_urls = set()
    try:
        url_col = ws.col_values(2)
        existing_urls = set(url_col[1:])
    except Exception:
        pass

    today = datetime.date.today().isoformat()
    new_rows = []
    for c in comments:
        url = c.get("url", "")
        if url in existing_urls:
            continue
        new_rows.append([
            today,
            url,
            c.get("title", "")[:100],
            c.get("author", ""),
            c.get("comment", ""),
            c.get("status", "draft"),
            c.get("keyword", ""),
        ])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
    return len(new_rows)
```

---

## Implementation: X Distribution Page (add to `app.py`)

### Search Keywords — TRON/Bridge/USDT specific

These are taken from the existing **Shillers Playbook → Keyword Hunting** tab, adapted for SerpAPI:

```python
TWITTER_QUERIES = [
    # HIGH priority (from existing Keyword Hunting)
    'site:twitter.com OR site:x.com "bridge to tron"',
    'site:twitter.com OR site:x.com "send USDT to tron"',
    'site:twitter.com OR site:x.com "USDT TRC-20" bridge OR transfer OR send',
    # MED priority
    'site:twitter.com OR site:x.com "cheapest way" USDT tron',
    'site:twitter.com OR site:x.com "how to get USDT on tron"',
    'site:twitter.com OR site:x.com tron bridge -from:Allbridge_io',
    # LOW priority (broader ecosystem)
    'site:twitter.com OR site:x.com "cross-chain" tron OR @trondao',
    'site:twitter.com OR site:x.com SunPump OR SunSwap "need USDT"',
    # Additional discovery
    'site:twitter.com OR site:x.com "best tron bridge"',
    'site:twitter.com OR site:x.com "USDT bridge" cheapest fees',
    'site:twitter.com OR site:x.com allbridge tron',
    'site:twitter.com OR site:x.com "bridge USDT" ethereum tron',
]
```

### State Persistence

```python
import json, os
import streamlit as st

_DIST_CACHE = "distribution_cache.json"

def _save_distribution_state():
    state = {
        "fetched_posts": st.session_state.get("fetched_posts", []),
        "comment_queue": st.session_state.get("comment_queue", []),
        "twitter_found": st.session_state.get("twitter_found", []),
    }
    with open(_DIST_CACHE, "w") as f:
        json.dump(state, f, default=str)

def _load_distribution_state():
    if os.path.exists(_DIST_CACHE):
        try:
            with open(_DIST_CACHE) as f:
                state = json.load(f)
            for key in ["fetched_posts", "comment_queue", "twitter_found"]:
                if key in state and key not in st.session_state:
                    st.session_state[key] = state[key]
        except Exception:
            pass
```

### Tab 1: Find Tweets

```python
def _serpapi_search_twitter(custom_q: str, num_q: int, serpapi_key: str) -> list[dict]:
    """Search X/Twitter via SerpAPI Google search. Returns list of tweet dicts."""
    import re
    import requests

    queries = []
    site_prefix = "site:twitter.com OR site:x.com"
    if custom_q:
        queries.append(f"{site_prefix} {custom_q}")
    queries.extend(TWITTER_QUERIES[:num_q])

    all_posts = []
    seen = set()
    progress = st.progress(0)

    for i, q in enumerate(queries):
        try:
            resp = requests.get("https://serpapi.com/search.json", params={
                "api_key": serpapi_key,
                "engine": "google",
                "q": q,
                "num": 10,
                "tbs": "qdr:m3",  # Last 3 months — fresher tweets for engagement
            }, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("organic_results", []):
                    link = item.get("link", "")
                    if link in seen:
                        continue
                    seen.add(link)

                    # Must be an actual tweet URL (not profile/list)
                    m = re.search(r'(?:twitter|x)\.com/(\w+)/status', link)
                    if not m:
                        continue

                    all_posts.append({
                        "title": item.get("title", "")[:120],
                        "author": f"@{m.group(1)}",
                        "snippet": item.get("snippet", "")[:200],
                        "url": link,
                        "platform": "Twitter",
                        "keyword": q.replace("site:twitter.com OR site:x.com ", ""),
                    })
        except Exception:
            pass
        progress.progress((i + 1) / len(queries))

    progress.empty()
    return all_posts[:30]
```

### Tab 1: Display Results + Send to Drafts

```python
def _show_twitter_results():
    """Display found tweets with select checkboxes + send to drafts."""
    found = st.session_state.get("twitter_found", [])
    if not found:
        return

    st.success(f"Found {len(found)} tweets")

    col_sel, col_send = st.columns([3, 2])
    with col_sel:
        if st.button("Select All", key="select_all_tweets"):
            for i in range(len(found)):
                st.session_state[f"tsel_{i}"] = True
            st.rerun()
        if st.button("Deselect All", key="deselect_all_tweets"):
            for i in range(len(found)):
                st.session_state[f"tsel_{i}"] = False
            st.rerun()

    selected_urls = []
    for i, post in enumerate(found):
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{post['title'][:80]}** — {post['author']}")
                if post.get("snippet"):
                    st.caption(post["snippet"][:120] + "...")
            with col2:
                if st.checkbox("Select", key=f"tsel_{i}"):
                    selected_urls.append(post["url"])

    with col_send:
        if st.button(f"Send {len(selected_urls)} to Draft Replies", type="primary",
                     disabled=not selected_urls):
            existing = st.session_state.get("prefilled_urls", "")
            new_urls = "\n".join(selected_urls)
            st.session_state["prefilled_urls"] = (existing + "\n" + new_urls).strip()

            post_cache = st.session_state.get("post_metadata_cache", {})
            for p in found:
                if p["url"] in selected_urls:
                    post_cache[p["url"]] = {
                        "title": p.get("title", ""),
                        "snippet": p.get("snippet", ""),
                        "author": p.get("author", ""),
                        "keyword": p.get("keyword", ""),
                        "platform": "Twitter",
                    }
            st.session_state["post_metadata_cache"] = post_cache
            st.success(f"Added {len(selected_urls)} URLs! Switch to **Draft Replies** tab.")
```

### Tab 2: Fetch Tweet Context

```python
def _fetch_tweet(url: str) -> dict:
    """Fetch tweet context. Uses cached metadata, falls back to SerpAPI lookup."""
    import re
    import requests

    post = {"url": url, "title": "", "body": "", "author": "", "platform": "Twitter", "keyword": ""}

    # Check cached metadata first
    post_cache = st.session_state.get("post_metadata_cache", {})
    if url in post_cache:
        cached = post_cache[url]
        post["title"] = cached.get("title", "")
        post["body"] = cached.get("snippet", "")
        post["author"] = cached.get("author", "")
        post["keyword"] = cached.get("keyword", "")
        if post["title"] and post["body"]:
            return post

    # Extract @username from URL
    m = re.search(r'(?:twitter|x)\.com/(\w+)/status', url)
    post["author"] = f"@{m.group(1)}" if m else ""
    post["title"] = f"Tweet by {post['author']}" if post["author"] else "Tweet"

    # Fallback: SerpAPI Google search for tweet content
    serpapi_key = st.session_state.get("serpapi_key", "")
    if serpapi_key and not post.get("body"):
        try:
            resp = requests.get("https://serpapi.com/search.json", params={
                "api_key": serpapi_key,
                "engine": "google",
                "q": url,
                "num": 1,
            }, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                organic = data.get("organic_results", [])
                if organic:
                    snippet = organic[0].get("snippet", "")
                    title = organic[0].get("title", "")
                    if snippet:
                        post["body"] = snippet[:500]
                        post["title"] = title[:120] if title else post["title"]
        except Exception:
            pass
    return post
```

### Tab 2: Generate All Replies (batch)

```python
def _generate_all_comments(fetched_posts, api_key, ref_url=""):
    """Generate Claude replies for all fetched tweets."""
    from llm_client import generate_comment_reply

    queue = st.session_state.get("comment_queue", [])
    progress = st.progress(0)
    status = st.empty()

    for i, post in enumerate(fetched_posts):
        if any(q["url"] == post["url"] for q in queue):
            progress.progress((i + 1) / len(fetched_posts))
            continue

        status.text(f"Generating reply for: {post['title'][:50]}...")
        try:
            comment = generate_comment_reply(
                api_key,
                post_title=post["title"],
                post_body=post.get("body", ""),
                platform="Twitter",
                author=post.get("author", ""),
                article_url=ref_url,
            )
            queue.append({
                "url": post["url"],
                "title": post["title"],
                "platform": "Twitter",
                "author": post.get("author", ""),
                "comment": comment,
                "status": "draft",
                "keyword": post.get("keyword", ""),
            })
        except Exception as e:
            queue.append({
                "url": post["url"],
                "title": post["title"],
                "platform": "Twitter",
                "author": post.get("author", ""),
                "comment": f"[Error: {e}]",
                "status": "error",
                "keyword": post.get("keyword", ""),
            })
        progress.progress((i + 1) / len(fetched_posts))

    st.session_state["comment_queue"] = queue
    _save_distribution_state()
    status.empty()
    progress.empty()
    return queue
```

### Tab 3: Queue — Review, Edit, Revise, Export, Push to Sheets

```python
# The queue tab displays each reply in an editable card:
#
# For each item in queue:
# 1. Status icon (draft/posted/error) + linked tweet title + @author
# 2. Editable text_area with the generated reply
# 3. Character count (show red if >280)
# 4. Revision input + "Revise" button (calls revise_comment via Claude)
# 5. "Open tweet" link to original
# 6. "Posted" button to mark status
# 7. "Copy" download button
#
# Batch actions at top:
# - "Revise All Drafts" — apply same revision instruction to all drafts
# - Summary metrics: Total | Drafts | Posted
#
# Export section at bottom:
# - "Export All to CSV" button — all comments as CSV
# - "Export Drafts Only" — only draft-status
# - "Push to Google Sheets" button — calls push_comments()
#
# CSV/Sheets columns:
# Date | Tweet URL | Tweet Text | Author | Our Reply | Status | Keyword
```

### Full Page Assembly

```python
def page_x_distribution():
    st.title("X " + "Distribution")  # Use app's red accent style
    st.caption("Find relevant tweets → generate natural replies → track posting → push to Google Sheets")

    # Rules of Engagement reminder (matches existing Shillers Playbook style)
    with st.container(border=True):
        st.markdown("**Rules:** 1. Never shill under negative/hack posts. "
                    "2. Add value first — data, then mention Allbridge. "
                    "3. Max 3-4 replies per account per week. "
                    "4. Tag @trondao when relevant. "
                    "5. Match the original post's tone.")

    _load_distribution_state()

    # API keys from sidebar or secrets
    api_key = st.session_state.get("anthropic_key") or st.secrets.get("ANTHROPIC_API_KEY", "")
    serpapi_key = st.session_state.get("serpapi_key") or st.secrets.get("SERPAPI_KEY", "")

    # Sidebar: API key inputs + optional blog URL
    with st.sidebar:
        st.subheader("X Distribution")
        if not api_key:
            api_key = st.text_input("Anthropic API Key", type="password", key="anthropic_key_input")
            if api_key:
                st.session_state["anthropic_key"] = api_key
        if not serpapi_key:
            serpapi_key = st.text_input("SerpAPI Key", type="password", key="serpapi_key_input")
            if serpapi_key:
                st.session_state["serpapi_key"] = serpapi_key
        ref_url = st.text_input("Blog post URL to reference (optional)",
                                placeholder="https://core.allbridge.io/blog/...")

    tab_search, tab_drafts, tab_tracker = st.tabs(["Find Tweets", "Draft Replies", "Queue"])

    # ── Tab 1: Find Tweets ──
    with tab_search:
        if not serpapi_key:
            st.warning("Add your **SerpAPI key** in the sidebar to search.")

        col1, col2 = st.columns([3, 1])
        with col1:
            twitter_q = st.text_input("Custom search", placeholder='e.g. "bridge USDT to tron"')
        with col2:
            twitter_n = st.number_input("Queries", value=4, min_value=1, max_value=12,
                                         help="1 SerpAPI credit per query")

        if st.button("Search X/Twitter", type="primary", disabled=not serpapi_key):
            results = _serpapi_search_twitter(twitter_q, twitter_n, serpapi_key)
            st.session_state["twitter_found"] = results[:30]
            _save_distribution_state()
            st.rerun()

        _show_twitter_results()

    # ── Tab 2: Draft Replies ──
    with tab_drafts:
        st.subheader("Draft Replies")

        prefilled = st.session_state.get("prefilled_urls", "")
        urls_text = st.text_area("Paste tweet URLs (one per line)", value=prefilled or "",
                                  height=200, placeholder="https://x.com/user/status/123456...")

        col_fetch, col_gen = st.columns(2)
        with col_fetch:
            if st.button("Fetch Tweets", type="primary", disabled=not urls_text.strip()):
                urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip()]
                fetched = [_fetch_tweet(url) for url in urls]
                st.session_state["fetched_posts"] = fetched
                _save_distribution_state()
                st.rerun()

        with col_gen:
            fetched = st.session_state.get("fetched_posts", [])
            if not api_key and fetched:
                st.warning("Add Anthropic API key to generate replies.")
            if st.button("Generate All Replies", type="primary",
                         disabled=not api_key or not fetched):
                _generate_all_comments(fetched, api_key, ref_url)
                st.success("Replies generated! Go to **Queue** tab.")
                st.rerun()

        # Show fetched tweets preview
        fetched = st.session_state.get("fetched_posts", [])
        if fetched:
            st.divider()
            st.markdown(f"### {len(fetched)} tweets fetched")
            for i, post in enumerate(fetched):
                st.markdown(f"{i+1}. **{post['title'][:80]}** — {post.get('author', '')}")

    # ── Tab 3: Queue ──
    with tab_tracker:
        st.subheader("Reply Queue")
        queue = st.session_state.get("comment_queue", [])

        if not queue:
            st.info("No replies yet. Find tweets → Draft replies first.")
        else:
            # Summary row
            total = len(queue)
            posted = sum(1 for q in queue if q["status"] == "posted")
            drafts_count = sum(1 for q in queue if q["status"] == "draft")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", total)
            c2.metric("Drafts", drafts_count)
            c3.metric("Posted", posted)

            # Batch revise
            revise_all_text = st.text_input("Revise all drafts:", placeholder="e.g. shorter, add @trondao tag")
            if st.button("Revise All Drafts", disabled=not api_key or not revise_all_text):
                from llm_client import revise_comment
                drafts = [i for i, q in enumerate(queue) if q["status"] == "draft"]
                progress = st.progress(0)
                for j, idx in enumerate(drafts):
                    try:
                        queue[idx]["comment"] = revise_comment(api_key, queue[idx]["comment"], revise_all_text)
                        st.session_state[f"q_ver_{idx}"] = st.session_state.get(f"q_ver_{idx}", 0) + 1
                    except Exception:
                        pass
                    progress.progress((j + 1) / len(drafts))
                st.session_state["comment_queue"] = queue
                _save_distribution_state()
                progress.empty()
                st.rerun()

            st.divider()

            # Individual comment cards
            for i, item in enumerate(queue):
                with st.container(border=True):
                    icon = {"draft": "📝", "posted": "✅", "error": "❌"}.get(item["status"], "📝")
                    st.markdown(f"{icon} **[{item['title'][:70]}]({item['url']})** — {item.get('author', '')}")

                    ver = st.session_state.get(f"q_ver_{i}", 0)
                    edited = st.text_area("Reply", value=item["comment"], height=100,
                                          key=f"q_comment_{i}_{ver}", label_visibility="collapsed")
                    queue[i]["comment"] = edited

                    # Char count
                    char_count = len(edited)
                    if char_count > 280:
                        st.error(f"{char_count}/280 characters — too long!")
                    else:
                        st.caption(f"{char_count}/280 characters")

                    rev_text = st.text_input("Revise:", placeholder="shorter, more data, add @trondao",
                                             key=f"q_rev_{i}", label_visibility="collapsed")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"[Open tweet]({item['url']})")
                    with col2:
                        if st.button("Revise", key=f"q_rev_btn_{i}", disabled=not api_key or not rev_text):
                            from llm_client import revise_comment
                            try:
                                queue[i]["comment"] = revise_comment(api_key, edited, rev_text)
                                st.session_state[f"q_ver_{i}"] = ver + 1
                                st.session_state["comment_queue"] = queue
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    with col3:
                        if item["status"] != "posted":
                            if st.button("Mark Posted", key=f"q_posted_{i}"):
                                queue[i]["status"] = "posted"
                                st.session_state["comment_queue"] = queue
                                _save_distribution_state()
                                st.rerun()
                    with col4:
                        st.download_button("Copy", data=edited, file_name=f"reply_{i}.txt",
                                           mime="text/plain", key=f"q_dl_{i}")

            st.session_state["comment_queue"] = queue
            _save_distribution_state()

            # ── Export section ──
            st.divider()
            import pandas as pd
            export_rows = []
            for item in queue:
                export_rows.append({
                    "Tweet URL": item["url"],
                    "Tweet Text": item["title"],
                    "Author": item.get("author", ""),
                    "Our Reply": item["comment"],
                    "Status": item["status"],
                    "Keyword": item.get("keyword", ""),
                    "Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                })
            export_df = pd.DataFrame(export_rows)
            csv_data = export_df.to_csv(index=False)

            col_exp1, col_exp2, col_exp3 = st.columns(3)
            with col_exp1:
                st.download_button("Export All CSV", data=csv_data,
                                   file_name=f"x_replies_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv")
            with col_exp2:
                draft_rows = [r for r in export_rows if r["Status"] == "draft"]
                if draft_rows:
                    st.download_button(f"Export {len(draft_rows)} Drafts",
                                       data=pd.DataFrame(draft_rows).to_csv(index=False),
                                       file_name=f"x_drafts_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                       mime="text/csv")
            with col_exp3:
                gsheets_creds = st.session_state.get("gsheets_json") or st.secrets.get("gsheets", "")
                if st.button("Push to Google Sheets", type="primary", disabled=not gsheets_creds):
                    from sheets_client import push_comments
                    try:
                        n = push_comments(gsheets_creds, queue)
                        if n:
                            st.success(f"Pushed {n} new replies to Google Sheets")
                        else:
                            st.info("All replies already in sheet.")
                    except Exception as e:
                        st.error(f"Failed: {e}")
```

---

## Key Design Decisions

1. **SerpAPI Google search, not X API** — Search `site:twitter.com OR site:x.com` via Google. Free (100 credits/month). No X API account needed.

2. **Keywords from existing Shillers Playbook** — The search queries match what's already in the Keyword Hunting tab: "bridge to tron", "send USDT to tron", "USDT TRC-20 bridge", etc.

3. **Character limit = 240 (not 280)** — Leaves room for @mentions and threading. System prompt enforces this.

4. **Data-driven replies** — System prompt encourages including real Allbridge numbers ($1B+, 38%, $4K avg) which get 10-25x reach per existing app's proven formula.

5. **@trondao tagging** — System prompt includes this as a natural amplification strategy, matching the existing SMM Guide.

6. **temperature=0.8 for generation** — High creativity for varied replies. 0.3 for revisions (precise edits).

7. **Local JSON + Google Sheets** — `distribution_cache.json` for session persistence, Google Sheets as permanent record with deduplication.

8. **Tracks which keyword found each tweet** — The "keyword" field flows through search → queue → CSV → Google Sheets so you can measure which queries produce the best engagement.

---

## Optional Enhancement: X MCP Server

For **direct posting** instead of copy-paste, integrate [xdevplatform/xmcp](https://github.com/xdevplatform/xmcp):
- 140+ tools from X API v2 (search, post, reply natively)
- Requires: `X_OAUTH_CONSUMER_KEY`, `X_OAUTH_CONSUMER_SECRET`, `X_BEARER_TOKEN`
- Free tier: 1,500 posts/month
- Would add a "Post Reply" button that posts directly via X API

---

## Quick Start

1. Create `llm_client.py` with `generate_comment_reply()` and `revise_comment()` — copy the Allbridge-specific system prompt exactly
2. Create `sheets_client.py` with `push_comments()` — set your `SHEET_ID`
3. Add `page_x_distribution()` to `app.py` under OUTREACH in `st.navigation()`
4. Add to `requirements.txt`: `anthropic>=0.40.0`, `gspread>=6.0.0`, `google-auth>=2.0.0`
5. Add Streamlit secrets: `SERPAPI_KEY`, `ANTHROPIC_API_KEY`, optionally `gsheets`
6. Test: search → select tweets → fetch → generate → review → push to sheets
