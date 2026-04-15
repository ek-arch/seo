"""Page 0 — Dashboard: weekly action checklist and quick start guide."""
from __future__ import annotations

import streamlit as st


def page_dashboard():
    st.title("🤖 Kolo SEO & GEO Intelligence Agent")
    st.markdown("**April 2026 · \\$2,000 budget · SEO + GEO (AI visibility) + Social Distribution**")

    st.divider()

    # ── Weekly Actions ──────────────────────────────────────────
    st.subheader("🎯 This Week's Actions")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("### 📣 Social Distribution")
            st.markdown("""
- [ ] Search Reddit for "best crypto card" threads → draft 3 comments
- [ ] Answer 2 Quora questions ("how to spend USDT", "crypto card Europe")
- [ ] Find r/digitalnomad posts about multi-currency cards → comment
- [ ] Post in Telegram crypto card groups (3 communities)
- [ ] Monitor r/CryptoCards for new questions daily
""")
        with st.container(border=True):
            st.markdown("### 🤖 GEO Optimization")
            st.markdown("""
- [ ] Test 10 AI queries (ChatGPT, Perplexity, Google AI) — log Kolo mentions
- [ ] Add FAQ section to every published article
- [ ] Add comparison tables (Kolo vs Binance Card, vs Revolut)
- [ ] Create stat-dense paragraphs AI engines can cite
- [ ] Submit articles to sources AI engines crawl (Reddit, Quora, Wikipedia refs)
""")

    with col_b:
        with st.container(border=True):
            st.markdown("### ✍️ Content & PR")
            st.markdown("""
- [ ] Generate EN article with GEO-optimized structure
- [ ] Translate to RU, ES, ID, IT (top markets by LTV)
- [ ] Publish via outlets from Track Publications
- [ ] Add UTM params to every publication link
- [ ] Use AI Revise to add question headers + quotable stats
""")
        with st.container(border=True):
            st.markdown("### 📊 Track & Measure")
            st.markdown("""
- [ ] Log all published article URLs in Track Publications
- [ ] Check referral traffic from published articles (GA4)
- [ ] Track Reddit comment karma / engagement
- [ ] Record which AI queries show Kolo in answers
- [ ] Monthly eval: compare ROI by channel (SEO vs GEO vs Social)
""")

    st.divider()

    # ── Quick Links ─────────────────────────────────────────────
    st.subheader("🚀 Quick Start")
    st.markdown("""
| Step | Where | What to do |
|---|---|---|
| 1 | **Distribution** → Find Posts | Search Reddit/Quora for crypto card threads |
| 2 | **Distribution** → Draft Comments | Paste post URL → generate helpful reply |
| 3 | **PR Generator** → Generate Draft | Create GEO-optimized article |
| 4 | **PR Generator** → Track Publications | Log published articles + URLs |
| 5 | **Distribution** → Tracker | Monitor comment posting status |
""")
