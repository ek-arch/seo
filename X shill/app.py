import os
import time
import streamlit as st
import json
import anthropic
from datetime import datetime
from personas import ACCOUNTS, TOPICS, SYSTEM_PROMPT_TEMPLATE

# ── API key from Streamlit secrets or env ─────────────────────────────────────
api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
if not api_key:
    st.error("Set ANTHROPIC_API_KEY in Streamlit secrets or environment.")
    st.stop()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KOLO Twitter Comment Tool",
    page_icon="𝕏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #060608; color: #d4d4e8; }

.brand {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8e8f0;
    letter-spacing: -0.02em;
}

.tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.tag-en { background: #0a1628; border: 1px solid #1d4ed8; color: #60a5fa; }
.tag-ru { background: #1a0a0a; border: 1px solid #dc2626; color: #f87171; }
.tag-active { background: #0a1f0f; border: 1px solid #16a34a; color: #4ade80; }
.tag-topic { background: #12101e; border: 1px solid #6d28d9; color: #a78bfa; }

.post-card {
    background: #0c0c14;
    border: 1px solid #18182a;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.15s;
}
.post-card:hover { border-color: #2a2a42; }

.post-author {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #6060a0;
    margin-bottom: 0.4rem;
}

.post-text {
    font-size: 0.88rem;
    color: #c0c0d8;
    line-height: 1.6;
    margin-bottom: 0.6rem;
}

.comment-draft {
    background: #080814;
    border: 1px solid #1e1e38;
    border-left: 3px solid #4ade80;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-size: 0.84rem;
    color: #b0d0b0;
    line-height: 1.6;
    font-family: 'DM Sans', sans-serif;
}

.comment-draft.ru {
    border-left-color: #f87171;
    color: #d0b0b0;
}

.queue-item {
    background: #0c0c14;
    border: 1px solid #18182a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
}

.queue-status {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    padding: 2px 8px;
    border-radius: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.status-pending { background: #1a1400; border: 1px solid #ca8a04; color: #fbbf24; }
.status-approved { background: #0a1f0f; border: 1px solid #16a34a; color: #4ade80; }
.status-rejected { background: #1a0808; border: 1px solid #dc2626; color: #f87171; }

.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: #404060;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 0.5rem;
}

.stat-box {
    background: #0c0c14;
    border: 1px solid #18182a;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.stat-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #e8e8f8;
    display: block;
    line-height: 1;
}
.stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem;
    color: #404060;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 0.3rem;
}

.stButton > button {
    background: #0f0f1e !important;
    color: #a0a0c8 !important;
    border: 1px solid #1e1e38 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: #3a3a68 !important;
    color: #d0d0f0 !important;
}

button[kind="primary"] > div > p,
.primary-btn > button {
    background: linear-gradient(135deg, #1d4ed8, #6d28d9) !important;
    color: white !important;
    border: none !important;
}

.stSelectbox > div > div { background: #0c0c14 !important; border-color: #18182a !important; }
.stTextInput > div > div > input { background: #0c0c14 !important; border-color: #18182a !important; color: #d4d4e8 !important; }
.stTextArea > div > div > textarea { background: #0c0c14 !important; border-color: #18182a !important; color: #d4d4e8 !important; font-family: 'DM Sans', sans-serif !important; }
.stNumberInput > div > div > input { background: #0c0c14 !important; border-color: #18182a !important; color: #d4d4e8 !important; }

div[data-testid="stSidebarContent"] { background: #040406 !important; border-right: 1px solid #18182a; }
hr { border-color: #18182a !important; }
.stSpinner > div { border-top-color: #4ade80 !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent; gap: 0.5rem; }
.stTabs [data-baseweb="tab"] {
    background: #0c0c14 !important;
    border: 1px solid #18182a !important;
    border-radius: 6px !important;
    color: #606080 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: #12122a !important;
    border-color: #3a3a68 !important;
    color: #d0d0f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "queue" not in st.session_state:
    st.session_state.queue = []  # list of comment items
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "active_account" not in st.session_state:
    st.session_state.active_account = "kolo_en"

# ── Helpers ───────────────────────────────────────────────────────────────────
def add_to_queue(post_url, post_text, post_author, comment_text, account_id, topic):
    st.session_state.queue.append({
        "id": len(st.session_state.queue) + 1,
        "timestamp": datetime.now().strftime("%H:%M"),
        "post_url": post_url,
        "post_author": post_author,
        "post_text": post_text,
        "comment": comment_text,
        "account": account_id,
        "topic": topic,
        "status": "pending",
        "edited_comment": comment_text,
    })

def _call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait = 2 ** attempt * 5
                time.sleep(wait)
            else:
                raise

def generate_comment(post_text, post_author, account_id, topic):
    account = ACCOUNTS[account_id]
    system = SYSTEM_PROMPT_TEMPLATE.format(
        account_name=account["name"],
        account_handle=account["handle"],
        language=account["language"],
        persona=account["persona"],
        tone=account["tone"],
        rules="\n".join(f"- {r}" for r in account["rules"]),
        topic=topic,
    )
    client = anthropic.Anthropic(api_key=api_key)
    def _call():
        return client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Post by @{post_author}:\n\n{post_text}\n\nWrite a comment for this post."
            }]
        )
    response = _call_with_retry(_call)
    return response.content[0].text.strip()

def search_twitter_posts(topic, account_id, max_results):
    account = ACCOUNTS[account_id]
    client = anthropic.Anthropic(api_key=api_key)
    def _call():
        return client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system="""You search Twitter/X for relevant posts on a given topic.
Use web_search to find recent Twitter posts matching the topic.
Return results as a JSON array ONLY (no markdown, no explanation):
[
  {
    "author": "username",
    "text": "full post text",
    "url": "https://twitter.com/...",
    "relevance": "why this post is relevant for commenting"
  }
]
Find posts that are: recent, have engagement potential, are NOT from competitor crypto card products, and are suitable for a thoughtful comment that mentions KOLO naturally.""",
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{
                "role": "user",
                "content": f"Search Twitter for recent posts about: {topic}\nLanguage preference: {account['language']}\nFind {max_results} posts suitable for commenting."
            }]
        )
    response = _call_with_retry(_call)
    # Extract text blocks
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        # Find JSON array in text
        start = clean.find("[")
        end = clean.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except:
        pass
    return []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand">𝕏 KOLO Comment Tool</div>', unsafe_allow_html=True)
    st.markdown("<div style=\"font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#404060;letter-spacing:0.12em;margin-bottom:1.2rem;\">TWITTER GROWTH AUTOMATION</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-label">Active Account</div>', unsafe_allow_html=True)

    for acc_id, acc in ACCOUNTS.items():
        is_active = st.session_state.active_account == acc_id
        lang_class = "tag-en" if acc["language"] == "English" else "tag-ru"
        active_indicator = "● " if is_active else "○ "
        if st.button(
            f"{active_indicator}{acc['handle']} ({acc['language'][:2].upper()})",
            key=f"acc_{acc_id}",
            use_container_width=True
        ):
            st.session_state.active_account = acc_id
            st.rerun()

    st.markdown("---")

    # Queue stats
    pending = sum(1 for q in st.session_state.queue if q["status"] == "pending")
    approved = sum(1 for q in st.session_state.queue if q["status"] == "approved")
    rejected = sum(1 for q in st.session_state.queue if q["status"] == "rejected")

    st.markdown('<div class="section-label">Queue Stats</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-box"><span class="stat-num" style="color:#fbbf24">{pending}</span><div class="stat-label">Pending</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><span class="stat-num" style="color:#4ade80">{approved}</span><div class="stat-label">OK</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><span class="stat-num" style="color:#f87171">{rejected}</span><div class="stat-label">Skip</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑 Clear All Queue", use_container_width=True):
        st.session_state.queue = []
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
account = ACCOUNTS[st.session_state.active_account]
lang_tag = "tag-en" if account["language"] == "English" else "tag-ru"

st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-family:'IBM Plex Mono',monospace; font-size:1.8rem; font-weight:700; color:#e8e8f8;">Comment Queue</span>
    <span class="tag {lang_tag}">{account['language']}</span>
    <span class="tag tag-active">● Active: {account['handle']}</span>
</div>
<div style="font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#404060; letter-spacing:0.1em; margin-bottom:1.5rem;">
    {account['persona']}
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍  Search & Draft", "📋  Review Queue", "✏️  Manual Add"])

# ── TAB 1: Search & Draft ─────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-label" style="margin-top:0.5rem;">Search Settings</div>', unsafe_allow_html=True)

    col_topic, col_count = st.columns([3, 1])
    with col_topic:
        selected_topic = st.selectbox(
            "Topic",
            options=list(TOPICS.keys()),
            format_func=lambda k: TOPICS[k]["label"],
            label_visibility="collapsed"
        )
    with col_count:
        max_posts = st.number_input("Posts", min_value=1, max_value=10, value=5, label_visibility="collapsed")

    col_acc, col_btn = st.columns([2, 1])
    with col_acc:
        handle = account["handle"]
        st.markdown(f"<div style=\"font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#606080; padding-top:0.6rem;\">Drafting as: <span style=\"color:#a0a0e0\">{handle}</span></div>", unsafe_allow_html=True)
    with col_btn:
        search_btn = st.button("Search Twitter →", use_container_width=True)

    if search_btn:
        topic_data = TOPICS[selected_topic]
        with st.spinner(f"Searching Twitter for '{topic_data['label']}' posts..."):
            results = search_twitter_posts(
                topic=topic_data["search_query"],
                account_id=st.session_state.active_account,
                max_results=max_posts,
            )
            st.session_state.search_results = results

    if st.session_state.search_results:
        st.markdown("---")
        st.markdown(f'<div class="section-label">Found {len(st.session_state.search_results)} posts — generate comments below</div>', unsafe_allow_html=True)

        for i, post in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown(f"""
                <div class="post-card">
                    <div class="post-author">@{post.get('author', 'unknown')} · {post.get('relevance', '')}</div>
                    <div class="post-text">{post.get('text', '')[:300]}{'...' if len(post.get('text','')) > 300 else ''}</div>
                </div>
                """, unsafe_allow_html=True)

                col_gen, col_add = st.columns([1, 1])
                draft_key = f"draft_{i}"

                with col_gen:
                    if st.button(f"✨ Generate Comment", key=f"gen_{i}", use_container_width=True):
                        with st.spinner("Drafting comment (retrying if rate-limited)..."):
                            try:
                                comment = generate_comment(
                                    post_text=post.get("text", ""),
                                    post_author=post.get("author", ""),
                                    account_id=st.session_state.active_account,
                                    topic=TOPICS[selected_topic]["label"],
                                )
                                st.session_state[draft_key] = comment
                            except anthropic.RateLimitError:
                                st.warning("⏳ Rate limited — wait 30s and try again.")
                            except Exception as e:
                                st.error(f"Error: {e}")

                if draft_key in st.session_state:
                    draft_class = "comment-draft" if account["language"] == "English" else "comment-draft ru"
                    edited = st.text_area(
                        "Edit comment",
                        value=st.session_state[draft_key],
                        key=f"edit_{i}",
                        height=90,
                        label_visibility="collapsed"
                    )
                    with col_add:
                        if st.button(f"+ Add to Queue", key=f"add_{i}", use_container_width=True):
                            add_to_queue(
                                post_url=post.get("url", ""),
                                post_text=post.get("text", ""),
                                post_author=post.get("author", ""),
                                comment_text=edited,
                                account_id=st.session_state.active_account,
                                topic=TOPICS[selected_topic]["label"],
                            )
                            st.success("Added to queue!")

# ── TAB 2: Review Queue ───────────────────────────────────────────────────────
with tab2:
    if not st.session_state.queue:
        st.markdown("<div style=\"text-align:center; padding:3rem; color:#404060; font-family:'IBM Plex Mono',monospace; font-size:0.8rem;\">Queue is empty — search for posts first</div>", unsafe_allow_html=True)
    else:
        # Filter controls
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_status = st.selectbox("Filter by status", ["all", "pending", "approved", "rejected"], label_visibility="collapsed")
        with filter_col2:
            filter_account = st.selectbox("Filter by account", ["all"] + list(ACCOUNTS.keys()), label_visibility="collapsed")

        items = st.session_state.queue
        if filter_status != "all":
            items = [q for q in items if q["status"] == filter_status]
        if filter_account != "all":
            items = [q for q in items if q["account"] == filter_account]

        st.markdown(f'<div class="section-label">{len(items)} items</div>', unsafe_allow_html=True)

        for item in reversed(items):
            idx = st.session_state.queue.index(item)
            acc = ACCOUNTS[item["account"]]
            status_class = f"status-{item['status']}"

            with st.container():
                st.markdown(f"""
                <div class="queue-item">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                        <span style="font-family:'IBM Plex Mono',monospace; font-size:0.65rem; color:#606080;">
                            #{item['id']} · {item['timestamp']} · <span style="color:#a0a0c8">@{item['post_author']}</span> · <span style="color:#8080c0">{item['topic']}</span>
                        </span>
                        <span class="queue-status {status_class}">{item['status']}</span>
                    </div>
                    <div style="font-size:0.78rem; color:#606080; margin-bottom:0.6rem; font-style:italic;">"{item['post_text'][:120]}..."</div>
                </div>
                """, unsafe_allow_html=True)

                edited_comment = st.text_area(
                    "Comment",
                    value=item["edited_comment"],
                    key=f"q_edit_{idx}",
                    height=80,
                    label_visibility="collapsed"
                )
                # Update edited comment
                st.session_state.queue[idx]["edited_comment"] = edited_comment

                # Account badge + actions
                col_acc_badge, col_approve, col_reject, col_copy = st.columns([2, 1, 1, 1])
                with col_acc_badge:
                    lang_c = "tag-en" if acc["language"] == "English" else "tag-ru"
                    st.markdown(f'<span class="tag {lang_c}" style="display:inline-block;margin-top:0.4rem;">{acc["handle"]}</span>', unsafe_allow_html=True)
                    if item.get("post_url"):
                        post_url = item["post_url"]
                        st.markdown(f"<a href=\"{post_url}\" target=\"_blank\" style=\"font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#404080;text-decoration:none;\">↗ open post</a>", unsafe_allow_html=True)

                with col_approve:
                    if st.button("✓ Approve", key=f"approve_{idx}", use_container_width=True):
                        st.session_state.queue[idx]["status"] = "approved"
                        st.rerun()
                with col_reject:
                    if st.button("✗ Skip", key=f"reject_{idx}", use_container_width=True):
                        st.session_state.queue[idx]["status"] = "rejected"
                        st.rerun()
                with col_copy:
                    st.code(edited_comment[:50] + "...", language=None)

                st.markdown("---")

        # Export approved
        approved_items = [q for q in st.session_state.queue if q["status"] == "approved"]
        if approved_items:
            st.markdown(f'<div class="section-label" style="margin-top:1rem;">{len(approved_items)} approved — ready to post</div>', unsafe_allow_html=True)
            export_data = []
            for q in approved_items:
                export_data.append({
                    "account": ACCOUNTS[q["account"]]["handle"],
                    "post_url": q["post_url"],
                    "comment": q["edited_comment"],
                    "topic": q["topic"],
                })
            st.download_button(
                "↓ Export Approved as JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"kolo_comments_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )

# ── TAB 3: Manual Add ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-label" style="margin-top:0.5rem;">Paste a post manually</div>', unsafe_allow_html=True)

    m_url = st.text_input("Post URL", placeholder="https://twitter.com/...", label_visibility="collapsed")
    m_author = st.text_input("Author handle", placeholder="@username", label_visibility="collapsed")
    m_text = st.text_area("Post text", placeholder="Paste the post content here...", height=100, label_visibility="collapsed")

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        m_account = st.selectbox("Post as account", options=list(ACCOUNTS.keys()),
                                  format_func=lambda k: ACCOUNTS[k]["handle"])
    with m_col2:
        m_topic = st.selectbox("Topic category", options=list(TOPICS.keys()),
                                format_func=lambda k: TOPICS[k]["label"])

    if st.button("✨ Generate Comment for this Post", use_container_width=True):
        if m_text.strip():
            with st.spinner("Generating (retrying if rate-limited)..."):
                try:
                    comment = generate_comment(
                        post_text=m_text,
                        post_author=m_author.replace("@", ""),
                        account_id=m_account,
                        topic=TOPICS[m_topic]["label"],
                    )
                    st.session_state["manual_draft"] = comment
                except anthropic.RateLimitError:
                    st.warning("⏳ Rate limited — wait 30s and try again.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Paste a post first.")

    if "manual_draft" in st.session_state:
        m_edited = st.text_area("Edit comment", value=st.session_state["manual_draft"], height=100, key="m_edit", label_visibility="collapsed")
        if st.button("+ Add to Queue", use_container_width=True):
            add_to_queue(
                post_url=m_url,
                post_text=m_text,
                post_author=m_author.replace("@", ""),
                comment_text=m_edited,
                account_id=m_account,
                topic=TOPICS[m_topic]["label"],
            )
            del st.session_state["manual_draft"]
            st.success("Added to queue!")
            st.rerun()
