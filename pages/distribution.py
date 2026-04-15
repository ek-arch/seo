"""Page 9 — Social Listening & Distribution: find posts, draft comments, track posting."""
from __future__ import annotations

import json
import os
import re
import streamlit as st
import pandas as pd
import requests

from config import PLATFORM_QUERIES, DISTRIBUTION_CACHE
from llm_client import generate_comment_reply, revise_comment

try:
    from sheets_client import push_comments
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    def push_comments(*a, **kw): return 0


# ── Persistence helpers ───────────────────────────────────────────────────────

def _save_distribution_state():
    state = {
        "fetched_posts": st.session_state.get("fetched_posts", []),
        "comment_queue": st.session_state.get("comment_queue", []),
        "reddit_found": st.session_state.get("reddit_found", []),
    }
    with open(DISTRIBUTION_CACHE, "w") as f:
        json.dump(state, f, default=str)


def _load_distribution_state():
    if os.path.exists(DISTRIBUTION_CACHE):
        try:
            with open(DISTRIBUTION_CACHE) as f:
                state = json.load(f)
            for key in ["fetched_posts", "comment_queue", "reddit_found"]:
                if key in state and key not in st.session_state:
                    st.session_state[key] = state[key]
        except Exception:
            pass


# ── Post fetcher ──────────────────────────────────────────────────────────────

def _fetch_post(url: str) -> dict:
    """Fetch a post's title and body. Supports Reddit, Quora, Twitter."""
    post = {"url": url, "title": "", "body": "", "subreddit": "", "platform": "Reddit", "score": 0, "num_comments": 0}

    # Check cached metadata from Find Posts
    post_cache = st.session_state.get("post_metadata_cache", {})
    if url in post_cache:
        cached = post_cache[url]
        post["platform"] = cached.get("platform", post["platform"])
        post["title"] = cached.get("title", "") or post["title"]
        post["body"] = cached.get("snippet", "") or ""
        post["subreddit"] = cached.get("community", "") or ""
        if post["title"] and post["body"]:
            return post

    # Quora
    if "quora.com" in url:
        post["platform"] = "Quora"
        if not post["title"]:
            slug = url.split("/")[-1]
            slug = re.sub(r'^https?-www-quora-com-', '', slug)
            slug = re.sub(r'-\d+$', '', slug)
            slug = re.sub(r'-answer-[\w-]+$', '', slug)
            post["title"] = slug.replace("-", " ").strip() or "Quora question"
        return post

    # Twitter / X
    if "twitter.com" in url or "x.com" in url:
        post["platform"] = "Twitter"
        m = re.search(r'(?:twitter|x)\.com/(\w+)/status', url)
        post["subreddit"] = f"@{m.group(1)}" if m else ""
        post["title"] = f"Tweet by {post['subreddit']}" if post["subreddit"] else "Tweet"
        serpapi_key = st.session_state.get("serpapi_key", "")
        if serpapi_key and not post.get("body"):
            try:
                resp = requests.get("https://serpapi.com/search.json", params={
                    "api_key": serpapi_key, "engine": "google", "q": f"{url}", "num": 1,
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

    # HackerNews
    if "news.ycombinator" in url:
        post["platform"] = "HackerNews"
        post["title"] = "HN discussion"
        return post

    # Reddit
    reddit_match = re.search(r'reddit\.com/r/(\w+)', url)
    if reddit_match:
        post["subreddit"] = reddit_match.group(1)
        try:
            json_url = url.rstrip("/") + ".json"
            resp = requests.get(json_url, headers={"User-Agent": "KoloSEOAgent/1.0"}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    rd = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
                    post["title"] = rd.get("title", "")
                    post["body"] = (rd.get("selftext", "") or "")[:500]
                    post["score"] = rd.get("score", 0)
                    post["num_comments"] = rd.get("num_comments", 0)
                    post["archived"] = rd.get("archived", False) or rd.get("locked", False)
        except Exception:
            pass

    # Fallback title from URL slug
    if not post["title"]:
        slug_match = re.search(r'/comments/\w+/([^/]+)', url)
        if slug_match:
            post["title"] = slug_match.group(1).replace("_", " ")
        else:
            post["title"] = url.split("/")[-1].replace("_", " ").replace("-", " ")
    return post


# ── SerpAPI search helper ─────────────────────────────────────────────────────

def _serpapi_search(platform: str, custom_q: str, num_q: int, state_key: str):
    serpapi_key = st.session_state.get("serpapi_key", "")
    site_prefix = {"Reddit": "site:reddit.com", "Quora": "site:quora.com", "Twitter": "site:twitter.com OR site:x.com"}[platform]
    queries = []
    if custom_q:
        queries.append(f"{site_prefix} {custom_q}")
    queries.extend(PLATFORM_QUERIES[platform][:num_q])

    all_posts = []
    seen = set()
    progress = st.progress(0)

    for i, q in enumerate(queries):
        try:
            resp = requests.get("https://serpapi.com/search.json", params={
                "api_key": serpapi_key, "engine": "google", "q": q, "num": 10, "tbs": "qdr:m6",
            }, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("organic_results", []):
                    link = item.get("link", "")
                    if link in seen:
                        continue
                    seen.add(link)
                    community = ""
                    if platform == "Reddit":
                        m = re.search(r'reddit\.com/r/(\w+)', link)
                        community = f"r/{m.group(1)}" if m else ""
                        if not m or "/comments/" not in link:
                            continue
                    elif platform == "Quora":
                        community = "Quora"
                    elif platform == "Twitter":
                        m = re.search(r'(?:twitter|x)\.com/(\w+)/status', link)
                        community = f"@{m.group(1)}" if m else ""
                        if not m:
                            continue
                    all_posts.append({
                        "title": item.get("title", "")[:120],
                        "community": community,
                        "snippet": item.get("snippet", "")[:200],
                        "url": link,
                        "platform": platform,
                    })
        except Exception:
            pass
        progress.progress((i + 1) / len(queries))

    st.session_state[state_key] = all_posts[:30]
    _save_distribution_state()
    progress.empty()
    return all_posts


def _show_results(state_key: str, platform: str, prefix: str):
    found = st.session_state.get(state_key, [])
    if not found:
        return

    st.success(f"Found {len(found)} {platform} posts")
    col_sel, col_send = st.columns([3, 2])
    with col_sel:
        if st.button("✅ Select All", key=f"select_all_btn_{prefix}"):
            for i in range(len(found)):
                st.session_state[f"{prefix}_{i}"] = True
            st.rerun()
        if st.button("❌ Deselect All", key=f"deselect_all_btn_{prefix}"):
            for i in range(len(found)):
                st.session_state[f"{prefix}_{i}"] = False
            st.rerun()

    selected_urls = []
    for i, post in enumerate(found):
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{post['title'][:80]}** — {post.get('community', post.get('subreddit', ''))}")
                if post.get("snippet"):
                    st.caption(post["snippet"][:120] + "...")
            with col2:
                if st.checkbox("Select", key=f"{prefix}_{i}"):
                    selected_urls.append(post["url"])

    with col_send:
        if st.button(f"📋 Send {len(selected_urls)} to Draft Comments", type="primary", key=f"send_{prefix}", disabled=not selected_urls):
            existing = st.session_state.get("prefilled_urls", "")
            new_urls = "\n".join(selected_urls)
            st.session_state["prefilled_urls"] = (existing + "\n" + new_urls).strip()
            post_cache = st.session_state.get("post_metadata_cache", {})
            for p in found:
                if p["url"] in selected_urls:
                    post_cache[p["url"]] = {
                        "title": p.get("title", ""), "snippet": p.get("snippet", ""),
                        "community": p.get("community", ""), "platform": platform,
                    }
            st.session_state["post_metadata_cache"] = post_cache
            st.success(f"Added {len(selected_urls)} URLs! Switch to **Draft Comments** tab.")


# ── Main Page ─────────────────────────────────────────────────────────────────

def page_content_distribution():
    st.title("📣 Stage 9 · Social Listening & Distribution")
    st.caption("Find relevant Reddit & Quora posts → draft helpful comments → track posting")

    with st.expander("ℹ️ How distribution works", expanded=False):
        st.markdown("""
**3-step social distribution flow:**
1. **Find Posts** — uses SerpAPI to search Reddit, Quora, and Twitter/X for posts mentioning crypto cards
2. **Draft Comments** — Claude AI generates helpful, non-promotional replies that naturally mention Kolo
3. **Queue & Track** — manage drafted comments, mark as posted, track engagement

**Why:** Social comments on high-traffic threads = free backlinks + referral traffic + signals to AI engines that Kolo is a real product people discuss.
""")

    _load_distribution_state()
    api_key = st.session_state.get("anthropic_token")
    serpapi_key = st.session_state.get("serpapi_key", "")

    # Sidebar ref URL
    st.sidebar.divider()
    st.sidebar.subheader("📣 Distribution")
    ref_url = st.sidebar.text_input("Article URL to reference (optional)", placeholder="https://...", key="dist_ref_url")

    tab_search, tab_drafts, tab_tracker = st.tabs(["🔍 Find Posts", "✏️ Draft Comments", "📋 Queue"])

    # ── Tab 0: Find Posts ──────────────────────────────────────────
    with tab_search:
        if not serpapi_key:
            st.warning("Add your **SerpAPI key** in the sidebar to search.")

        plat_reddit, plat_quora, plat_twitter = st.tabs(["🔴 Reddit", "🔵 Quora", "🐦 Twitter / X"])

        with plat_reddit:
            st.subheader("Find Reddit Posts")
            col1, col2 = st.columns([3, 1])
            with col1:
                reddit_q = st.text_input("Custom search", placeholder="e.g. spend USDT abroad", key="reddit_q")
            with col2:
                reddit_n = st.number_input("Queries", value=3, min_value=1, max_value=8, key="reddit_n", help="1 SerpAPI credit per query")
            if st.button("🔍 Search Reddit", type="primary", disabled=not serpapi_key, key="btn_reddit"):
                results = _serpapi_search("Reddit", reddit_q, reddit_n, "reddit_found")
                st.success(f"Found {len(results)} Reddit posts")
                st.rerun()
            _show_results("reddit_found", "Reddit", "rsel")

        with plat_quora:
            st.subheader("Find Quora Questions")
            col1, col2 = st.columns([3, 1])
            with col1:
                quora_q = st.text_input("Custom search", placeholder="e.g. crypto card for travel", key="quora_q")
            with col2:
                quora_n = st.number_input("Queries", value=3, min_value=1, max_value=8, key="quora_n", help="1 SerpAPI credit per query")
            if st.button("🔍 Search Quora", type="primary", disabled=not serpapi_key, key="btn_quora"):
                results = _serpapi_search("Quora", quora_q, quora_n, "quora_found")
                st.success(f"Found {len(results)} Quora questions")
                st.rerun()
            _show_results("quora_found", "Quora", "qsel")

        with plat_twitter:
            st.subheader("Find Twitter / X Posts")
            col1, col2 = st.columns([3, 1])
            with col1:
                twitter_q = st.text_input("Custom search", placeholder="e.g. crypto card review", key="twitter_q")
            with col2:
                twitter_n = st.number_input("Queries", value=3, min_value=1, max_value=6, key="twitter_n", help="1 SerpAPI credit per query")
            if st.button("🔍 Search Twitter", type="primary", disabled=not serpapi_key, key="btn_twitter"):
                results = _serpapi_search("Twitter", twitter_q, twitter_n, "twitter_found")
                st.success(f"Found {len(results)} tweets")
                st.rerun()
            _show_results("twitter_found", "Twitter", "tsel")

    # ── Tab 1: Draft Comments ──────────────────────────────────────
    with tab_drafts:
        st.subheader("Draft Comments")
        st.markdown("Paste Reddit/Quora URLs → fetch → generate comments → all go to the Queue.")

        prefilled = st.session_state.get("prefilled_urls", "")
        if prefilled and "bulk_urls_ver" not in st.session_state:
            st.session_state["bulk_urls_ver"] = 0
        if prefilled:
            st.session_state["bulk_urls_ver"] = st.session_state.get("bulk_urls_ver", 0) + 1
            st.session_state.pop("prefilled_urls", None)

        url_ver = st.session_state.get("bulk_urls_ver", 0)
        urls_text = st.text_area(
            "Paste post URLs (one per line)",
            value=prefilled if prefilled else "",
            height=200,
            placeholder="https://www.reddit.com/r/cryptocurrency/comments/abc123/which_crypto_card_do_you_use/\nhttps://www.quora.com/What-is-the-best-crypto-debit-card-in-2026",
            key=f"bulk_urls_{url_ver}",
        )

        col_fetch, col_gen = st.columns(2)
        with col_fetch:
            if st.button("📥 Fetch Posts", type="primary", disabled=not urls_text.strip()):
                urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip()]
                fetched = []
                progress = st.progress(0)
                for i, url in enumerate(urls):
                    fetched.append(_fetch_post(url))
                    progress.progress((i + 1) / len(urls))
                st.session_state["fetched_posts"] = fetched
                _save_distribution_state()
                progress.empty()
                st.rerun()

        with col_gen:
            fetched = st.session_state.get("fetched_posts", [])
            if not api_key and fetched:
                st.warning("Add Anthropic API key to generate.")
            if st.button("🤖 Generate All Comments", type="primary", disabled=not api_key or not fetched):
                queue = st.session_state.get("comment_queue", [])
                progress = st.progress(0)
                status = st.empty()
                for i, post in enumerate(fetched):
                    if post.get("archived"):
                        progress.progress((i + 1) / len(fetched))
                        continue
                    if any(q["url"] == post["url"] for q in queue):
                        progress.progress((i + 1) / len(fetched))
                        continue
                    status.text(f"Generating comment for: {post['title'][:50]}...")
                    try:
                        comment = generate_comment_reply(
                            api_key, post_title=post["title"], post_body=post.get("body", ""),
                            platform=post["platform"], subreddit=post.get("subreddit", ""),
                            article_url=ref_url,
                        )
                        queue.append({
                            "url": post["url"], "title": post["title"], "platform": post["platform"],
                            "subreddit": post.get("subreddit", ""), "comment": comment, "status": "draft",
                        })
                    except Exception as e:
                        queue.append({
                            "url": post["url"], "title": post["title"], "platform": post["platform"],
                            "subreddit": post.get("subreddit", ""), "comment": f"[Error: {e}]", "status": "error",
                        })
                    progress.progress((i + 1) / len(fetched))
                st.session_state["comment_queue"] = queue
                _save_distribution_state()
                status.empty()
                progress.empty()
                st.success(f"Generated {len(fetched)} comments! Go to **Queue** tab.")
                st.rerun()

        # Show fetched posts preview
        fetched = st.session_state.get("fetched_posts", [])
        if fetched:
            st.divider()
            st.markdown(f"### ✅ {len(fetched)} posts fetched — click **Generate All Comments** to draft replies")
            archived_count = sum(1 for p in fetched if p.get("archived"))
            if archived_count:
                st.warning(f"⚠️ {archived_count} posts are archived/locked and will be skipped.")
            for i, post in enumerate(fetched):
                sub = f"r/{post['subreddit']}" if post["subreddit"] else post["platform"]
                score = f" · ⬆️ {post['score']} · 💬 {post['num_comments']}" if post.get("score") else ""
                archived = " · 🔒 **ARCHIVED**" if post.get("archived") else ""
                st.markdown(f"{i+1}. {'~~' if post.get('archived') else ''}**{post['title'][:80]}**{'~~' if post.get('archived') else ''} — {sub}{score}{archived}")

            queue = st.session_state.get("comment_queue", [])
            if queue:
                st.success(f"💬 {len(queue)} comments generated! Switch to the **Queue** tab to review and post.")

    # ── Tab 2: Queue ──────────────────────────────────────────────
    with tab_tracker:
        st.subheader("Comment Queue")
        st.markdown("All generated comments in one place. Edit, revise, then copy & post.")

        queue = st.session_state.get("comment_queue", [])

        col_clear1, col_clear2 = st.columns([6, 1])
        with col_clear2:
            if st.button("🗑️ Clear All", type="secondary"):
                st.session_state["comment_queue"] = []
                st.session_state.pop("fetched_posts", None)
                _save_distribution_state()
                st.rerun()

        if not queue:
            st.info("No comments yet. Paste URLs in **Draft Comments** tab → Fetch → Generate All.")
        else:
            total = len(queue)
            posted = sum(1 for q in queue if q["status"] == "posted")
            drafts_count = sum(1 for q in queue if q["status"] == "draft")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", total)
            c2.metric("Drafts", drafts_count)
            c3.metric("Posted", posted)

            with c4:
                revise_all_text = st.text_input("Revise all drafts:", placeholder="e.g. make shorter", key="revise_all_input", label_visibility="collapsed")
            if st.button("✏️ Revise All Drafts", type="primary", disabled=not api_key or not revise_all_text):
                drafts_to_revise = [i for i, q in enumerate(queue) if q["status"] == "draft"]
                if drafts_to_revise:
                    progress = st.progress(0)
                    for j, idx in enumerate(drafts_to_revise):
                        try:
                            revised = revise_comment(api_key, current_comment=queue[idx]["comment"], instructions=revise_all_text)
                            queue[idx]["comment"] = revised
                            st.session_state[f"q_ver_{idx}"] = st.session_state.get(f"q_ver_{idx}", 0) + 1
                        except Exception:
                            pass
                        progress.progress((j + 1) / len(drafts_to_revise))
                    st.session_state["comment_queue"] = queue
                    _save_distribution_state()
                    progress.empty()
                    st.success(f"Revised {len(drafts_to_revise)} comments!")
                    st.rerun()

            st.divider()

            for i, item in enumerate(queue):
                with st.container(border=True):
                    sub = f"r/{item['subreddit']}" if item["subreddit"] else item["platform"]
                    status_icon = {"draft": "📝", "posted": "✅", "error": "❌"}.get(item["status"], "📝")
                    st.markdown(f"{status_icon} **[{item['title'][:70]}]({item['url']})** — {sub}")

                    ver = st.session_state.get(f"q_ver_{i}", 0)
                    edited = st.text_area("Comment", value=item["comment"], height=120, key=f"q_comment_{i}_{ver}", label_visibility="collapsed")
                    queue[i]["comment"] = edited

                    rev_text = st.text_input("What to change?", placeholder="shorter, less promotional, add fee comparison", key=f"q_rev_{i}", label_visibility="collapsed")

                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                    with col1:
                        st.markdown(f"[Open post ↗]({item['url']})")
                    with col2:
                        if st.button("✏️ Revise", key=f"q_rev_btn_{i}", disabled=not api_key or not rev_text):
                            try:
                                revised = revise_comment(api_key, current_comment=edited, instructions=rev_text)
                                queue[i]["comment"] = revised
                                st.session_state[f"q_ver_{i}"] = ver + 1
                                st.session_state["comment_queue"] = queue
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    with col3:
                        if item["status"] != "posted":
                            if st.button("✅ Posted", key=f"q_posted_{i}"):
                                queue[i]["status"] = "posted"
                                st.session_state["comment_queue"] = queue
                                _save_distribution_state()
                                st.rerun()
                    with col4:
                        st.download_button("📋 Copy", data=edited, file_name=f"comment_{i}.txt", mime="text/plain", key=f"q_dl_{i}")

            st.session_state["comment_queue"] = queue
            _save_distribution_state()

            st.divider()

            # Export
            export_rows = [{
                "Post URL": item["url"], "Post Title": item["title"], "Platform": item["platform"],
                "Subreddit": item.get("subreddit", ""), "Comment": item["comment"],
                "Status": item["status"], "Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            } for item in queue]
            export_df = pd.DataFrame(export_rows)
            csv_data = export_df.to_csv(index=False)

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button("📥 Export All to CSV", data=csv_data,
                    file_name=f"reddit_comments_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="export_queue_csv")
            with col_exp2:
                draft_rows = [r for r in export_rows if r["Status"] == "draft"]
                if draft_rows:
                    draft_csv = pd.DataFrame(draft_rows).to_csv(index=False)
                    st.download_button(f"📥 Export {len(draft_rows)} Drafts Only", data=draft_csv,
                        file_name=f"reddit_drafts_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="export_drafts_csv")

            # Push to Google Sheets
            gsheets_creds = st.session_state.get("gsheets_json", "")
            col_sheets, col_csv2 = st.columns(2)
            with col_sheets:
                if st.button("📊 Push to Google Sheets", type="primary", key="push_sheets_btn", disabled=not gsheets_creds):
                    with st.spinner("Pushing to Google Sheets..."):
                        try:
                            n = push_comments(gsheets_creds, queue)
                            if n:
                                st.success(f"✅ Pushed {n} new comments to [Google Sheet](https://docs.google.com/spreadsheets/d/1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k)")
                            else:
                                st.info("All comments already in the sheet (no duplicates).")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            with col_csv2:
                if not gsheets_creds:
                    st.caption("⚠️ Google Sheets credentials not found. Add secrets.toml to enable.")
            st.caption("**GEO Impact:** Reddit & Quora comments are indexed by ChatGPT, Perplexity, and Google AI Overviews.")
