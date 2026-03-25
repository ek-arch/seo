"""
app.py — Kolo SEO & GEO Intelligence Agent
Single-file Streamlit app using st.navigation().
All data lives in data_sources.py.
GEO = Generative Engine Optimization (AI answer visibility).
"""

import streamlit as st
import pandas as pd
import altair as alt
import requests as _requests
from data_sources import DATA, score_outlet_notion, outlet_verdict
from collaborator_outlets import (
    get_outlets, get_top_outlets_all_langs,
    LANG_LABELS, score_label, RAW_OUTLETS,
)
from publication_roi import (
    calculate_publication_roi, batch_roi, roi_label,
    LTV_BY_LANG, CONVERSION_RATE_BY_LANG, LTV_BY_MARKET_LANG,
)
from llm_client import generate_press_release, revise_press_release, translate_press_release, recommend_monthly_plan, generate_comment_reply, LANG_NAMES
from geo_visibility import DEFAULT_QUERIES, audit_query, run_full_audit, summarize_audit
from notion_writer import (
    create_content_plan_entry, create_pr_draft_page,
    create_monthly_plan_page, log_publication_result,
)
from monthly_cycle import (
    PublicationResult, MonthlyEvaluation, MonthlyPlan,
    evaluate_month, generate_plan_inputs, parse_plan_recommendation,
    plan_to_notion_entries,
)
import ahrefs_hook

st.set_page_config(
    page_title="Kolo SEO & GEO Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://kolo.in/favicon.ico", width=32)
    st.title("Kolo SEO & GEO Agent")
    st.caption("kolo.in · crypto Visa card")
    st.divider()
    st.subheader("🔑 API Keys")
    hex_token = st.text_input("Hex API token",           type="password", placeholder="hxtp_...",    help="app.hex.tech → Settings → API keys")
    collab_token = st.text_input("Collaborator.pro token", type="password", placeholder="etVxo-...", help="collaborator.pro/user/api")
    notion_token = st.text_input("Notion token", type="password", placeholder="secret_...", help="Required for writing to Notion")
    anthropic_token = st.text_input("Anthropic API key", type="password", placeholder="sk-ant-...", help="console.anthropic.com → API keys")
    serpapi_key = st.text_input("SerpAPI key", type="password", placeholder="...", help="serpapi.com → free 100 searches/month")
    for k, v in [("hex_token", hex_token), ("collab_token", collab_token), ("notion_token", notion_token), ("anthropic_token", anthropic_token), ("serpapi_key", serpapi_key)]:
        if v:
            st.session_state[k] = v
    st.divider()
    st.subheader("📋 Pipeline")
    for name, status in [("Stage 1 · Market Intel", "✅"), ("Stage 2 · Kolo Metrics", "✅"),
                          ("Stage 3 · Content Plan", "✅"), ("Stage 4 · Outlet Match",  "✅"),
                          ("Stage 5 · Pub ROI",       "✅"),
                          ("Stage 6 · PR Generator",  "🆕"), ("Stage 7 · Distribution", "🆕"),
                          ("Stage 8 · GEO Visibility","🆕"),
                          ("Stage 9 · Monthly Eval", "🆕"),
                          ("Stage 10 · Monthly Planner","🆕")]:
        st.markdown(f"{status} {name}")
    st.divider()
    st.caption("Source: Hex BigQuery · exchanger2_db_looker\n180-day window · F&F excluded · Refreshed 2026-03-24")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 0 · DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    st.title("🤖 Kolo SEO & GEO Intelligence Agent")
    st.markdown("**March 2026 · \\$2,000 budget · SEO + GEO (AI visibility) + Social Distribution**")

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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 · MARKET INTEL
# ══════════════════════════════════════════════════════════════════════════════

def page_market_intel():
    st.title("📊 Stage 1 · Market Intel")
    st.caption("Last run: 2026-03-10 · Web search + competitor analysis + AI engine audit")

    st.header("Competitor Map by Market")
    competitors = pd.DataFrame([
        {"Market": "🇬🇧 GBR", "Key Competitors": "Wirex, Bybit, Nexo, Coinbase",          "Kolo Advantage": "Lower fees, USDT TRC20, Telegram-native",         "Threat": "High"},
        {"Market": "🇦🇪 ARE", "Key Competitors": "Oobit, Crypto.com, Club Swan",            "Kolo Advantage": "TRON community, TRC20 dominant stablecoin rail",   "Threat": "High"},
        {"Market": "🇵🇱 POL", "Key Competitors": "Bleap (local), MetaMask Card, Binance",   "Kolo Advantage": "No dominant local brand — Kolo can own it",         "Threat": "Medium"},
        {"Market": "🇮🇹 ITA", "Key Competitors": "Coinbase, Binance, MetaMask Card",        "Kolo Advantage": "Zero Italian SEO competition",                     "Threat": "Medium"},
        {"Market": "🇪🇸 ESP", "Key Competitors": "Crypto.com, Coinbase, MetaMask",          "Kolo Advantage": "RU-speaking Spanish users = 2× LTV",               "Threat": "Medium"},
        {"Market": "🇮🇩 IDN", "Key Competitors": "Bitget (50+ markets)",                    "Kolo Advantage": "Strong USDT TRC20 use case, cheap media",          "Threat": "Low"},
        {"Market": "🇧🇷 BRA", "Key Competitors": "Crypto.com, COCA, Gnosis Pay",            "Kolo Advantage": "—",                                                "Threat": "Low (deprioritize)"},
        {"Market": "🇷🇴 ROU", "Key Competitors": "Bybit (Crypto Expo 2026 winner)",         "Kolo Advantage": "+183% growth, no Kolo content yet",                "Threat": "High (urgent)"},
        {"Market": "🌍 CIS",  "Key Competitors": "Oobit (KGZ only)",                        "Kolo Advantage": "Bybit/Nexo/KuCoin ALL exclude CIS — structural moat","Threat": "Low"},
        {"Market": "🇨🇭 CHE", "Key Competitors": "None dominant",                           "Kolo Advantage": "44.68% crypto penetration, premium audience",       "Threat": "Low"},
    ])
    def color_threat(val):
        return {"High": "background-color: #ffd6d6", "Medium": "background-color: #fff3cd",
                "Low": "background-color: #d4edda", "High (urgent)": "background-color: #ff9999",
                "Low (deprioritize)": "background-color: #e8e8e8"}.get(val, "")
    st.dataframe(competitors.style.applymap(color_threat, subset=["Threat"]), use_container_width=True, hide_index=True)

    st.header("Content Gaps vs. Competitors")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 Critical Gaps")
        st.markdown("""
1. **"Best crypto card [country]" pages** — Oobit has country-specific landing pages. Kolo has none.
2. **Cashback comparison** — "0% fee vs 4% cashback with 1.7% conversion cost = Kolo wins."
3. **USDT TRC20 spend guide** — TRC20 dominant in CIS + UAE. Zero content from Kolo.
4. **Trustee Plus shutdown coverage** — Highest-intent migration keyword, minimal competition.
5. **B2B crypto card** — 41% of Kolo spend, 7× faster growth. Zero B2B-targeted content.
""")
    with col2:
        st.subheader("🟡 Opportunity Gaps")
        st.markdown("""
6. **Romania crypto card** — +183% Kolo growth, Bybit now competing there. Move fast.
7. **"How to spend USDT in [city]"** — Local content for Dubai, Warsaw, Tbilisi, Bishkek.
8. **TRON/TRC20 card guide** — TRON partnership drove 2.9× deposit spike.
9. **Crypto card for freelancers** — B2B angle, growing segment, underserved.
10. **Argentina USDC stablecoin card** — Argentina is 46.6% USDC. Localized angle.
""")

    st.header("Target Keyword Rankings")
    keywords = pd.DataFrame([
        {"Keyword": "best crypto card 2026",       "Intent": "Transactional", "Top Competitors": "Wirex, Crypto.com, Bybit, Nexo", "Kolo": "❌ Not visible", "Priority": "🔴"},
        {"Keyword": "crypto card UK",               "Intent": "Transactional", "Top Competitors": "Wirex, Coinbase, Crypto.com",    "Kolo": "❌ Not visible", "Priority": "🔴"},
        {"Keyword": "USDT card",                    "Intent": "Transactional", "Top Competitors": "Oobit, Bitget, Buvei",           "Kolo": "❌ Not visible", "Priority": "🔴"},
        {"Keyword": "Trustee Plus alternative",     "Intent": "Transactional", "Top Competitors": "Minimal",                       "Kolo": "❌ Not visible", "Priority": "🔴 HUGE"},
        {"Keyword": "how to spend crypto",          "Intent": "Informational", "Top Competitors": "MetaMask, CoinGecko, guides",   "Kolo": "❌ Not visible", "Priority": "🟠"},
        {"Keyword": "crypto card Poland",           "Intent": "Transactional", "Top Competitors": "Bleap, MetaMask Card",          "Kolo": "❌ Not visible", "Priority": "🟠"},
        {"Keyword": "crypto card Italy",            "Intent": "Transactional", "Top Competitors": "Binance, Coinbase, MetaMask",   "Kolo": "❌ Not visible", "Priority": "🟠"},
        {"Keyword": "crypto debit card UAE",        "Intent": "Transactional", "Top Competitors": "Oobit, Crypto.com, Bybit",      "Kolo": "❌ Not visible", "Priority": "🟠"},
        {"Keyword": "TRC20 card",                   "Intent": "Transactional", "Top Competitors": "Bitget, Buvei",                 "Kolo": "❌ Not visible", "Priority": "🟡"},
        {"Keyword": "crypto card Georgia",          "Intent": "Transactional", "Top Competitors": "Bitget (150 countries)",        "Kolo": "❌ Not visible", "Priority": "🟡"},
    ])
    st.dataframe(keywords, use_container_width=True, hide_index=True)

    st.header("Market Trend Signals")
    c1, c2, c3 = st.columns(3)
    c1.metric("Visa crypto card spending growth", "15×", "Jan 2023 → Dec 2025")
    c2.metric("Total stablecoin tx volume (2025)", "2.5T", "USDT dominant globally")
    c3.metric("Visa stablecoin card programs", "130+", "40+ countries")
    st.markdown("""
| Signal | Detail |
|---|---|
| 🇷🇴 Romania breakout | 10% flat crypto tax, MiCA adopted, IT expat community, Revolut 3M users |
| 🇨🇭 Switzerland | 4.03M crypto users projected 2026, 44.68% penetration, premium fintech audience |
| 🌍 CIS structural gap | Bybit, Nexo, KuCoin all explicitly exclude CIS — Kolo has exclusive access |
| 🇸🇪 Sweden whale | \\$24,570/user (9 users, \\$221K) — RU expat cluster, no competitor content targeting them |
""")
    st.info("**Data source:** Web search, competitor sites, CoinGecko, Cryptopolitan · 2026-03-10")

    st.header("🤖 AI Engine Visibility Audit (GEO)")
    st.caption("Generative Engine Optimization — does Kolo appear when users ask AI about crypto cards?")
    geo_audit = pd.DataFrame([
        {"Query": "best crypto card 2026",        "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Crypto.com, Coinbase, Wirex, Bybit"},
        {"Query": "crypto card UK",                "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Wirex, Coinbase, Nexo, Revolut"},
        {"Query": "USDT card",                     "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Oobit, Bitget, Bybit"},
        {"Query": "Trustee Plus alternative",      "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Minimal competition — high opportunity"},
        {"Query": "how to spend crypto",           "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "MetaMask, CoinGecko guides, Crypto.com"},
        {"Query": "crypto card Poland",            "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Binance, MetaMask Card"},
        {"Query": "crypto card Italy",             "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Coinbase, Binance"},
        {"Query": "crypto debit card UAE",         "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Oobit, Crypto.com, Bybit"},
        {"Query": "TRC20 card",                    "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Bitget, minimal competition"},
        {"Query": "crypto card for business",      "ChatGPT": "❌", "Perplexity": "❌", "Google AI Overview": "❌", "Who Appears Instead": "Crypto.com, Coinbase, Ramp"},
    ])
    st.dataframe(geo_audit, use_container_width=True, hide_index=True)
    st.error(
        "**Kolo is invisible across all 10 target queries in ALL AI engines.** "
        "GEO tactics needed: FAQ sections, stat-dense content, entity-rich intros, "
        "and publication on high-authority outlets that AI engines cite."
    )
    st.markdown("""
**GEO Action Plan:**
1. **Restructure lead article** with FAQ section + question-format headers
2. **Publish on high-DR outlets** (DR>65) that AI engines frequently cite
3. **Include quotable stats** — AI engines extract self-contained factual sentences
4. **Target "Trustee Plus alternative"** — minimal AI competition, high intent
5. **Monitor monthly** — re-audit AI engine presence after each publication cycle
""")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 · KOLO METRICS
# ══════════════════════════════════════════════════════════════════════════════

def page_kolo_metrics():
    st.title("📈 Stage 2 · Kolo Metrics")
    st.caption("Language & country analysis for SEO/GEO targeting · F&F excluded · STANDARD referrals only")

    st.warning(
        "⚠️ **Friends & Family users excluded** from all metrics. "
        "Data shows organic/standard users only — PRT, ARE and other markets "
        "may show lower numbers than before but are more accurate for SEO ROI projections."
    )

    st.header("Language Cluster Analysis")
    st.info("🔑 **Russian users spend 1.7× per user vs English** (\\$6,357 vs \\$3,792) — the Russian pillar is the highest-ROI allocation.")
    langs = pd.DataFrame(DATA["languages"])
    langs["spend_fmt"] = langs["spend_per_user"].apply(lambda x: f"${x:,}")
    langs["total_fmt"] = langs["total_spend"].apply(lambda x: f"${x/1e3:.0f}K")
    lang_chart = alt.Chart(langs).mark_bar().encode(
        x=alt.X("spend_per_user:Q", title="Spend per User (USD)"),
        y=alt.Y("lang:N", sort="-x", title="Language"),
        color=alt.condition(alt.datum.code == "ru", alt.value("#FF6B35"), alt.value("#2196F3")),
        tooltip=["lang", alt.Tooltip("spend_per_user:Q", format="$,.0f"),
                 "card_users", alt.Tooltip("total_spend:Q", format="$,.0f")],
    ).properties(height=280)
    st.altair_chart(lang_chart, use_container_width=True)

    st.header("Country Performance (99 Active Markets)")
    countries = pd.DataFrame(DATA["countries"])
    tier_filter = st.multiselect(
        "Filter by tier", options=["1","2","3"], default=["1","2"],
        format_func=lambda x: {"1":"Tier 1 (>$400K)","2":"Tier 2 ($100K–$400K)",
                                "3":"Tier 3 ($30K–$100K)"}.get(x, x),
    )
    filtered = countries[countries["tier"].astype(str).isin(tier_filter)].copy()
    filtered["spend_fmt"] = filtered["card_spend"].apply(lambda x: f"${x/1e3:.0f}K")
    filtered["spu_fmt"]   = filtered["spend_per_user"].apply(lambda x: f"${x:,}")
    filtered["conv_fmt"]  = filtered["conversion"].apply(lambda x: f"{x*100:.0f}%")
    def highlight_row(row):
        if row["Tier"] == "whale": return ["background-color: #fff3cd"] * len(row)
        try:
            conv = float(str(row.get("Conv.", "0")).replace("%", ""))
            if conv >= 80: return ["background-color: #d4edda"] * len(row)
        except (ValueError, TypeError):
            pass
        return [""] * len(row)
    st.dataframe(
        filtered[["flag","country","card_users","spend_fmt","spu_fmt","conv_fmt","tier"]]
        .rename(columns={"flag":"","country":"Country","card_users":"Users","spend_fmt":"Spend",
                         "spu_fmt":"$/User","conv_fmt":"Conv.","tier":"Tier"})
        .style.apply(highlight_row, axis=1),
        use_container_width=True, hide_index=True,
    )
    st.caption("🟢 = ≥80% conversion")

    st.caption("Articles remain indexed 12+ months. Year-one ROI: estimated 4–15×.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 · CONTENT PLAN
# ══════════════════════════════════════════════════════════════════════════════

def page_content_plan():
    st.title("✍️ Stage 3 · Content Plan")
    st.caption("Generated: 2026-03-10 · Based on Stage 1 competitor analysis + Hex live data + GEO checklist")

    st.header("10 Article Briefs")
    briefs = pd.DataFrame([
        {"#": 1,  "Title": "How to Spend Crypto with a Visa Card in 2026",          "Lang": "EN",    "Market": "Global",      "KW": "how to spend crypto with a visa card",  "Words": 1500, "Priority": "🔴 LEAD"},
        {"#": 2,  "Title": "Best Crypto Debit Card in the UK 2026",                 "Lang": "EN",    "Market": "🇬🇧 GBR",    "KW": "best crypto card UK 2026",              "Words": 1200, "Priority": "🔴"},
        {"#": 3,  "Title": "Crypto Card for UAE Expats 2026: Spend USDT in Dubai",  "Lang": "EN",    "Market": "🇦🇪 ARE",    "KW": "crypto card UAE / USDT card UAE",       "Words": 1200, "Priority": "🔴"},
        {"#": 4,  "Title": "Najlepsza karta krypto w Polsce 2026",                  "Lang": "PL",    "Market": "🇵🇱 POL",    "KW": "karta krypto Polska",                   "Words": 1000, "Priority": "🟠"},
        {"#": 5,  "Title": "Melhor Cartão Cripto no Brasil 2026: Gaste USDT",       "Lang": "PT-BR", "Market": "🇧🇷 BRA",    "KW": "cartão cripto Brasil / cartão USDT",    "Words": 1000, "Priority": "🟠"},
        {"#": 6,  "Title": "Migliore Carta Crypto in Italia 2026",                  "Lang": "IT",    "Market": "🇮🇹 ITA",    "KW": "carta crypto Italia",                   "Words": 1000, "Priority": "🟠"},
        {"#": 7,  "Title": "Kartu Kripto Terbaik di Indonesia 2026",                "Lang": "ID",    "Market": "🇮🇩 IDN",    "KW": "kartu kripto Indonesia",                "Words": 1000, "Priority": "🟠"},
        {"#": 8,  "Title": "Альтернатива Trustee Plus: лучшая крипто-карта 2026",  "Lang": "RU+UK", "Market": "🌍 CIS/UKR", "KW": "альтернатива trustee plus",             "Words": 1200, "Priority": "🔴 URGENT"},
        {"#": 9,  "Title": "Cel mai bun card crypto în România 2026",               "Lang": "RO",    "Market": "🇷🇴 ROU",    "KW": "card crypto Romania",                   "Words": 1000, "Priority": "🔴 BREAKOUT"},
        {"#": 10, "Title": "Crypto Card for Business 2026: Pay with USDT",          "Lang": "EN+RU", "Market": "Global B2B", "KW": "crypto card business / USDT card B2B",  "Words": 1400, "Priority": "🟡"},
    ])
    def color_priority(val):
        if "URGENT" in str(val) or "LEAD" in str(val): return "background-color: #ffd6d6; font-weight: bold"
        if "BREAKOUT" in str(val):                      return "background-color: #ffe0b2; font-weight: bold"
        if "🔴" in str(val):                            return "background-color: #fff0f0"
        if "🟠" in str(val):                            return "background-color: #fff9e6"
        return ""
    st.dataframe(briefs.style.applymap(color_priority, subset=["Priority"]), use_container_width=True, hide_index=True)

    st.header("🤖 GEO Optimization Checklist")
    st.caption("Generative Engine Optimization — ensure each article is structured to be cited by AI engines")
    geo_checklist = pd.DataFrame([
        {"#": 1,  "Article": "How to Spend Crypto with a Visa Card", "FAQ Section": "Required", "Question Headers": "Required", "Stat Density": "3+ quotable stats", "AI Query Target": "how to spend crypto, best crypto card 2026"},
        {"#": 2,  "Article": "Best Crypto Debit Card UK 2026",       "FAQ Section": "Required", "Question Headers": "Required", "Stat Density": "3+ quotable stats", "AI Query Target": "crypto card UK, best crypto card UK"},
        {"#": 3,  "Article": "Crypto Card UAE Expats",               "FAQ Section": "Required", "Question Headers": "Required", "Stat Density": "2+ quotable stats", "AI Query Target": "crypto card UAE, USDT card Dubai"},
        {"#": 4,  "Article": "Najlepsza karta krypto Polska",        "FAQ Section": "Recommended", "Question Headers": "Recommended", "Stat Density": "2+ quotable stats", "AI Query Target": "karta krypto Polska"},
        {"#": 5,  "Article": "Melhor Cartao Cripto Brasil",           "FAQ Section": "Recommended", "Question Headers": "Recommended", "Stat Density": "2+ quotable stats", "AI Query Target": "cartao cripto Brasil"},
        {"#": 6,  "Article": "Migliore Carta Crypto Italia",          "FAQ Section": "Recommended", "Question Headers": "Recommended", "Stat Density": "2+ quotable stats", "AI Query Target": "carta crypto Italia"},
        {"#": 7,  "Article": "Kartu Kripto Indonesia",                "FAQ Section": "Recommended", "Question Headers": "Recommended", "Stat Density": "2+ quotable stats", "AI Query Target": "kartu kripto Indonesia"},
        {"#": 8,  "Article": "Alternativa Trustee Plus",              "FAQ Section": "Required", "Question Headers": "Required", "Stat Density": "3+ quotable stats", "AI Query Target": "Trustee Plus alternative, crypto card CIS"},
        {"#": 9,  "Article": "Card crypto Romania",                   "FAQ Section": "Recommended", "Question Headers": "Recommended", "Stat Density": "2+ quotable stats", "AI Query Target": "card crypto Romania"},
        {"#": 10, "Article": "Crypto Card for Business",              "FAQ Section": "Required", "Question Headers": "Required", "Stat Density": "3+ quotable stats", "AI Query Target": "crypto card business, USDT card B2B"},
    ])

    def color_geo(val):
        if val == "Required": return "background-color: #fff0f0"
        if val == "Recommended": return "background-color: #fff9e6"
        return ""
    st.dataframe(
        geo_checklist.style.applymap(color_geo, subset=["FAQ Section", "Question Headers"]),
        use_container_width=True, hide_index=True,
    )
    st.info("**GEO tip:** Articles marked 'Required' target high-competition AI queries. "
            "These MUST include FAQ sections, question-format H2 headers, and at least 3 "
            "self-contained stat sentences that AI engines can extract and cite.")

    # ── GEO Audit-driven briefs ─────────────────────────────────────
    geo_results = st.session_state.get("geo_audit_results", [])
    if geo_results:
        not_visible = [r for r in geo_results if not r.get("error") and not r.get("kolo_visible")]
        visible_low = [r for r in geo_results if r.get("kolo_position") and r["kolo_position"] > 5]

        if not_visible or visible_low:
            st.header("🔍 GEO Audit Gaps → New Briefs")
            st.caption("Auto-generated from your latest GEO Visibility Audit — queries where Kolo is missing or low-ranked")

            gap_rows = []
            existing_kws = {b["KW"].lower() for _, b in briefs.iterrows()}

            for i, r in enumerate(not_visible):
                q = r["query"]
                # Skip if already covered by existing briefs
                if any(q.lower() in kw for kw in existing_kws):
                    continue
                competitors = ", ".join(r.get("competitors_found", [])[:2]) or "—"
                gap_rows.append({
                    "#": f"G{i+1}",
                    "Title": f"{q.replace('crypto', 'Crypto').title()} — Complete Guide 2026",
                    "KW": q,
                    "Status": "🔴 NOT VISIBLE",
                    "Top Competitor": r.get("top_result_domain", "—"),
                    "Action": "Write new article + publish on DR 40+ outlet",
                    "GEO": "FAQ + comparison table + question headers",
                })

            for i, r in enumerate(visible_low):
                q = r["query"]
                if any(q.lower() in kw for kw in existing_kws):
                    continue
                gap_rows.append({
                    "#": f"B{i+1}",
                    "Title": f"Boost: {q.title()}",
                    "KW": q,
                    "Status": f"🟡 Position #{r['kolo_position']}",
                    "Top Competitor": r.get("top_result_domain", "—"),
                    "Action": "Reddit/Quora answers + backlinks to existing article",
                    "GEO": "Add FAQ to existing article if missing",
                })

            if gap_rows:
                gap_df = pd.DataFrame(gap_rows)
                st.dataframe(gap_df, use_container_width=True, hide_index=True)
                st.info(f"**{len([r for r in gap_rows if '🔴' in r['Status']])} new articles needed** + "
                        f"**{len([r for r in gap_rows if '🟡' in r['Status']])} existing articles to boost** "
                        f"based on your GEO audit.")
            else:
                st.success("All audit queries are already covered by existing briefs!")
        else:
            st.success("🎉 GEO Audit shows Kolo is visible in all target queries!")
    else:
        st.info("💡 Run a **GEO Visibility Audit** (Stage 8) to auto-generate content gap briefs here.")

    st.header("🚨 Plan Revisions from Hex Live Data")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**Revision 1 — Spanish cluster targets wrong language**\n\nESP-ru = \\$7,302/user vs ESP-en = \\$4,233/user. Add 4th Russian outlet with Spain/relocation angle. Reallocate \\$100 from IDN pillar.")
        st.info("**Revision 2 — Dubai RU outlet = Week 1, not Week 2**\n\nARE-ru = \\$21,640/user. Single highest expected-value placement. Must lock in Week 1.")
    with col2:
        st.info("**Revision 3 — Portugal data cleaned (F&F excluded)**\n\nPRT = \\$1.13M, \\$6,215/user, 94% conversion — STANDARD users only. F&F users removed from all markets. Brazil (\\$326K, 183 users) is the correct PT-BR content market.")

    st.header("Localization Notes (7 Languages)")
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["🇷🇺 Russian","🇮🇹 Italian","🇪🇸 Spanish","🇵🇱 Polish","🇵🇹 Portuguese","🇮🇩 Indonesian","🇷🇴 Romanian"])
    with t1:
        st.markdown("**Angle:** Trustee Plus alternative + Ukrainian diaspora + CIS expat communities\n\n**Must include:** Why CIS users can't use Bybit/Nexo/KuCoin\n\n**New hooks:** *Spain relocation guide* · *Crypto card for UAE expats (RU-speaking)* · *CIS/SWE expat guide*\n\n**Keywords:** карта USDT 2026, крипто карта для граждан Украины, альтернатива trustee plus\n\n**Publish on:** DR>50 RU crypto outlet, DR>40 RU crypto outlet, Dubai RU expat outlet")
    with t2:
        st.markdown("**Angle:** Italian expat diaspora in UK, Cyprus, UAE\n\n**Add:** Italian crypto tax (26% CGT) and how stablecoin spending reduces exposure\n\n**Keywords:** carta crypto Italia, pagare con criptovalute 2026, carta USDT Italia\n\n**Local hook:** Many Italians in London use Kolo (GBR = #1 Kolo revenue market)")
    with t3:
        st.markdown("**Two angles:** Spain (EU compliance) vs Argentina (USDC for inflation)\n\n**Key:** ESP-ru = \\$7,302/user vs ESP-en = \\$4,233/user — RU-speaking Spanish users are the real target\n\n**Argentina:** USDC/USDT for inflation hedging, 46.6% USDC penetration\n\n**Keywords:** tarjeta crypto España, gastar bitcoin 2026, tarjeta USDT")
    with t4:
        st.markdown("**Angle:** Polish IT freelancer paid in EUR, tired of PLN conversion fees\n\n**Tone:** Very practical, numbers-first. Polish readers trust data over claims.\n\n**Add:** Direct fee comparison: Bleap (local brand) vs Kolo\n\n**Keywords:** karta krypto Polska, płatności USDT Polska, najlepsza karta bitcoin")
    with t5:
        st.markdown("**Primary market: Brazil (PT-BR)**\n\nBRA = \\$326K, 183 card users, \\$1,781/user — adital.com.br in plan\n\n**PRT status:** \\$1.13M, 182 users, \\$6,215/user — high-value market but F&F excluded. PRT organic users are high spenders.\n\n**Angle (PT-BR):** USDT card for Brazil — inflation protection, no BRL exposure\n\n**Keywords:** cartão cripto Brasil, cartão USDT 2026, gastar bitcoin Brasil")
    with t6:
        st.markdown("**Angle:** USDT TRC20 = dominant rail in Indonesia/SEA\n\n**Tone:** Mobile-first, social proof. Indonesian audience responds to community validation.\n\n**Add:** TRC20 top-up tutorial (cheap, fast, popular with IDN users)\n\n**Keywords:** kartu kripto Indonesia, bayar USDT Indonesia, kartu debit bitcoin\n\n**Note:** IDN has high user count (160) but low \\$/user (\\$1,455) vs CIS — consider reallocating \\$100 to RU pillar")
    with t7:
        st.markdown("**BONUS — Not in original plan, added for +183% breakout market**\n\n**Angle:** Romania +183% Kolo growth, 10% flat crypto tax, IT expat community\n\n**Urgency:** Bybit won Crypto Expo Europe 2026 in Bucharest — move fast\n\n**Keywords:** card crypto Romania, plătesc cu crypto Romania, card USDT 2026")

    st.header("90-Day Publishing Calendar")
    tab_mar, tab_apr, tab_may = st.tabs(["March 2026","April 2026","May 2026"])
    with tab_mar:
        st.dataframe(pd.DataFrame([
            {"Week":"Mar 10–14","Article":"Lead article: How to spend crypto",  "Lang":"EN",    "Market":"Global",      "Outlet":"Own blog + syndication",             "Budget":"$0"},
            {"Week":"Mar 10–14","Article":"Trustee Plus alternative",            "Lang":"RU+UK", "Market":"CIS/Ukraine", "Outlet":"Russian outlets ×3",                "Budget":"$450"},
            {"Week":"Mar 15–21","Article":"Best crypto card UK 2026",            "Lang":"EN",    "Market":"🇬🇧 GBR",   "Outlet":"businessabc.net + businessage.com",  "Budget":"$130"},
            {"Week":"Mar 15–21","Article":"Crypto card UAE expats",              "Lang":"EN",    "Market":"🇦🇪 ARE",   "Outlet":"thetradable.com",                    "Budget":"$100"},
            {"Week":"Mar 15–21","Article":"Migliore carta crypto Italia",        "Lang":"IT",    "Market":"🇮🇹 ITA",   "Outlet":"viverepesaro.it + 1 new",            "Budget":"$200"},
            {"Week":"Mar 22–28","Article":"Kartu kripto Indonesia",              "Lang":"ID",    "Market":"🇮🇩 IDN",   "Outlet":"1–2 new Indonesian outlets",         "Budget":"$80"},
            {"Week":"Mar 22–28","Article":"UK press: crypto card for expats",    "Lang":"EN",    "Market":"🇬🇧 GBR",   "Outlet":"financial-news.co.uk + newspioneer", "Budget":"$190"},
            {"Week":"Mar 29–31","Article":"Najlepsza karta krypto Polska",       "Lang":"PL",    "Market":"🇵🇱 POL",   "Outlet":"netbe.pl + 1 new",                   "Budget":"$74"},
            {"Week":"Mar 29–31","Article":"Tarjeta cripto España",               "Lang":"ES",    "Market":"🇪🇸 ESP",   "Outlet":"crypto-economy + sevillaBN",         "Budget":"$263"},
            {"Week":"Buffer",   "Article":"Deploy based on Week 1–3 traction",  "Lang":"—",     "Market":"TBD",         "Outlet":"TBD",                                "Budget":"~$230"},
        ]), use_container_width=True, hide_index=True)
        st.metric("March Total Budget","$1,717","within $2,000 allocation · $283 buffer")
    with tab_apr:
        st.dataframe(pd.DataFrame([
            {"Week":"Apr 1–7",   "Article":"Melhor cartão cripto Brasil",            "Lang":"PT-BR", "Priority":"🟠 HIGH"},
            {"Week":"Apr 1–7",   "Article":"B2B crypto card for business",           "Lang":"EN",    "Priority":"🟡 MEDIUM"},
            {"Week":"Apr 8–14",  "Article":"Cel mai bun card crypto România",        "Lang":"RO",    "Priority":"🔴 URGENT breakout"},
            {"Week":"Apr 8–14",  "Article":"USDT TRC20 card guide",                  "Lang":"EN+RU", "Priority":"🟠 HIGH"},
            {"Week":"Apr 15–21", "Article":"Bitcoin card Switzerland",               "Lang":"EN/DE", "Priority":"🟡 MEDIUM"},
            {"Week":"Apr 22–28", "Article":"Tarjeta cripto Argentina (USDC angle)",  "Lang":"ES-AR", "Priority":"🟡 MEDIUM"},
            {"Week":"Apr 22–28", "Article":"Kolo × TRON partnership story",          "Lang":"EN+RU", "Priority":"🟡 MEDIUM"},
        ]), use_container_width=True, hide_index=True)
    with tab_may:
        st.dataframe(pd.DataFrame([
            {"Week":"May 1–7",   "Article":"Country page: /crypto-card/georgia",           "Lang":"EN+RU"},
            {"Week":"May 1–7",   "Article":"Country page: /crypto-card/kyrgyzstan",        "Lang":"EN+RU"},
            {"Week":"May 8–14",  "Article":"Update lead article with Q1 2026 data",        "Lang":"All 7"},
            {"Week":"May 8–14",  "Article":"How Kolo helped 1,000+ Trustee users migrate", "Lang":"EN+RU"},
            {"Week":"May 15–21", "Article":"Crypto card comparison 2026 (updated)",        "Lang":"EN"},
            {"Week":"May 22–31", "Article":"Country pages: Uzbekistan + Moldova",          "Lang":"EN+RU"},
        ]), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 · OUTLET MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def page_outlet_matching():
    st.title("🗞️ Stage 4 · Outlet Matching")
    st.caption("Scoring: 6-dimension 0–18 system (SEO + GEO) · Source of truth for all outlet decisions")
    st.success(
        "✅ **Catalog scraped via browser session** — "
        f"{sum(len(v) for v in RAW_OUTLETS.values())} sites across 7 languages "
        "· Filters: DR ≥ 30, price ≤ $250, categories: Crypto + Business & Finance · Refreshed 2026-03-11"
    )

    # ── Scoring Model (Notion guide) ──────────────────────────────────────────
    with st.expander("📐 Scoring Model (SEO + GEO)", expanded=False):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("""
| Dimension | 3 pts | 2 pts | 1 pt | 0 pts |
|---|---|---|---|---|
| **Search %** | >50% | 40–50% | 35–40% | <35% |
| **DR** | >65 | 50–65 | 40–50 | <40 |
| **\\$/DR point** | <\\$2 | \\$2–4 | \\$4–6 | >\\$6 |
| **Category fit** | Crypto+Finance | Crypto+Other | Finance only | Irrelevant |
| **Monthly traffic** | >100K | 30–100K | 5–30K | <5K |
| **AI Citability (GEO)** | Frequently cited | Occasionally | Rarely | Never cited |
""")
        with col2:
            st.markdown("""
**Score thresholds (max 18):**
- **15–18** → ✅ Must buy
- **11–14** → 🟡 Buy if budget allows
- **7–10** → 🟠 Consider only
- **<7** → 🔴 Skip

**Must-Have (auto-disqualify):**
- Search < 35% → **SKIP**
- DR < 40 → **SKIP**
- Price > \\$5/DR → **SKIP**

*AI Citability = how often AI engines (ChatGPT, Perplexity, Google AI) cite this outlet*
""")

    # ── Live Catalog Search ───────────────────────────────────────────────────
    st.header("🔍 Live Catalog Search")
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1, 1, 1, 1])
    with fc1:
        selected_langs = st.multiselect(
            "Languages",
            options=list(LANG_LABELS.keys()),
            default=list(LANG_LABELS.keys()),
            format_func=lambda k: LANG_LABELS[k],
        )
    with fc2:
        min_dr = st.slider("Min DR", min_value=30, max_value=80, value=40, step=5)
    with fc3:
        max_price = st.slider("Max price ($)", min_value=20, max_value=250, value=200, step=10)
    with fc4:
        min_score = st.slider("Min score", min_value=0, max_value=18, value=11, step=1)
    with fc5:
        crypto_only = st.toggle("Crypto category only", value=False)

    catalog_rows = []
    for lang in selected_langs:
        for o in get_outlets(lang, min_dr=min_dr, max_price=max_price,
                             min_score=min_score, crypto_only=crypto_only):
            catalog_rows.append({
                "Lang":        LANG_LABELS[lang],
                "Domain":      o["domain"],
                "DR":          o["dr"],
                "Price ($)":   o["price"],
                "$/DR":        o["price_per_dr"],
                "Search %":    o["search_pct"],
                "Traffic":     o["traffic"],
                "Score":       o["score"],
                "Rating":      score_label(o["score"]),
                "Crypto":      "✅" if o["has_crypto"] else "—",
            })

    if catalog_rows:
        cat_df = pd.DataFrame(catalog_rows)

        def color_catalog(row):
            s = row["Score"]
            if s >= 16: return ["background-color: #c3e6cb"] * len(row)
            if s >= 14: return ["background-color: #d4edda"] * len(row)
            if s >= 12: return ["background-color: #e8f4fd"] * len(row)
            return [""] * len(row)

        st.dataframe(
            cat_df.style.apply(color_catalog, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price ($)":  st.column_config.NumberColumn("Price ($)",  format="$%.2f"),
                "$/DR":       st.column_config.NumberColumn("$/DR",       format="$%.2f"),
                "Search %":   st.column_config.NumberColumn("Search %",   format="%d%%"),
                "Traffic":    st.column_config.NumberColumn("Traffic",    format="%d"),
                "DR":         st.column_config.NumberColumn("DR"),
                "Score":      st.column_config.NumberColumn("Score /18"),
            },
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Outlets shown", len(catalog_rows))
        c2.metric("Avg score", f"{cat_df['Score'].mean():.1f} / 18")
        c3.metric("Avg price", f"${cat_df['Price ($)'].mean():.0f}")
    else:
        st.info("No outlets match current filters — try relaxing DR or price constraints.")

    # ── Top Picks per Pillar ──────────────────────────────────────────────────
    st.header("🏆 Top Picks per Pillar")
    st.caption("Best 5 per language · DR ≥ 40 · Price ≤ $200 · sorted by score then DR · catalog scores 0-15 (add +0-3 for AI citability)")
    top = get_top_outlets_all_langs(min_dr=40, max_price=200, top_n=5)
    cols = st.columns(len([l for l in selected_langs if top.get(l)]) or 1)
    visible_langs = [l for l in selected_langs if top.get(l)]
    for idx, lang in enumerate(visible_langs):
        picks = top[lang]
        with cols[idx]:
            st.subheader(LANG_LABELS[lang])
            for p in picks:
                badge = score_label(p["score"])
                crypto_tag = " 🪙" if p["has_crypto"] else ""
                st.markdown(
                    f"**{p['domain']}**{crypto_tag}  \n"
                    f"{badge} · DR {p['dr']} · ${p['price']:.0f}  \n"
                    f"Search {p['search_pct']}% · {p['traffic']:,} visits"
                )
                st.divider()

    # ── March 2026 Confirmed Outlets ──────────────────────────────────────────
    st.header("📋 March 2026 Confirmed Outlets")
    rows = []
    for lang, sites in DATA["march_outlets"].items():
        for s in sites:
            is_tbd       = "TBD" in s["name"]
            notion_score = s.get("notion_score")
            is_unscored  = notion_score is None and not is_tbd
            verdict      = outlet_verdict(notion_score)
            if is_tbd:
                status  = "⏳ TBD"
                verdict = "—"
            elif is_unscored:
                status = "⚠️ Unscored"
            else:
                status = "✅ Confirmed"
            rows.append({
                "Lang":    lang.upper(),
                "Outlet":  s["name"],
                "Price":   s["price"],
                "DR":      s["dr"],
                "Pillar":  s["pillar"],
                "Score":   notion_score,
                "Verdict": verdict,
                "Status":  status,
                "Notes":   s.get("notes", ""),
            })
    outlets_df = pd.DataFrame(rows)

    def color_row(row):
        if row["Status"] == "⚠️ Unscored": return ["background-color: #fff3cd"] * len(row)
        if row["Status"] == "⏳ TBD":      return ["background-color: #f0f0f0"] * len(row)
        score = row["Score"]
        try:
            if float(score) >= 15: return ["background-color: #d4edda"] * len(row)
            if float(score) >= 11: return ["background-color: #e8f4fd"] * len(row)
        except (TypeError, ValueError):
            pass
        return [""] * len(row)

    st.dataframe(
        outlets_df.style.apply(color_row, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price":  st.column_config.NumberColumn("Price ($)", format="$%d"),
            "DR":     st.column_config.NumberColumn("DR"),
            "Score":  st.column_config.NumberColumn("Score /15"),
        },
    )

    # ── Key Callouts ──────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.success("**🆕 pt.egamersworld.com added (score 13/15)**\n\nIn Notion guide as 'Must buy' — DR>65, >100K traffic, >50% search. Price TBD. Portuguese/Brazil pillar.")
        st.warning("**⚠️ financial-news.co.uk — NOT in Notion guide**\n\nIn March plan but never scored by the guide. Verify independently (DR 54, \\$125) before purchasing.")
    with col_b:
        st.warning("**⚠️ sevillaBN — NOT in Notion guide**\n\nIn March plan but never scored. Verify independently before purchasing.")
        st.info("**sticknoticias.com → Score 3 → Skip**\n\ncoinarbitragebot → Score 9 → Skip (0% search)\n\nBoth in Notion guide as hard Skips — do not buy.")

    # ── Budget Breakdown ──────────────────────────────────────────────────────
    st.header("Pillar Budget Allocation")
    pillar_budget = (
        outlets_df.dropna(subset=["Price"])
        .groupby("Pillar")["Price"].sum()
        .reset_index()
    )
    pillar_budget.columns = ["Pillar", "Spent"]
    caps = {"English": 500, "Russian": 500, "Italian": 200, "Spanish": 300,
            "Polish": 100, "Portuguese": 200, "Indonesian": 100, "Romanian": 100}
    pillar_budget["Cap"]       = pillar_budget["Pillar"].map(caps)
    pillar_budget["Remaining"] = pillar_budget["Cap"] - pillar_budget["Spent"]
    pillar_budget["Util %"]    = (pillar_budget["Spent"] / pillar_budget["Cap"] * 100).round(0).astype(int)
    def color_util(val):
        if val >= 90: return "background-color: #ffd6d6"
        if val >= 60: return "background-color: #fff3cd"
        return "background-color: #d4edda"
    st.dataframe(
        pillar_budget.style.applymap(color_util, subset=["Util %"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Spent":     st.column_config.NumberColumn("Spent ($)", format="$%d"),
            "Cap":       st.column_config.NumberColumn("Cap ($)",   format="$%d"),
            "Remaining": st.column_config.NumberColumn("Remaining ($)", format="$%d"),
        },
    )

    confirmed_df    = outlets_df[outlets_df["Status"] == "✅ Confirmed"]
    tbd_df          = outlets_df[outlets_df["Status"] == "⏳ TBD"]
    confirmed_spend = int(confirmed_df["Price"].fillna(0).sum())
    tbd_spend       = int(tbd_df["Price"].fillna(0).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Scored & Confirmed", f"\\${confirmed_spend:,}", f"{len(confirmed_df)} outlets")
    c2.metric("TBD Allocation",     f"\\${tbd_spend:,}",       f"{len(tbd_df)} slots to source")
    c3.metric("Total Allocated",    f"\\${confirmed_spend + tbd_spend:,}", "of \\$2,000 budget")

    # ── Next Steps ────────────────────────────────────────────────────────────
    st.header("Next Steps")
    c1, c2 = st.columns(2)
    with c1:
        st.warning("**Unresolved items before buying:**\n- Price/DR for **pt.egamersworld.com** (score 13 — price TBD)\n- Verify **financial-news.co.uk** + **sevillaBN** independently\n- Lock Dubai RU expat outlet (ARE-ru = \\$21,640/user — Week 1!)")
    with c2:
        st.markdown("**🔗 UTM Link Generator**")
        utm_base = st.text_input("Landing page", value="https://kolo.xyz", key="utm_base")
        utm_campaign = st.text_input("Campaign", value="march2026", key="utm_campaign")

        # Auto-generate UTM links for all confirmed outlets
        all_outlets = []
        for lang_key, sites in DATA["march_outlets"].items():
            for s in sites:
                if "TBD" not in s["name"]:
                    all_outlets.append({"outlet": s["name"], "lang": lang_key})

        if all_outlets:
            utm_rows = []
            for o in all_outlets:
                slug = o["outlet"].strip().replace(" ", "_").lower()
                link = (
                    f"{utm_base.rstrip('/')}?"
                    f"utm_source={slug}"
                    f"&utm_medium=sponsored_article"
                    f"&utm_campaign={utm_campaign}"
                    f"&utm_content={o['lang']}"
                )
                utm_rows.append({"Outlet": o["outlet"], "Lang": o["lang"].upper(), "UTM Link": link})

            utm_df = pd.DataFrame(utm_rows)
            st.dataframe(
                utm_df,
                use_container_width=True,
                hide_index=True,
                column_config={"UTM Link": st.column_config.LinkColumn("UTM Link", width="large")},
            )
            # Copy-all block
            all_links = "\n".join([f"{r['Outlet']}: {r['UTM Link']}" for r in utm_rows])
            st.download_button("📋 Download all UTM links", data=all_links, file_name="utm_links.txt", mime="text/plain")

        # Custom UTM for outlets not in the list
        with st.expander("Custom UTM"):
            custom_outlet = st.text_input("Outlet domain", placeholder="e.g. newsite.com", key="utm_custom_outlet")
            custom_lang = st.selectbox("Language", ["en", "ru", "it", "es", "pl", "pt", "id", "ro"], key="utm_custom_lang")
            if custom_outlet:
                slug = custom_outlet.strip().replace(" ", "_").lower()
                link = (
                    f"{utm_base.rstrip('/')}?"
                    f"utm_source={slug}"
                    f"&utm_medium=sponsored_article"
                    f"&utm_campaign={utm_campaign}"
                    f"&utm_content={custom_lang}"
                )
                st.code(link, language=None)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 · PUBLICATION ROI
# ══════════════════════════════════════════════════════════════════════════════

def page_publication_roi():
    st.title("💰 Stage 5 · Publication ROI")
    st.caption(
        "3-layer model: direct referral + SEO compound + AI citation traffic (90-day) × LTV by language · "
        "LTV source: Hex BigQuery cohort Oct 2025–Mar 2026"
    )

    # ── Assumption Controls ───────────────────────────────────────────────────
    with st.expander("⚙️ Model Assumptions", expanded=False):
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            article_ctr  = st.slider("% of outlet traffic that sees article",
                                     0.05, 0.50, 0.20, 0.05,
                                     help="Typical sponsored post: 0.10–0.25% of monthly visitors")
            ref_ctr      = st.slider("% of article readers who click to kolo.in",
                                     0.5, 5.0, 1.5, 0.5,
                                     help="Crypto-interested audience: 1–3%")
        with ac2:
            seo_months   = st.slider("SEO compound window (months)", 1, 6, 3,
                                     help="How many months to count the backlink traffic lift")
            default_rank = st.slider("Assumed current rank if unknown", 10, 30, 20,
                                     help="Where kolo.in ranks for target keyword without this link")
            ai_search_share = st.slider("AI share of search (%)", 2, 20, 8,
                                        help="% of search traffic now going through AI engines (ChatGPT, Perplexity, Google AI)")
            ai_search_frac = ai_search_share / 100.0
        with ac3:
            st.markdown("**LTV by language (from Hex)**")
            for lang, ltv in LTV_BY_LANG.items():
                cr = CONVERSION_RATE_BY_LANG[lang]
                st.markdown(f"`{lang.upper()}` — LTV **${ltv:,}** · CR **{cr*100:.2f}%**")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_batch, tab_calc, tab_ltv = st.tabs([
        "📋 March 2026 Portfolio", "🔬 Single-outlet Calculator", "📊 LTV Benchmark"
    ])

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 1 · MARCH 2026 PORTFOLIO
    # ──────────────────────────────────────────────────────────────────────────
    with tab_batch:
        st.subheader("ROI Forecast — March 2026 Confirmed Outlets")
        st.caption("Outlets marked TBD use DR-based traffic proxy. Sorted by mid-scenario ROI.")

        # Build outlet list from DATA["march_outlets"] + traffic from collaborator catalog
        catalog_traffic: dict[str, int] = {}
        catalog_dr: dict[str, int] = {}
        for lang_outlets in RAW_OUTLETS.values():
            for dom, dr, price, spct, traffic, score, crypto in lang_outlets:
                catalog_traffic[dom.lower()] = traffic
                catalog_dr[dom.lower()] = dr

        outlet_inputs = []
        lang_map = {
            "EN": "en", "RU": "ru", "IT": "it", "ES": "es",
            "PL": "pl", "PT": "pt", "ID": "id", "RO": "en",
        }
        for lang_key, sites in DATA["march_outlets"].items():
            for s in sites:
                if "TBD" in s["name"]:
                    continue
                dom = s["name"].replace("https://", "").replace("http://", "").split("/")[0].lower()
                raw_dr  = s.get("dr") or 50
                traffic = catalog_traffic.get(dom, max(raw_dr * 800, 20_000))
                dr      = catalog_dr.get(dom, raw_dr)
                price   = s.get("price") or 0
                if price == 0:
                    continue
                outlet_inputs.append({
                    "outlet": s["name"],
                    "lang":   lang_map.get(lang_key.upper(), "en"),
                    "price":  price,
                    "traffic": traffic,
                    "dr":     dr,
                    "has_crypto": True,
                    "ai_citability": s.get("ai_citability", 1),
                })

        results = batch_roi(outlet_inputs, article_ctr, ref_ctr, seo_months, ai_search_frac)

        rows = []
        for r in results:
            m = r.mid()
            lo = r.low()
            hi = r.best()
            rows.append({
                "Outlet":       r.outlet,
                "Lang":         r.lang.upper(),
                "Price ($)":    r.price,
                "DR":           r.outlet_dr,
                "Traffic":      r.outlet_traffic,
                "LTV ($)":      int(r.ltv),
                "Conservative": f"{lo.roi_x}×",
                "Mid":          f"{m.roi_x}×",
                "Optimistic":   f"{hi.roi_x}×",
                "90d Revenue":  m.revenue,
                "Registrations":m.registrations,
                "CAC ($)":      m.cac,
                "Rating":       roi_label(m.roi_x),
                "_roi":         m.roi_x,
            })

        roi_df = pd.DataFrame(rows)

        def color_roi(row):
            v = row["_roi"]
            if v >= 10:  return ["background-color: #c3e6cb"] * len(row)
            if v >= 5:   return ["background-color: #d4edda"] * len(row)
            if v >= 2:   return ["background-color: #e8f4fd"] * len(row)
            if v >= 1:   return ["background-color: #fff3cd"] * len(row)
            return ["background-color: #ffd6d6"] * len(row)

        display_df = roi_df.drop(columns=["_roi"])
        st.dataframe(
            roi_df.style.apply(color_roi, axis=1).hide(["_roi"], axis="columns"),
            use_container_width=True, hide_index=True,
            column_config={
                "Price ($)":     st.column_config.NumberColumn("Price ($)",     format="$%d"),
                "Traffic":       st.column_config.NumberColumn("Traffic",       format="%d"),
                "LTV ($)":       st.column_config.NumberColumn("LTV/user ($)",  format="$%d"),
                "90d Revenue":   st.column_config.NumberColumn("90d Rev ($)",   format="$%d"),
                "Registrations": st.column_config.NumberColumn("Regs (mid)"),
                "CAC ($)":       st.column_config.NumberColumn("CAC ($)",       format="$%.0f"),
            },
        )

        # Summary metrics
        total_spend   = sum(r.price for r in results)
        total_rev_mid = sum(r.mid().revenue for r in results)
        total_rev_lo  = sum(r.low().revenue for r in results)
        total_rev_hi  = sum(r.best().revenue for r in results)
        total_regs    = sum(r.mid().registrations for r in results)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total spend",         f"${total_spend:,.0f}")
        m2.metric("90d revenue (cons.)", f"${total_rev_lo:,.0f}",  f"{total_rev_lo/total_spend:.1f}× ROI")
        m3.metric("90d revenue (mid)",   f"${total_rev_mid:,.0f}", f"{total_rev_mid/total_spend:.1f}× ROI")
        m4.metric("90d revenue (opt.)",  f"${total_rev_hi:,.0f}",  f"{total_rev_hi/total_spend:.1f}× ROI")
        m5.metric("Registrations (mid)", f"{total_regs:.0f}",      "new users")

        # Pillar bar chart
        chart_df = roi_df.groupby("Lang").agg(
            Spend=("Price ($)", "sum"),
            Revenue=("90d Revenue", "sum"),
        ).reset_index()
        chart_df["ROI"] = (chart_df["Revenue"] / chart_df["Spend"]).round(1)
        chart_melted = chart_df.melt(id_vars="Lang", value_vars=["Spend", "Revenue"],
                                      var_name="Type", value_name="USD")
        bar = (
            alt.Chart(chart_melted)
            .mark_bar()
            .encode(
                x=alt.X("Lang:N", title="Language Pillar"),
                y=alt.Y("USD:Q", title="USD ($)", stack=None),
                color=alt.Color("Type:N", scale=alt.Scale(
                    domain=["Spend", "Revenue"],
                    range=["#6c757d", "#28a745"]
                )),
                tooltip=["Lang", "Type", alt.Tooltip("USD:Q", format="$,.0f")],
            )
            .properties(title="Spend vs 90-day Revenue by Language Pillar", height=280)
        )
        st.altair_chart(bar, use_container_width=True)

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 2 · SINGLE OUTLET CALCULATOR
    # ──────────────────────────────────────────────────────────────────────────
    with tab_calc:
        st.subheader("Single-outlet ROI Calculator")
        st.caption("Model any outlet — useful for evaluating new opportunities before buying.")

        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            c_outlet   = st.text_input("Outlet domain", "businessabc.net")
            c_lang     = st.selectbox("Language", list(LANG_LABELS.keys()),
                                      format_func=lambda k: LANG_LABELS[k])
            c_price    = st.number_input("Price ($)", 10, 1000, 100, 5)
        with cc2:
            c_traffic  = st.number_input("Monthly traffic", 1_000, 10_000_000, 100_000, 5_000)
            c_dr       = st.slider("DR", 20, 90, 60)
            c_crypto   = st.toggle("Crypto / Finance category", value=True)
        with cc3:
            c_kw_vol   = st.number_input("Target keyword monthly volume (0 = unknown)",
                                         0, 500_000, 0, 500)
            c_rank     = st.slider("Current rank for that keyword", 1, 30, default_rank)
            c_market   = st.text_input("Market override (e.g. ARE, ISR, KAZ — optional)", "")
            c_ai_cite  = st.slider("AI Citability (GEO)", 0, 3, 1,
                                   help="0=Never cited by AI, 3=Frequently cited")

        roi = calculate_publication_roi(
            outlet=c_outlet, lang=c_lang, price=c_price,
            outlet_traffic=c_traffic, outlet_dr=c_dr,
            keyword_volume=c_kw_vol, current_rank=c_rank,
            article_ctr_pct=article_ctr, referral_to_site_pct=ref_ctr,
            seo_months=seo_months, market=c_market or None,
            has_crypto_category=c_crypto,
            ai_citability=c_ai_cite, ai_share_of_search=ai_search_frac,
        )

        st.divider()
        sc1, sc2, sc3 = st.columns(3)
        for col, key, emoji in [(sc1, "conservative", "🔵"), (sc2, "mid", "🟢"), (sc3, "optimistic", "🟡")]:
            s = roi.scenarios[key]
            with col:
                st.markdown(f"### {emoji} {key.capitalize()}")
                st.metric("90-day revenue",  f"${s.revenue:,.0f}")
                st.metric("ROI",             f"{s.roi_x}×",      roi_label(s.roi_x))
                st.metric("Registrations",   f"{s.registrations:.1f} users")
                st.metric("CAC",             f"${s.cac:.0f}/user")
                st.metric("Payback",         f"{s.payback_days} days")
                st.caption(f"Referral: {s.referral_visits:,} · SEO: {s.seo_visits_90d:,} · AI: {s.ai_visits_90d:,} visits")

        st.info(
            f"**Assumptions:** LTV = ${roi.ltv:,}/user · "
            f"Conversion rate = {roi.cr*100:.2f}% · "
            f"Article CTR = {article_ctr:.2f}% of outlet traffic"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 3 · LTV BENCHMARK
    # ──────────────────────────────────────────────────────────────────────────
    with tab_ltv:
        st.subheader("LTV × Conversion Rate by Language Pillar")
        st.caption("Why language choice matters more than outlet DR. Source: Hex BigQuery cohort.")

        ltv_rows = []
        for lang, ltv in LTV_BY_LANG.items():
            cr  = CONVERSION_RATE_BY_LANG[lang]
            rev_per_1k = ltv * cr * 1000
            ltv_rows.append({
                "Language":         LANG_LABELS[lang],
                "LTV/user ($)":     ltv,
                "Conv. rate":       cr,
                "Rev / 1K visits":  round(rev_per_1k),
                "vs EN baseline":   f"{ltv / LTV_BY_LANG['en']:.1f}×",
            })
        ltv_rows.sort(key=lambda r: r["Rev / 1K visits"], reverse=True)
        ltv_df = pd.DataFrame(ltv_rows)

        def color_ltv(row):
            v = row["LTV/user ($)"]
            if v >= 6000: return ["background-color: #c3e6cb"] * len(row)
            if v >= 3000: return ["background-color: #d4edda"] * len(row)
            if v >= 2000: return ["background-color: #e8f4fd"] * len(row)
            return [""] * len(row)

        st.dataframe(
            ltv_df.style.apply(color_ltv, axis=1),
            use_container_width=True, hide_index=True,
            column_config={
                "LTV/user ($)":    st.column_config.NumberColumn("LTV/user ($)",    format="$%d"),
                "Conv. rate":      st.column_config.NumberColumn("Conv. rate",      format="%.2%%"),
                "Rev / 1K visits": st.column_config.NumberColumn("Rev / 1K visits", format="$%d"),
            },
        )

        st.info(
            "**Key insight:** A Russian-language outlet delivers **2×** the revenue per visit vs English, "
            "and a Dubai-Russian outlet (ARE-ru) delivers **$21,640/user** — 6× the English baseline. "
            "Prioritise RU-language outlets even at lower DR or higher price."
        )

        # Market-lang combo table
        from publication_roi import LTV_BY_MARKET_LANG
        ml_rows = [
            {"Market-Lang": f"{m}-{l.upper()}", "LTV/user ($)": v,
             "vs EN": f"{v/LTV_BY_LANG['en']:.1f}×"}
            for (m, l), v in sorted(LTV_BY_MARKET_LANG.items(),
                                    key=lambda x: x[1], reverse=True)
        ]
        st.subheader("High-value Market × Language Combos")
        st.caption("Outlets that reach these specific audience segments command premium ROI.")
        st.dataframe(
            pd.DataFrame(ml_rows),
            use_container_width=True, hide_index=True,
            column_config={
                "LTV/user ($)": st.column_config.NumberColumn("LTV/user ($)", format="$%d"),
            },
        )


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — PR GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

# Briefs used by both Content Plan page and PR Generator
BRIEFS = [
    {"#": 1,  "Title": "How to Spend Crypto with a Visa Card in 2026",          "Lang": "EN",    "Market": "Global",      "KW": "how to spend crypto with a visa card",  "Words": 1500, "Priority": "High"},
    {"#": 2,  "Title": "Best Crypto Debit Card in the UK 2026",                 "Lang": "EN",    "Market": "GBR",         "KW": "best crypto card UK 2026",              "Words": 1200, "Priority": "High"},
    {"#": 3,  "Title": "Crypto Card for UAE Expats 2026: Spend USDT in Dubai",  "Lang": "EN",    "Market": "ARE",         "KW": "crypto card UAE / USDT card UAE",       "Words": 1200, "Priority": "High"},
    {"#": 4,  "Title": "Najlepsza karta krypto w Polsce 2026",                  "Lang": "PL",    "Market": "POL",         "KW": "karta krypto Polska",                   "Words": 1000, "Priority": "Medium"},
    {"#": 5,  "Title": "Melhor Cartao Cripto no Brasil 2026: Gaste USDT",       "Lang": "PT",    "Market": "BRA",         "KW": "cartao cripto Brasil / cartao USDT",    "Words": 1000, "Priority": "Medium"},
    {"#": 6,  "Title": "Migliore Carta Crypto in Italia 2026",                  "Lang": "IT",    "Market": "ITA",         "KW": "carta crypto Italia",                   "Words": 1000, "Priority": "Medium"},
    {"#": 7,  "Title": "Kartu Kripto Terbaik di Indonesia 2026",                "Lang": "ID",    "Market": "IDN",         "KW": "kartu kripto Indonesia",                "Words": 1000, "Priority": "Medium"},
    {"#": 8,  "Title": "Alternativa Trustee Plus: luchshaya kripto-karta 2026", "Lang": "RU",    "Market": "CIS/UKR",     "KW": "alternativa trustee plus",              "Words": 1200, "Priority": "High"},
    {"#": 9,  "Title": "Cel mai bun card crypto in Romania 2026",               "Lang": "RO",    "Market": "ROU",         "KW": "card crypto Romania",                   "Words": 1000, "Priority": "High"},
    {"#": 10, "Title": "Crypto Card for Business 2026: Pay with USDT",          "Lang": "EN",    "Market": "Global B2B",  "KW": "crypto card business / USDT card B2B",  "Words": 1400, "Priority": "Medium"},
]

def _get_all_briefs():
    """Return BRIEFS + any gap briefs from GEO audit."""
    all_briefs = list(BRIEFS)
    geo_results = st.session_state.get("geo_audit_results", [])
    if geo_results:
        existing_kws = {b["KW"].lower() for b in BRIEFS}
        not_visible = [r for r in geo_results if not r.get("error") and not r.get("kolo_visible")]
        for i, r in enumerate(not_visible):
            q = r["query"]
            if any(q.lower() in kw for kw in existing_kws):
                continue
            all_briefs.append({
                "#": 100 + i,
                "Title": f"{q.replace('crypto', 'Crypto').title()} — Complete Guide 2026",
                "Lang": "EN",
                "Market": "Global",
                "KW": q,
                "Words": 1200,
                "Priority": "GEO Gap",
            })
    return all_briefs


def page_pr_generator():
    st.title("📝 Stage 6 · PR Generator")
    st.caption("Generate SEO+GEO-optimized press releases, revise with AI, translate, and track publications")

    api_key = st.session_state.get("anthropic_token")

    tab_gen, tab_trans, tab_track = st.tabs([
        "Generate Draft", "Translate", "Track Publications"
    ])

    # ── Tab 1: Generate Draft ─────────────────────────────────────────────
    with tab_gen:
        st.subheader("Generate English Draft")
        mode = st.radio("Source", ["Pick from briefs", "Custom brief"], horizontal=True)

        if mode == "Pick from briefs":
            all_briefs = _get_all_briefs()
            brief_titles = [f"{'🔍 GEO GAP — ' if b['#'] >= 100 else ''}#{b['#']} — {b['Title']}" for b in all_briefs]
            sel = st.selectbox("Select brief", brief_titles)
            idx = brief_titles.index(sel)
            brief = all_briefs[idx]
            label = "**🔍 GEO Gap** · " if brief.get("Priority") == "GEO Gap" else ""
            st.markdown(f"{label}**KW:** {brief['KW']} · **Market:** {brief['Market']} · **Words:** ~{brief['Words']}")
        else:
            brief = {
                "Title": st.text_input("Title", placeholder="Best crypto card for..."),
                "KW": st.text_input("Primary keyword", placeholder="crypto card UK"),
                "Market": st.text_input("Target market", value="Global"),
                "Words": st.number_input("Word count", value=1200, step=100),
                "Priority": "Medium",
            }

        col1, col2 = st.columns(2)
        with col1:
            brief["angle"] = st.text_input("Angle (optional)", placeholder="e.g. expat relocation guide")
        with col2:
            brief["hooks"] = st.text_input("Hooks to include (optional)", placeholder="e.g. USDT TRC20, Telegram mini-app")

        if st.button("🚀 Generate EN Draft", type="primary", disabled=not api_key):
            if not api_key:
                st.error("Add your Anthropic API key in the sidebar.")
            else:
                with st.spinner("Generating press release..."):
                    try:
                        draft = generate_press_release(api_key, brief)
                        st.session_state["pr_en_draft"] = draft
                        st.session_state["pr_draft_version"] = st.session_state.get("pr_draft_version", 0) + 1
                        st.session_state["pr_brief"] = brief
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

        if not api_key:
            st.info("Enter your Anthropic API key in the sidebar to enable generation.")

        draft = st.session_state.get("pr_en_draft", "")
        if draft:
            # Use version counter as part of key to force widget refresh on new content
            ver = st.session_state.get("pr_draft_version", 0)
            edited = st.text_area("Edit draft", value=draft, height=400, key=f"pr_draft_editor_{ver}")
            st.session_state["pr_en_draft"] = edited
            st.download_button("Download .md", data=edited, file_name="press_release_en.md", mime="text/markdown")

            # ── AI Revision ────────────────────────────────────────────
            st.divider()
            st.subheader("Revise with AI")
            revision_instructions = st.text_area(
                "What should be changed?",
                placeholder="e.g. Make it shorter, add more data about UAE market, change tone to more formal, remove the section about...",
                height=100,
                key="revision_instructions",
            )
            if st.button("✏️ Revise Draft", type="primary", disabled=not api_key or not revision_instructions):
                with st.spinner("Revising..."):
                    try:
                        revised = revise_press_release(api_key, edited, revision_instructions)
                        st.session_state["pr_en_draft"] = revised
                        st.session_state["pr_draft_version"] = ver + 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Revision failed: {e}")

    # ── Tab 2: Translate ──────────────────────────────────────────────────
    with tab_trans:
        st.subheader("Translate to Target Languages")
        source = st.session_state.get("pr_en_draft", "")
        if not source:
            st.warning("Generate an English draft first (Tab 1).")
        else:
            st.text_area("Source (EN)", value=source[:500] + "..." if len(source) > 500 else source, height=150, disabled=True)
            target_langs = st.multiselect(
                "Target languages",
                options=["ru", "it", "es", "pl", "pt", "id", "ro"],
                default=["ru", "it", "es", "pl", "pt", "id"],
                format_func=lambda x: LANG_NAMES.get(x, x),
            )
            if st.button("🌍 Translate All", type="primary", disabled=not api_key):
                translations = st.session_state.get("pr_translations", {})
                progress = st.progress(0)
                for i, lang in enumerate(target_langs):
                    with st.spinner(f"Translating to {LANG_NAMES.get(lang, lang)}..."):
                        try:
                            translations[lang] = translate_press_release(api_key, source, lang)
                        except Exception as e:
                            st.error(f"Translation to {lang} failed: {e}")
                    progress.progress((i + 1) / len(target_langs))
                st.session_state["pr_translations"] = translations
                st.success(f"Translated to {len(translations)} languages!")

            translations = st.session_state.get("pr_translations", {})
            for lang, text in translations.items():
                with st.expander(f"🌐 {LANG_NAMES.get(lang, lang).upper()}", expanded=False):
                    edited = st.text_area(f"Edit {lang}", value=text, height=400, key=f"trans_{lang}")
                    translations[lang] = edited
                    st.download_button(
                        f"Download {lang}.md", data=edited,
                        file_name=f"press_release_{lang}.md", mime="text/markdown",
                        key=f"dl_{lang}",
                    )
            if translations:
                st.session_state["pr_translations"] = translations

    # ── Tab 3: Track Publications ─────────────────────────────────────────
    with tab_track:
        st.subheader("Track Published Articles")
        st.caption("Add publication links when articles are paid and live. Data feeds into Monthly Evaluation.")

        # Initialize tracking data
        if "publications" not in st.session_state:
            # Pre-fill with March outlets
            rows = []
            for lang_key, sites in DATA["march_outlets"].items():
                for s in sites:
                    if "TBD" in s["name"]:
                        continue
                    rows.append({
                        "Outlet": s["name"],
                        "Lang": lang_key.upper(),
                        "Price ($)": s.get("price") or 0,
                        "Status": "Planned",
                        "Publication URL": "",
                        "Post to X": "",
                    })
            st.session_state["publications"] = pd.DataFrame(rows)

        pub_df = st.data_editor(
            st.session_state["publications"],
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    options=["Planned", "Draft Sent", "Paid", "Published", "Rejected"],
                    default="Planned",
                ),
                "Publication URL": st.column_config.LinkColumn("Publication URL"),
                "Post to X": st.column_config.LinkColumn("Post to X"),
            },
            key="pub_editor",
        )
        st.session_state["publications"] = pub_df

        # Summary metrics
        if not pub_df.empty:
            total = len(pub_df)
            published = len(pub_df[pub_df["Status"] == "Published"])
            paid = len(pub_df[pub_df["Status"] == "Paid"])
            total_spent = pub_df[pub_df["Status"].isin(["Paid", "Published"])]["Price ($)"].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Articles", total)
            col2.metric("Published", published)
            col3.metric("Paid (awaiting)", paid)
            col4.metric("Total Spent", f"${total_spent:,.0f}")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — MONTHLY EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def page_monthly_eval():
    st.title("📉 Stage 7 · Monthly Evaluation")
    st.caption("Compare actual vs projected ROI for published articles")

    notion_tok = st.session_state.get("notion_token")

    tab_input, tab_report, tab_ahrefs = st.tabs([
        "Input Results", "Evaluation Report", "Ahrefs Data"
    ])

    # ── Tab 1: Input Results ──────────────────────────────────────────────
    with tab_input:
        st.subheader("Enter Publication Results")
        eval_month = st.selectbox("Month to evaluate", ["2026-03", "2026-04", "2026-05", "2026-06"], key="eval_month_sel")

        # Pre-fill from march_outlets for 2026-03
        if eval_month == "2026-03":
            default_rows = []
            for lang_key, sites in DATA["march_outlets"].items():
                for s in sites:
                    if "TBD" in s["name"]:
                        continue
                    default_rows.append({
                        "Outlet": s["name"],
                        "Lang": lang_key.upper(),
                        "Price": s.get("price") or 0,
                        "Publication URL": "",
                        "Referral Traffic": 0,
                        "Registrations": 0,
                        "Revenue ($)": 0.0,
                    })
        else:
            default_rows = [{"Outlet": "", "Lang": "EN", "Price": 0, "Publication URL": "",
                            "Referral Traffic": 0, "Registrations": 0, "Revenue ($)": 0.0}]

        if f"eval_data_{eval_month}" not in st.session_state:
            st.session_state[f"eval_data_{eval_month}"] = pd.DataFrame(default_rows)

        edited_df = st.data_editor(
            st.session_state[f"eval_data_{eval_month}"],
            use_container_width=True,
            num_rows="dynamic",
            key=f"eval_editor_{eval_month}",
        )
        st.session_state[f"eval_data_{eval_month}"] = edited_df

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Results"):
                results = []
                for _, row in edited_df.iterrows():
                    results.append(PublicationResult(
                        outlet=row.get("Outlet", ""),
                        lang=row.get("Lang", "en").lower(),
                        price=float(row.get("Price", 0)),
                        publication_url=row.get("Publication URL") or None,
                        actual_referral_traffic=int(row.get("Referral Traffic", 0)),
                        actual_registrations=int(row.get("Registrations", 0)),
                        actual_revenue=float(row.get("Revenue ($)", 0)),
                    ))
                st.session_state[f"eval_results_{eval_month}"] = results
                st.success(f"Saved {len(results)} results for {eval_month}")

        # Auto-fill from Track Publications tab if available
        with col2:
            if st.button("📥 Import from Track Publications"):
                pubs = st.session_state.get("publications")
                if pubs is not None and not pubs.empty:
                    published = pubs[pubs["Status"].isin(["Paid", "Published"])]
                    if not published.empty:
                        import_rows = []
                        for _, row in published.iterrows():
                            import_rows.append({
                                "Outlet": row["Outlet"],
                                "Lang": row["Lang"],
                                "Price": float(row.get("Price ($)", 0)),
                                "Publication URL": row.get("Publication URL", ""),
                                "Referral Traffic": 0,
                                "Registrations": 0,
                                "Revenue ($)": 0.0,
                            })
                        st.session_state[f"eval_data_{eval_month}"] = pd.DataFrame(import_rows)
                        st.rerun()
                    else:
                        st.warning("No paid/published articles found in Track Publications.")
                else:
                    st.info("No tracking data yet. Add articles in PR Generator → Track Publications.")

    # ── Tab 2: Evaluation Report ──────────────────────────────────────────
    with tab_report:
        st.subheader("Actual vs Projected")
        eval_month = st.session_state.get("eval_month_sel", "2026-03")
        results = st.session_state.get(f"eval_results_{eval_month}")

        if not results:
            st.info("Save results in the Input tab first.")
        else:
            # Get projections from the existing ROI model
            from publication_roi import batch_roi as _batch_roi
            outlet_inputs = []
            for r in results:
                outlet_inputs.append({
                    "outlet": r.outlet, "lang": r.lang,
                    "price": r.price, "traffic": 20_000, "dr": 50,
                    "has_crypto": True,
                })
            projections = _batch_roi(outlet_inputs) if outlet_inputs else []
            evaluation = evaluate_month(eval_month, results, projections)

            # KPI cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Spend", f"${evaluation.total_spend:,.0f}")
            c2.metric("Actual Revenue", f"${evaluation.total_actual_revenue:,.0f}")
            c3.metric("Projected Revenue", f"${evaluation.total_projected_revenue_mid:,.0f}")
            ratio_pct = (evaluation.actual_vs_projected_ratio - 1) * 100
            c4.metric("vs Projected", f"{evaluation.actual_vs_projected_ratio:.1f}x",
                      delta=f"{ratio_pct:+.0f}%" if evaluation.total_projected_revenue_mid > 0 else None)

            # Comparison table
            rows = []
            for r in evaluation.publications:
                proj_rev = r.projected.scenarios[1].revenue if r.projected and len(r.projected.scenarios) > 1 else 0
                rows.append({
                    "Outlet": r.outlet,
                    "Lang": r.lang.upper(),
                    "Price ($)": r.price,
                    "Actual Revenue ($)": r.actual_revenue,
                    "Projected Revenue ($)": proj_rev,
                    "Actual ROI": f"{r.actual_revenue / r.price:.1f}x" if r.price else "—",
                    "Registrations": r.actual_registrations,
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Bar chart: actual vs projected
            if rows:
                chart_data = pd.DataFrame(rows)
                chart_data = chart_data[chart_data["Actual Revenue ($)"] > 0]
                if not chart_data.empty:
                    melted = pd.melt(
                        chart_data, id_vars=["Outlet"],
                        value_vars=["Actual Revenue ($)", "Projected Revenue ($)"],
                        var_name="Type", value_name="Revenue",
                    )
                    chart = alt.Chart(melted).mark_bar().encode(
                        x=alt.X("Outlet:N", sort="-y"),
                        y="Revenue:Q",
                        color="Type:N",
                        xOffset="Type:N",
                    ).properties(height=350)
                    st.altair_chart(chart, use_container_width=True)

            # Insights
            if evaluation.insights:
                st.subheader("Key Insights")
                for insight in evaluation.insights:
                    st.markdown(f"- {insight}")
            if evaluation.top_performer:
                st.success(f"🏆 Top performer: **{evaluation.top_performer}**")
            if evaluation.worst_performer and evaluation.worst_performer != evaluation.top_performer:
                st.warning(f"⚠️ Worst performer: **{evaluation.worst_performer}**")

            st.session_state[f"eval_report_{eval_month}"] = evaluation

    # ── Tab 3: Ahrefs Data ────────────────────────────────────────────────
    with tab_ahrefs:
        st.subheader("Ahrefs Integration")
        if ahrefs_hook.is_available():
            st.success("Ahrefs is connected!")
            st.info("Ahrefs data will auto-populate when evaluating results.")
        else:
            st.info("⏳ Ahrefs integration not yet connected.\n\n"
                    "When the Ahrefs MCP connector is available, this tab will "
                    "auto-populate with:\n"
                    "- Backlink count per publication\n"
                    "- Referring domains\n"
                    "- Organic traffic from published articles\n"
                    "- Domain Rating changes for kolo.in")
            st.markdown("**Ahrefs MCP UUID:** `098cb32a-ba21-4770-97dd-78bb54655419`")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8 — MONTHLY PLANNER
# ══════════════════════════════════════════════════════════════════════════════

def page_monthly_planner():
    st.title("🗓️ Stage 8 · Monthly Planner")
    st.caption("Full cycle: evaluate last month → recommend next → approve → push to Notion")

    api_key = st.session_state.get("anthropic_token")
    notion_tok = st.session_state.get("notion_token")

    tab_rec, tab_review, tab_approve = st.tabs([
        "Analyze + Recommend", "Review Plan", "Approve + Push"
    ])

    # ── Tab 1: Analyze + Recommend ────────────────────────────────────────
    with tab_rec:
        st.subheader("Generate Next Month's Plan")

        col1, col2 = st.columns(2)
        with col1:
            plan_month = st.selectbox("Planning for", ["2026-04", "2026-05", "2026-06"], key="plan_month_sel")
        with col2:
            budget = st.number_input("Budget ($)", value=2000, step=100, min_value=500, max_value=10000)

        # Show last month's summary if available
        prev_months = {"2026-04": "2026-03", "2026-05": "2026-04", "2026-06": "2026-05"}
        prev = prev_months.get(plan_month, "2026-03")
        prev_eval = st.session_state.get(f"eval_report_{prev}")

        if prev_eval:
            st.info(f"**{prev} Summary:** ${prev_eval.total_spend:,.0f} spent → "
                    f"${prev_eval.total_actual_revenue:,.0f} revenue "
                    f"({prev_eval.actual_vs_projected_ratio:.1f}x vs projected)")
        else:
            st.warning(f"No evaluation data for {prev}. Go to Monthly Eval → Input Results first, "
                       "or the recommendation will be based on projected data only.")

        if st.button("🧠 Generate Recommendation", type="primary", disabled=not api_key):
            if not api_key:
                st.error("Add Anthropic API key in sidebar.")
            else:
                with st.spinner("Analysing performance and generating plan..."):
                    try:
                        # Build last_month_results from evaluation or defaults
                        if prev_eval:
                            last_month = generate_plan_inputs(
                                prev_eval,
                                {},  # available_outlets populated below
                                budget,
                                DATA.get("countries", []),
                                DATA.get("languages", []),
                            )
                        else:
                            # Fallback: use projected data from march outlets
                            last_month = {
                                "month": prev,
                                "total_spend": 1717,
                                "total_actual_revenue": 0,
                                "actual_vs_projected": 0,
                                "publications": [],
                                "insights": ["No actual data yet — recommending based on projections."],
                                "top_countries": [],
                                "language_ltv": {k: v for k, v in LTV_BY_LANG.items()},
                                "budget": budget,
                            }

                        # Get available outlets
                        available = []
                        for lang_code in ["en", "ru", "it", "es", "pl", "pt", "id"]:
                            try:
                                from collaborator_outlets import get_outlets
                                outlets = get_outlets(lang_code, min_dr=40, max_price=250)
                                for o in outlets[:10]:
                                    available.append({
                                        "domain": o[0], "dr": o[1], "price": o[2],
                                        "search_pct": o[3], "traffic": o[4], "score": o[5],
                                        "lang": lang_code,
                                    })
                            except Exception:
                                pass

                        raw = recommend_monthly_plan(api_key, last_month, available, budget)
                        plan = parse_plan_recommendation(raw, plan_month, budget)
                        st.session_state["plan_parsed"] = plan
                        st.session_state["plan_raw"] = raw
                        st.success("Plan generated! Review it in the next tab.")
                    except Exception as e:
                        st.error(f"Recommendation failed: {e}")

        if not api_key:
            st.info("Enter your Anthropic API key in the sidebar to enable plan generation.")

    # ── Tab 2: Review Plan ────────────────────────────────────────────────
    with tab_review:
        plan = st.session_state.get("plan_parsed")
        if not plan:
            st.info("Generate a recommendation first (Tab 1).")
        else:
            st.subheader(f"Recommended Plan: {plan.month}")

            # Outlet allocations
            st.markdown("### Outlet Allocations")
            if plan.outlet_allocations:
                alloc_df = pd.DataFrame(plan.outlet_allocations)
                edited_alloc = st.data_editor(alloc_df, use_container_width=True, num_rows="dynamic", key="plan_outlets_editor")
                plan.outlet_allocations = edited_alloc.to_dict("records")

            # Content angles
            st.markdown("### Content Angles")
            if plan.content_angles:
                angles_df = pd.DataFrame(plan.content_angles)
                edited_angles = st.data_editor(angles_df, use_container_width=True, num_rows="dynamic", key="plan_angles_editor")
                plan.content_angles = edited_angles.to_dict("records")

            # Budget breakdown
            st.markdown("### Budget by Pillar")
            if plan.pillar_budgets:
                budget_df = pd.DataFrame([
                    {"Pillar": k, "Budget ($)": v} for k, v in plan.pillar_budgets.items()
                ])
                chart = alt.Chart(budget_df).mark_arc(innerRadius=50).encode(
                    theta="Budget ($):Q",
                    color="Pillar:N",
                    tooltip=["Pillar", "Budget ($)"],
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

                total = sum(plan.pillar_budgets.values())
                st.metric("Total Planned Spend", f"${total:,.0f}",
                          delta=f"${plan.budget - total:+,.0f} remaining" if total <= plan.budget else f"${total - plan.budget:,.0f} over budget")

            # ROI forecast for recommended outlets
            st.markdown("### Projected ROI")
            roi_inputs = []
            for o in plan.outlet_allocations:
                roi_inputs.append({
                    "outlet": o.get("outlet", ""),
                    "lang": o.get("lang", "en"),
                    "price": o.get("price", 100),
                    "traffic": 20_000,
                    "dr": 50,
                    "has_crypto": True,
                })
            if roi_inputs:
                try:
                    rois = batch_roi(roi_inputs)
                    roi_rows = []
                    for r in rois:
                        if not r.scenarios:
                            continue
                        m = r.scenarios[1] if len(r.scenarios) > 1 else r.scenarios[0]
                        roi_rows.append({
                            "Outlet": r.outlet, "Lang": r.lang.upper(),
                            "Price ($)": r.price, "Mid ROI": f"{m.roi_x}x",
                            "90d Revenue ($)": m.revenue, "Regs": m.registrations,
                        })
                    if roi_rows:
                        st.dataframe(pd.DataFrame(roi_rows), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.warning(f"Could not compute ROI projections: {e}")

            # Reasoning
            st.markdown("### Reasoning")
            st.markdown(plan.reasoning)

            st.session_state["plan_parsed"] = plan

    # ── Tab 3: Approve + Push ─────────────────────────────────────────────
    with tab_approve:
        plan = st.session_state.get("plan_parsed")
        if not plan:
            st.info("Generate and review a plan first.")
        else:
            st.subheader(f"Plan: {plan.month} — Status: {plan.status.upper()}")

            # Summary
            n_outlets = len(plan.outlet_allocations)
            n_angles = len(plan.content_angles)
            total_budget = sum(o.get("price", 0) for o in plan.outlet_allocations)
            st.markdown(f"**{n_outlets} outlets** · **{n_angles} content angles** · **${total_budget:,.0f} total spend**")

            col1, col2 = st.columns(2)
            with col1:
                if plan.status == "draft":
                    if st.button("✅ Approve Plan", type="primary"):
                        plan.status = "approved"
                        st.session_state["plan_parsed"] = plan
                        st.rerun()
                elif plan.status == "approved":
                    st.success("Plan approved!")
                elif plan.status == "pushed":
                    st.success("Plan pushed to Notion!")

            with col2:
                if plan.status == "approved" and notion_tok:
                    if st.button("📤 Push to Notion", type="primary"):
                        with st.spinner("Creating Notion pages..."):
                            try:
                                # Create monthly plan page
                                plan_resp = create_monthly_plan_page(
                                    notion_tok, month=plan.month,
                                    plan_data={
                                        "recommended_outlets": plan.outlet_allocations,
                                        "content_angles": plan.content_angles,
                                        "pillar_budgets": plan.pillar_budgets,
                                        "reasoning": plan.reasoning,
                                    },
                                )
                                plan_url = plan_resp.get("url", "")
                                st.success(f"Plan page created: [Open in Notion]({plan_url})")

                                # Create Content Plan entries
                                entries = plan_to_notion_entries(plan)
                                created = 0
                                for entry in entries:
                                    try:
                                        create_content_plan_entry(notion_tok, **entry)
                                        created += 1
                                    except Exception as e:
                                        st.error(f"Failed to create entry for {entry.get('outlet', '?')}: {e}")

                                st.success(f"Created {created} Content Plan entries in Notion")
                                plan.status = "pushed"
                                st.session_state["plan_parsed"] = plan
                            except Exception as e:
                                st.error(f"Failed to push plan: {e}")
                elif plan.status == "approved" and not notion_tok:
                    st.error("Add Notion token in sidebar to push.")

            if plan.status == "draft":
                st.info("Review the plan in the Review tab, then approve here.")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 9 — SOCIAL LISTENING & DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════

# Search queries to find relevant posts where Kolo could be mentioned
LISTENING_QUERIES = [
    {"q": "best crypto card", "label": "Best crypto card", "geo": True},
    {"q": "crypto debit card Europe", "label": "Crypto card Europe", "geo": True},
    {"q": "spend USDT real life", "label": "Spend USDT IRL", "geo": True},
    {"q": "crypto card vs revolut", "label": "Crypto vs Revolut", "geo": False},
    {"q": "USDT Visa card", "label": "USDT Visa card", "geo": True},
    {"q": "crypto card digital nomad", "label": "Nomad crypto card", "geo": True},
    {"q": "TRC20 card", "label": "TRC20 card", "geo": True},
    {"q": "crypto card fees comparison", "label": "Card fees comparison", "geo": False},
    {"q": "telegram crypto wallet", "label": "Telegram wallet", "geo": True},
    {"q": "crypto card no KYC", "label": "Crypto card KYC", "geo": False},
]

SUBREDDITS = [
    "cryptocurrency", "CryptoCards", "TRON", "digitalnomad",
    "ethfinance", "Bitcoin", "defi", "personalfinance",
]


def page_content_distribution():
    st.title("📣 Stage 9 · Social Listening & Distribution")
    st.caption("Find relevant Reddit & Quora posts → draft helpful comments → track posting")

    api_key = st.session_state.get("anthropic_token")

    # Optional article URL to reference
    st.sidebar.divider()
    st.sidebar.subheader("📣 Distribution")
    ref_url = st.sidebar.text_input("Article URL to reference (optional)", placeholder="https://...", key="dist_ref_url")

    tab_find, tab_drafts, tab_tracker = st.tabs(["🔍 Find Posts", "✏️ Draft Comments", "📊 Tracker"])

    # ── Tab 1: Find Posts ─────────────────────────────────────────────
    with tab_find:
        st.subheader("1. Find Posts to Comment On")
        st.markdown(
            "Click the search links below — they open Reddit/Quora/Google in your browser. "
            "When you find a good post, **paste its URL** in the Draft Comments tab to generate a reply. "
            "**High GEO value:** AI engines index Reddit & Quora answers heavily."
        )

        # ── Reddit Search Links ───────────────────────────────────
        st.markdown("### 🔴 Reddit")
        st.markdown("Click to open Reddit search in your browser:")

        reddit_queries = [
            ("best crypto card", ["cryptocurrency", "CryptoCards", "digitalnomad"]),
            ("crypto debit card Europe", ["cryptocurrency", "CryptoCards", "ethfinance"]),
            ("spend USDT real life", ["cryptocurrency", "TRON", "defi"]),
            ("USDT Visa card", ["cryptocurrency", "CryptoCards"]),
            ("crypto card fees comparison", ["cryptocurrency", "CryptoCards", "personalfinance"]),
            ("crypto card digital nomad", ["digitalnomad", "cryptocurrency"]),
            ("telegram crypto wallet", ["cryptocurrency", "TRON"]),
            ("crypto card vs revolut", ["cryptocurrency", "CryptoCards"]),
            ("TRC20 card", ["TRON", "cryptocurrency"]),
            ("best way spend crypto", ["cryptocurrency", "Bitcoin", "defi"]),
        ]

        for query, subs in reddit_queries:
            encoded = query.replace(" ", "+")
            sub_links = " · ".join(
                [f"[r/{s}](https://www.reddit.com/r/{s}/search/?q={encoded}&sort=new&t=month)" for s in subs]
            )
            st.markdown(f"**{query}:** [All Reddit](https://www.reddit.com/search/?q={encoded}&sort=new&t=month) · {sub_links}")

        st.divider()

        # ── Quora Search Links ────────────────────────────────────
        st.markdown("### 🔵 Quora")
        quora_queries = [
            "best crypto card 2026", "how to spend USDT in real life",
            "crypto card Europe", "USDT Visa card review",
            "crypto debit card comparison", "is it safe to use crypto debit cards",
            "best way to spend crypto abroad", "crypto card for digital nomads",
        ]
        cols = st.columns(2)
        for i, qq in enumerate(quora_queries):
            encoded = qq.replace(" ", "+")
            with cols[i % 2]:
                st.markdown(f"[🔍 {qq}](https://www.quora.com/search?q={encoded})")

        st.divider()

        # ── Google Search Links (site:reddit.com + site:quora.com) ─
        st.markdown("### 🟢 Google (finds Reddit + Quora posts)")
        st.markdown("Google search with `site:` filter — often finds older, high-traffic posts:")
        google_queries = [
            "best crypto card", "spend USDT", "crypto Visa card",
            "USDT debit card", "crypto card fees", "telegram crypto wallet",
        ]
        cols = st.columns(2)
        for i, gq in enumerate(google_queries):
            encoded = gq.replace(" ", "+")
            with cols[i % 2]:
                st.markdown(
                    f"**{gq}:** "
                    f"[Reddit](https://www.google.com/search?q=site:reddit.com+{encoded}) · "
                    f"[Quora](https://www.google.com/search?q=site:quora.com+{encoded})"
                )

        st.divider()

        # ── Quick Add from URL ────────────────────────────────────
        st.markdown("### ➕ Quick Add Post")
        st.markdown("Found a good post? Paste its URL here to add it to the Draft Comments queue:")
        quick_url = st.text_input("Post URL", placeholder="https://www.reddit.com/r/cryptocurrency/comments/...", key="quick_add_url")
        quick_title = st.text_input("Post title (what the person is asking)", placeholder="What's the best crypto card for Europe?", key="quick_add_title")
        if st.button("Add to Queue", disabled=not quick_title):
            import re
            selected = st.session_state.get("selected_posts", [])
            # Auto-detect platform and subreddit
            platform = "Reddit"
            subreddit = ""
            if "quora.com" in quick_url:
                platform = "Quora"
            elif "news.ycombinator" in quick_url:
                platform = "HackerNews"
            reddit_match = re.search(r'reddit\.com/r/(\w+)', quick_url)
            if reddit_match:
                subreddit = reddit_match.group(1)
            selected.append({
                "title": quick_title,
                "selftext": "",
                "subreddit": subreddit,
                "url": quick_url,
                "score": 0,
                "num_comments": 0,
                "platform": platform,
            })
            st.session_state["selected_posts"] = selected
            st.success(f"Added to queue! Go to Draft Comments tab to generate a reply.")
            st.rerun()

    # ── Tab 2: Draft Comments ─────────────────────────────────────────
    with tab_drafts:
        st.subheader("Draft Comment Replies")
        st.markdown("Generate helpful comments for queued posts. Comments are written as a genuine user — not an ad.")

        selected = st.session_state.get("selected_posts", [])

        if not selected:
            st.info("Queue posts from the Find Posts tab, or add manually below.")

        # Manual post entry
        with st.expander("Add post manually"):
            manual_title = st.text_input("Post title", key="manual_title")
            manual_body = st.text_area("Post body (optional)", key="manual_body", height=80)
            manual_platform = st.selectbox("Platform", ["Reddit", "Quora", "HackerNews", "Forum"], key="manual_platform")
            manual_sub = st.text_input("Subreddit / community", key="manual_sub")
            manual_url = st.text_input("Post URL", key="manual_url")
            if st.button("Add to queue"):
                if manual_title:
                    selected.append({
                        "title": manual_title,
                        "selftext": manual_body,
                        "subreddit": manual_sub,
                        "url": manual_url,
                        "score": 0,
                        "num_comments": 0,
                        "platform": manual_platform,
                    })
                    st.session_state["selected_posts"] = selected
                    st.rerun()

        # Generate comments for queued posts
        drafts = st.session_state.get("comment_drafts", {})

        for i, post in enumerate(selected):
            platform = post.get("platform", "Reddit")
            with st.expander(
                f"{'✅' if str(i) in drafts else '⬜'} {post['title'][:60]} — "
                f"{post.get('subreddit', platform)}",
                expanded=str(i) not in drafts,
            ):
                st.markdown(f"**[{post['title']}]({post.get('url', '#')})**")
                if post.get("selftext"):
                    st.caption(post["selftext"][:200])

                col_gen, col_remove = st.columns([3, 1])
                with col_gen:
                    if st.button("🤖 Generate Comment", key=f"gencomment_{i}", disabled=not api_key):
                        with st.spinner("Drafting comment..."):
                            try:
                                comment = generate_comment_reply(
                                    api_key,
                                    post_title=post["title"],
                                    post_body=post.get("selftext", ""),
                                    platform=platform,
                                    subreddit=post.get("subreddit", ""),
                                    article_url=ref_url,
                                )
                                drafts[str(i)] = {
                                    "content": comment,
                                    "status": "draft",
                                    "post_url": post.get("url", ""),
                                    "platform": platform,
                                    "community": post.get("subreddit", ""),
                                }
                                st.session_state["comment_drafts"] = drafts
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                with col_remove:
                    if st.button("🗑️ Remove", key=f"remove_{i}"):
                        selected.pop(i)
                        drafts.pop(str(i), None)
                        st.session_state["selected_posts"] = selected
                        st.session_state["comment_drafts"] = drafts
                        st.rerun()

                # Show/edit generated comment
                if str(i) in drafts:
                    edited = st.text_area(
                        "Edit comment before posting",
                        value=drafts[str(i)]["content"],
                        height=150,
                        key=f"editcomment_{i}",
                    )
                    drafts[str(i)]["content"] = edited

                    dc1, dc2, dc3 = st.columns(3)
                    with dc1:
                        drafts[str(i)]["status"] = st.selectbox(
                            "Status", ["draft", "posted", "skipped"],
                            key=f"commentstatus_{i}",
                            index=["draft", "posted", "skipped"].index(drafts[str(i)].get("status", "draft")),
                        )
                    with dc2:
                        st.download_button(
                            "📋 Copy .txt", data=edited,
                            file_name=f"comment_{i}.txt", mime="text/plain",
                            key=f"dlcomment_{i}",
                        )
                    with dc3:
                        if post.get("url"):
                            st.markdown(f"[Open post ↗]({post['url']})")

        st.session_state["comment_drafts"] = drafts

        if not api_key:
            st.info("Enter your Anthropic API key in the sidebar to generate comments.")

    # ── Tab 3: Tracker ────────────────────────────────────────────────
    with tab_tracker:
        st.subheader("Distribution Tracker")
        drafts = st.session_state.get("comment_drafts", {})

        if drafts:
            rows = []
            for key, d in drafts.items():
                rows.append({
                    "Platform": d.get("platform", "Reddit"),
                    "Community": d.get("community", ""),
                    "Status": d.get("status", "draft"),
                    "Post URL": d.get("post_url", ""),
                    "Words": len(d.get("content", "").split()),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"Post URL": st.column_config.LinkColumn()})

            total = len(rows)
            posted = sum(1 for r in rows if r["Status"] == "posted")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Drafted", total)
            col2.metric("Posted", posted)
            col3.metric("Pending", total - posted)

            st.divider()
            st.markdown(
                "**GEO Impact:** Reddit & Quora comments are heavily indexed by "
                "ChatGPT, Perplexity, and Google AI Overviews. Each posted comment "
                "increases the chance Kolo appears in AI-generated answers for "
                "crypto card queries."
            )
        else:
            st.info("No comments drafted yet. Use Find Posts → Queue → Draft Comments.")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 10 — GEO VISIBILITY AUDIT
# ══════════════════════════════════════════════════════════════════════════════

_AUDIT_CACHE_FILE = "geo_audit_cache.json"


def _save_audit_results(results):
    """Persist audit results to a local JSON file."""
    import json
    with open(_AUDIT_CACHE_FILE, "w") as f:
        json.dump({"saved_at": pd.Timestamp.now().isoformat(), "results": results}, f, default=str)


def _load_audit_results():
    """Load cached audit results from disk."""
    import json, os
    if not os.path.exists(_AUDIT_CACHE_FILE):
        return None, None
    try:
        with open(_AUDIT_CACHE_FILE) as f:
            data = json.load(f)
        return data.get("results"), data.get("saved_at", "unknown")
    except Exception:
        return None, None


def page_geo_visibility():
    st.title("🔍 Stage 8 · GEO Visibility Audit")
    st.caption("Track Kolo's presence in Google search results vs competitors · SerpAPI free 100/month")

    serp_key = st.session_state.get("serpapi_key")

    # Load cached results on first visit (persists across sessions)
    if "geo_audit_results" not in st.session_state:
        cached, saved_at = _load_audit_results()
        if cached:
            st.session_state["geo_audit_results"] = cached
            st.session_state["geo_audit_saved_at"] = saved_at

    tab_audit, tab_plan, tab_history = st.tabs(["🔍 Run Audit", "🎯 Action Plan", "📊 History"])

    with tab_audit:
        st.subheader("Visibility Audit")
        st.markdown(
            f"Queries **{len(DEFAULT_QUERIES)}** target keywords on Google. "
            f"Checks if Kolo appears in top 10 results and which competitors rank."
        )

        if not serp_key:
            st.warning("Add your **SerpAPI key** in the sidebar to run new audits. The Action Plan tab works without it if you've run an audit before.")

        # Show queries
        with st.expander("Target queries", expanded=False):
            for i, q in enumerate(DEFAULT_QUERIES):
                st.markdown(f"{i+1}. **{q['q']}** — {q['intent']} · {q['geo']}")

        # Custom queries
        custom_q = st.text_input("Add custom query (optional)", placeholder="e.g. crypto card Poland")

        queries_to_run = [q["q"] for q in DEFAULT_QUERIES]
        if custom_q:
            queries_to_run.append(custom_q)

        if st.button(f"🚀 Run Audit ({len(queries_to_run)} queries)", type="primary", disabled=not serp_key):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, q in enumerate(queries_to_run):
                status.text(f"Searching: {q}")
                result = audit_query(serp_key, q)
                results.append(result)
                progress.progress((i + 1) / len(queries_to_run))

            st.session_state["geo_audit_results"] = results
            st.session_state["geo_audit_saved_at"] = pd.Timestamp.now().isoformat()
            _save_audit_results(results)
            status.empty()
            progress.empty()
            st.success(f"Audit complete! Results saved — Action Plan tab is ready.")

        # Display results
        results = st.session_state.get("geo_audit_results", [])
        if results:
            summary = summarize_audit(results)

            # Top metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kolo Visible", summary["visibility_score"],
                       f"{summary['kolo_visible_pct']}% of queries")
            c2.metric("Avg Position", summary["avg_kolo_position"] or "Not found")
            c3.metric("Queries Audited", summary["total_queries"])
            c4.metric("Errors", summary["errors"])

            st.divider()

            # Competitor leaderboard
            st.subheader("🏆 Competitor Visibility")
            if summary["top_competitors"]:
                comp_df = pd.DataFrame(summary["top_competitors"], columns=["Competitor", "Queries Visible"])
                comp_df["Share"] = comp_df["Queries Visible"].apply(
                    lambda x: f"{x}/{summary['total_queries'] - summary['errors']}"
                )
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            else:
                st.info("No known competitors found in results.")

            st.divider()

            # Per-query breakdown
            st.subheader("📋 Query-by-Query Results")
            rows = []
            for r in results:
                if r.get("error"):
                    rows.append({
                        "Query": r["query"],
                        "Kolo": "❌ Error",
                        "Position": "—",
                        "Top Result": r["error"][:50],
                        "Competitors": "—",
                    })
                else:
                    kolo_status = f"✅ #{r['kolo_position']}" if r["kolo_visible"] else "❌"
                    rows.append({
                        "Query": r["query"],
                        "Kolo": kolo_status,
                        "Position": r["kolo_position"] or "—",
                        "Top Result": f"{r['top_result_domain']}",
                        "Competitors": ", ".join(r["competitors_found"][:3]) or "None",
                    })

            results_df = pd.DataFrame(rows)
            st.dataframe(results_df, use_container_width=True, hide_index=True)

            # Detailed view per query
            with st.expander("Detailed results (top 10 per query)"):
                for r in results:
                    if r.get("error"):
                        continue
                    st.markdown(f"**{r['query']}**")
                    for res in r.get("results", []):
                        icon = "🟢" if res["kolo_domain"] else ("🟡" if res["kolo_mentioned"] else ("🔴" if res["competitor"] else "⚪"))
                        label = "KOLO" if res["kolo_domain"] or res["kolo_mentioned"] else (res["competitor"] or "")
                        st.markdown(f"{icon} #{res['position']} [{res['title'][:60]}]({res['link']}) {f'**{label}**' if label else ''}")
                    st.divider()

    # ── Tab 2: Action Plan (persists without re-running) ─────────────
    with tab_plan:
        results = st.session_state.get("geo_audit_results", [])
        if not results:
            st.info("Run an audit first (Run Audit tab) to generate an action plan. Results are saved to disk — you only need to run once.")
        else:
            saved_at = st.session_state.get("geo_audit_saved_at", "unknown")
            summary = summarize_audit(results)
            st.subheader(f"GEO Action Plan — Kolo visible in {summary['visibility_score']} queries")
            st.caption(f"Based on audit from: {saved_at[:16] if saved_at != 'unknown' else 'this session'} · No API key needed to view")

            # Categorize queries
            not_visible = [r for r in results if not r.get("error") and not r.get("kolo_visible")]
            visible_low = [r for r in results if r.get("kolo_position") and r["kolo_position"] > 5]
            visible_high = [r for r in results if r.get("kolo_position") and r["kolo_position"] <= 5]
            has_ai_overview = [r for r in results if r.get("ai_overview")]

            # ── Priority 1: Not visible at all ────────────────────
            if not_visible:
                st.markdown("### 🔴 Priority 1: Not Visible — Create Content")
                st.markdown("Kolo doesn't appear in top 10 for these queries. **Action: publish targeted articles.**")
                for r in not_visible:
                    competitors = ", ".join(r.get("competitors_found", [])[:3]) or "No known competitors"
                    top = r.get("top_result_domain", "—")
                    st.markdown(
                        f"- **\"{r['query']}\"** — Top result: `{top}` · Competitors: {competitors}\n"
                        f"  → Write article targeting this keyword · Publish on high-DR outlet · Add FAQ + comparison table"
                    )

                # Generate briefs suggestion
                st.divider()
                st.markdown("**Suggested article briefs:**")
                for i, r in enumerate(not_visible[:5]):
                    q = r["query"]
                    st.markdown(
                        f"{i+1}. **Title:** \"Best {q.title()} in 2026 — Complete Guide\" · "
                        f"**KW:** `{q}` · **Structure:** question headers + FAQ + comparison table + stat paragraphs"
                    )

            # ── Priority 2: Visible but low position ──────────────
            if visible_low:
                st.divider()
                st.markdown("### 🟡 Priority 2: Low Position (#6-10) — Optimize Existing")
                st.markdown("Kolo appears but below the fold. **Action: boost with backlinks + Reddit/Quora mentions.**")
                for r in visible_low:
                    st.markdown(
                        f"- **\"{r['query']}\"** — Position #{r['kolo_position']}\n"
                        f"  → Post on Reddit/Quora answering this query · Link to existing article · Add internal links"
                    )

            # ── Priority 3: Good position ─────────────────────────
            if visible_high:
                st.divider()
                st.markdown("### 🟢 Priority 3: Strong Position (#1-5) — Defend & Expand")
                st.markdown("Kolo ranks well. **Action: maintain + create related content.**")
                for r in visible_high:
                    st.markdown(
                        f"- ✅ **\"{r['query']}\"** — Position #{r['kolo_position']}"
                    )

            # ── Competitor Analysis ────────────────────────────────
            if summary["top_competitors"]:
                st.divider()
                st.markdown("### 🏆 Competitor Dominance — Where to Attack")
                for comp, count in summary["top_competitors"]:
                    total_valid = summary["total_queries"] - summary["errors"]
                    pct = round(count / max(total_valid, 1) * 100)
                    if pct > 50:
                        action = "**High threat** — create comparison articles (Kolo vs " + comp + ")"
                    elif pct > 25:
                        action = "Moderate presence — mention in Reddit/Quora answers as alternative"
                    else:
                        action = "Low presence — monitor"
                    st.markdown(f"- **{comp}** visible in {count}/{total_valid} queries ({pct}%) → {action}")

            # ── AI Overview Strategy ──────────────────────────────
            if has_ai_overview:
                st.divider()
                st.markdown("### 🤖 AI Overview Detected")
                ai_kolo = sum(1 for r in has_ai_overview if r["ai_overview"].get("kolo_mentioned"))
                st.markdown(
                    f"Google AI Overviews appeared for **{len(has_ai_overview)}** queries. "
                    f"Kolo mentioned in **{ai_kolo}** of them."
                )
                if ai_kolo < len(has_ai_overview):
                    st.markdown(
                        "**Action:** Restructure articles for AI citability:\n"
                        "- Add FAQ sections with exact target queries as questions\n"
                        "- Use question-format H2 headers\n"
                        "- Include self-contained stat sentences (\"Kolo supports USDT spending in 99 countries\")\n"
                        "- Post answers on Reddit/Quora — AI engines heavily cite these"
                    )

            # ── Weekly Action Checklist ────────────────────────────
            st.divider()
            st.markdown("### 📋 This Week's GEO Checklist")
            n_missing = len(not_visible)
            n_low = len(visible_low)
            top_comp = summary["top_competitors"][0][0] if summary["top_competitors"] else "Crypto.com"

            checklist = []
            if n_missing > 0:
                checklist.append(f"Write {min(n_missing, 3)} articles targeting missing queries (see Priority 1 above)")
            if n_missing > 0:
                checklist.append(f"Publish on outlets with DR 40+ for missing keyword coverage")
            if n_low > 0:
                checklist.append(f"Post {min(n_low, 3)} Reddit/Quora answers for low-position queries")
            checklist.append(f"Create comparison article: Kolo vs {top_comp}")
            checklist.append("Add FAQ sections to all published articles that don't have them")
            checklist.append("Test 5 queries on ChatGPT + Perplexity — log if Kolo appears")
            checklist.append(f"Re-run GEO audit next week to track progress")

            for item in checklist:
                st.markdown(f"- [ ] {item}")

    with tab_history:
        st.subheader("Audit History")
        st.info("Run audits regularly (weekly) to track visibility improvements over time. Results are stored in session — for persistence, download as CSV.")

        results = st.session_state.get("geo_audit_results", [])
        if results:
            summary = summarize_audit(results)
            # Export
            export_rows = []
            for r in results:
                export_rows.append({
                    "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                    "query": r["query"],
                    "kolo_visible": r.get("kolo_visible", False),
                    "kolo_position": r.get("kolo_position"),
                    "competitors": ", ".join(r.get("competitors_found", [])),
                    "top_result": r.get("top_result_domain", ""),
                })
            export_df = pd.DataFrame(export_rows)
            csv = export_df.to_csv(index=False)
            st.download_button("📥 Download audit as CSV", data=csv, file_name=f"geo_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")
            st.dataframe(export_df, use_container_width=True, hide_index=True)
        else:
            st.info("No audit results yet. Run an audit in the first tab.")


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

pg = st.navigation({
    "": [
        st.Page(page_dashboard,        title="Dashboard",        icon="🤖", default=True),
    ],
    "Stages": [
        st.Page(page_market_intel,     title="Market Intel",     icon="📊"),
        st.Page(page_kolo_metrics,     title="Kolo Metrics",     icon="📈"),
        st.Page(page_content_plan,     title="Content Plan",     icon="✍️"),
        st.Page(page_outlet_matching,  title="Outlet Matching",  icon="🗞️"),
        st.Page(page_publication_roi,  title="Publication ROI",  icon="💰"),
    ],
    "Actions": [
        st.Page(page_pr_generator,           title="PR Generator",     icon="📝"),
        st.Page(page_content_distribution,   title="Distribution",     icon="📣"),
        st.Page(page_geo_visibility,         title="GEO Visibility",   icon="🔍"),
        st.Page(page_monthly_eval,           title="Monthly Eval",     icon="📉"),
        st.Page(page_monthly_planner,        title="Monthly Planner",  icon="🗓️"),
    ],
})
pg.run()
