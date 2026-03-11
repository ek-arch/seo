"""
app.py — Kolo SEO Intelligence Agent
Single-file Streamlit app using st.navigation().
All data lives in data_sources.py.
"""

import streamlit as st
import pandas as pd
import altair as alt
from data_sources import DATA, score_outlet_notion, outlet_verdict
from collaborator_outlets import (
    get_outlets, get_top_outlets_all_langs,
    LANG_LABELS, score_label, RAW_OUTLETS,
)

st.set_page_config(
    page_title="Kolo SEO Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://kolo.in/favicon.ico", width=32)
    st.title("Kolo SEO Agent")
    st.caption("kolo.in · crypto Visa card")
    st.divider()
    st.subheader("🔑 API Keys")
    hex_token = st.text_input("Hex API token",           type="password", placeholder="hxtp_...",    help="app.hex.tech → Settings → API keys")
    collab_token = st.text_input("Collaborator.pro token", type="password", placeholder="etVxo-...", help="collaborator.pro/user/api")
    notion_token = st.text_input("Notion token (optional)", type="password", placeholder="secret_...", help="Only needed for direct API writes")
    for k, v in [("hex_token", hex_token), ("collab_token", collab_token), ("notion_token", notion_token)]:
        if v:
            st.session_state[k] = v
    st.divider()
    st.subheader("📋 Pipeline")
    for name, status in [("Stage 1 · Market Intel", "✅"), ("Stage 2 · Kolo Metrics", "✅"),
                          ("Stage 3 · Content Plan", "✅"), ("Stage 4 · Outlet Match",  "✅")]:
        st.markdown(f"{status} {name}")
    st.divider()
    st.caption("Source: Hex BigQuery · exchanger2_db_looker\nOct 10, 2025 – Mar 1, 2026")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 0 · DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    st.title("🤖 Kolo SEO Intelligence Agent")
    st.markdown("**March 2026 plan · \\$2,000 budget · 40+ countries · 1.9–5.9× ROI forecast**")

    pc  = DATA["platform"]["post_cashback"]
    pnl = DATA["pnl"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active B2C Users",   f"{pc['active_users']:,}",        "+90% vs pre-cashback")
    c2.metric("Monthly Card Spend", f"${pc['card_spend']/1e6:.2f}M",  "+111%")
    c3.metric("Avg Daily Spend",    f"${pc['avg_daily_spend']:,}",     "+57%")
    c4.metric("Net P&L (3-month)",  f"${sum(pnl['net_pnl']):,}",      "2.04× cashback coverage")
    c5.metric("Active Countries",   "99",                              "B2C USD cards")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.subheader("📊 Stage 1 · Market Intel")
            st.markdown("- 10 competitor profiles across 9 markets\n- **Oobit** = closest CIS threat\n- **Trustee Plus alternative** = #1 keyword opportunity\n- Romania (+183%) and Switzerland = breakout markets")
        with st.container(border=True):
            st.subheader("✍️ Stage 3 · Content Plan")
            st.markdown("- 10 article briefs across 7 languages\n- Full EN draft ready (~1,500 words)\n- 90-day calendar March–May 2026\n- **Spain relocation hook** added to Russian pillar")
    with col_b:
        with st.container(border=True):
            st.subheader("📈 Stage 2 · Kolo Metrics")
            st.markdown("- **Russian users** — \\$5,940/user vs English \\$3,467 (1.7×)\n- 🇸🇪 **Sweden whale** — \\$24,570/user (9 users, \\$221K)\n- 🇺🇾 Uruguay: \\$19,982/user, 99% conversion\n- Swap fees = **#1 revenue line** (\\$137K > card spend \\$81K)")
        with st.container(border=True):
            st.subheader("🗞️ Stage 4 · Outlet Matching")
            st.markdown("- Scoring: **Notion guide 5-dimension 0–15** system\n- 9 outlets scored · **pt.egamersworld (13/15)** added · 2 unscored flagged\n- Collaborator.pro API: **⏳ pending support unlock**\n- Must-Have: search>35%, DR>40, price<\\$5/DR")

    st.divider()
    st.subheader("💡 Top 3 Actions This Week")
    st.markdown("""
| Priority | Action | Why |
|---|---|---|
| 🔴 **URGENT** | Lock Dubai RU expat outlet (Week 1, not Week 2) | ARE-ru = \\$21,640/user — highest expected-value placement |
| 🟠 **HIGH** | Update Russian article hooks: remove ISR/KAZ angles, add Spain + CIS expat | ISR/KAZ card issuance suspended — hooks no longer valid |
| 🟠 **HIGH** | Add UTM params before buying any outlet | Without attribution, 90-day ROI is unverifiable |
""")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 · MARKET INTEL
# ══════════════════════════════════════════════════════════════════════════════

def page_market_intel():
    st.title("📊 Stage 1 · Market Intel")
    st.caption("Last run: 2026-03-10 · Web search + competitor analysis")

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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 · KOLO METRICS
# ══════════════════════════════════════════════════════════════════════════════

def page_kolo_metrics():
    st.title("📈 Stage 2 · Kolo Metrics")
    st.caption("Source: Hex.tech BigQuery · exchanger2_db_looker · Oct 10, 2025 – Mar 1, 2026")

    pre  = DATA["platform"]["pre_cashback"]
    post = DATA["platform"]["post_cashback"]
    st.header("Platform Growth: Before vs After Cashback")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active B2C Users",  f"{post['active_users']:,}",              f"+{round((post['active_users']/pre['active_users']-1)*100)}%")
    c2.metric("Transactions",      f"{post['transactions']:,}",              f"+{round((post['transactions']/pre['transactions']-1)*100)}%")
    c3.metric("Card Spend",        f"${post['card_spend']/1e6:.2f}M",        f"+{round((post['card_spend']/pre['card_spend']-1)*100)}%")
    c4.metric("Avg Daily Spend",   f"${post['avg_daily_spend']:,}",          f"+{round((post['avg_daily_spend']/pre['avg_daily_spend']-1)*100)}%")
    c5.metric("Avg Daily Txs",     f"{post['avg_daily_tx']:,}",              f"+{round((post['avg_daily_tx']/pre['avg_daily_tx']-1)*100)}%")

    st.header("Monthly P&L")
    pnl = DATA["pnl"]
    pnl_df = pd.DataFrame({
        "Month": pnl["months"] * 2,
        "Amount": pnl["total_revenue"] + [abs(x) for x in pnl["cashback_cost"]],
        "Type": ["Revenue"] * 3 + ["Cashback Cost"] * 3,
    })
    bars = alt.Chart(pnl_df).mark_bar().encode(
        x=alt.X("Month:N", sort=None), y=alt.Y("Amount:Q", title="USD"),
        color=alt.Color("Type:N", scale=alt.Scale(domain=["Revenue","Cashback Cost"], range=["#2196F3","#FF5252"])),
        xOffset="Type:N", tooltip=["Month","Type", alt.Tooltip("Amount:Q", format="$,.0f")],
    ).properties(height=300)
    net_df = pd.DataFrame({"Month": pnl["months"], "Net P&L": pnl["net_pnl"]})
    line = alt.Chart(net_df).mark_line(color="#4CAF50", strokeWidth=2, point=True).encode(
        x=alt.X("Month:N", sort=None), y="Net P&L:Q",
        tooltip=["Month", alt.Tooltip("Net P&L:Q", format="$,.0f")],
    )
    st.altair_chart((bars + line).resolve_scale(y="independent"), use_container_width=True)

    rev_total  = sum(pnl["total_revenue"])
    cost_total = sum(abs(x) for x in pnl["cashback_cost"])
    net_total  = sum(pnl["net_pnl"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("3-Month Revenue", f"${rev_total:,}")
    c2.metric("Cashback Cost",   f"${cost_total:,}")
    c3.metric("Net P&L",         f"${net_total:,}", "2.04× coverage")
    c4.metric("Swap / Card fees", f"${sum(pnl['swap_fees']):,} / ${sum(pnl['card_spend_fee']):,}", "Swap = #1 revenue line")

    st.header("Language Cluster Analysis")
    st.info("🔑 **Russian users spend 1.7× per user vs English** (\\$5,940 vs \\$3,467) — the \\$500 Russian pillar is the highest-ROI allocation.")
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

    st.header("Acquisition Channel Economics")
    ue = DATA["cashback_unit_economics"]
    fc = DATA["seo_forecast"]
    c1, c2, c3 = st.columns(3)
    c1.metric("BTC Cashback CAC",        f"${ue['cac_cashback']}/card",                      f"ROI +{ue['roi_pct']}%")
    c1.caption("\\$142K spent · one-time · expires")
    c2.metric("CPA Influencers CAC",     f"${ue['cac_cpa']}/card",                           "Zero risk · ongoing")
    c3.metric("SEO/Local Media (est.)",  f"${ue['cac_seo_low']}–${ue['cac_seo_high']}/card", f"{fc['conservative']['roi']}–{fc['optimistic']['roi']}× ROI in 90 days")
    c3.caption("\\$2K total · compounds 12+ months")
    st.divider()
    st.subheader("90-Day SEO Forecast")
    st.dataframe(pd.DataFrame([
        {"Scenario": "Conservative", "Revenue": f"${fc['conservative']['revenue']:,}", "Cost": "$2,000", "ROI": f"{fc['conservative']['roi']}×"},
        {"Scenario": "Mid-range",    "Revenue": f"${fc['mid']['revenue']:,}",          "Cost": "$2,000", "ROI": f"{fc['mid']['roi']}×"},
        {"Scenario": "Optimistic",   "Revenue": f"${fc['optimistic']['revenue']:,}",   "Cost": "$2,000", "ROI": f"{fc['optimistic']['roi']}×"},
    ]), use_container_width=True, hide_index=True)
    st.caption("Articles remain indexed 12+ months. Year-one ROI: estimated 4–15×.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 · CONTENT PLAN
# ══════════════════════════════════════════════════════════════════════════════

def page_content_plan():
    st.title("✍️ Stage 3 · Content Plan")
    st.caption("Generated: 2026-03-10 · Based on Stage 1 competitor analysis + Hex live data")

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

    st.header("🚨 Plan Revisions from Hex Live Data")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**Revision 1 — Spanish cluster targets wrong language**\n\nESP-ru = \\$7,302/user vs ESP-en = \\$4,233/user. Add 4th Russian outlet with Spain/relocation angle. Reallocate \\$100 from IDN pillar.")
        st.info("**Revision 2 — Dubai RU outlet = Week 1, not Week 2**\n\nARE-ru = \\$21,640/user. Single highest expected-value placement. Must lock in Week 1.")
    with col2:
        st.info("**Revision 3 — Portugal is Tier 2 only (cleaned data)**\n\nPRT = \\$105K, \\$1,696/user, 47% conversion after removing company accounts and UA friends/family. Brazil (\\$138K, 56% conv.) is the correct Portuguese-language market.")

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
        st.markdown("**Primary market: Brazil (PT-BR)**\n\nBRA = \\$138K, 86 users, \\$1,601/user, 56% conversion — adital.com.br in plan\n\n**PRT status:** \\$105K, 47% conv., cleaned (excludes company accounts + UA friends/family) — **NOT a priority market**\n\n**Angle (PT-BR):** USDT card for Brazil — inflation protection, no BRL exposure\n\n**Keywords:** cartão cripto Brasil, cartão USDT 2026, gastar bitcoin Brasil")
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
    st.caption("Scoring: Notion Media Outlet Selection Guide · 5-dimension 0–15 system · Source of truth for all outlet decisions")
    st.success(
        "✅ **Catalog scraped via browser session** — "
        f"{sum(len(v) for v in RAW_OUTLETS.values())} sites across 7 languages "
        "· Filters: DR ≥ 30, price ≤ $250, categories: Crypto + Business & Finance · Refreshed 2026-03-11"
    )

    # ── Scoring Model (Notion guide) ──────────────────────────────────────────
    with st.expander("📐 Scoring Model (Notion Guide)", expanded=False):
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
""")
        with col2:
            st.markdown("""
**Score thresholds (max 15):**
- **12–15** → ✅ Must buy
- **9–11** → 🟡 Buy if budget allows
- **6–8** → 🟠 Consider only
- **<6** → 🔴 Skip

**Must-Have (auto-disqualify):**
- Search < 35% → **SKIP**
- DR < 40 → **SKIP**
- Price > \\$5/DR → **SKIP**
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
        min_score = st.slider("Min score", min_value=0, max_value=15, value=11, step=1)
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
            if s >= 14: return ["background-color: #c3e6cb"] * len(row)
            if s >= 12: return ["background-color: #d4edda"] * len(row)
            if s >= 11: return ["background-color: #e8f4fd"] * len(row)
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
                "Score":      st.column_config.NumberColumn("Score /15"),
            },
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Outlets shown", len(catalog_rows))
        c2.metric("Avg score", f"{cat_df['Score'].mean():.1f} / 15")
        c3.metric("Avg price", f"${cat_df['Price ($)'].mean():.0f}")
    else:
        st.info("No outlets match current filters — try relaxing DR or price constraints.")

    # ── Top Picks per Pillar ──────────────────────────────────────────────────
    st.header("🏆 Top Picks per Pillar")
    st.caption("Best 5 per language · DR ≥ 40 · Price ≤ $200 · sorted by score then DR")
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
            if float(score) >= 12: return ["background-color: #d4edda"] * len(row)
            if float(score) >= 9:  return ["background-color: #e8f4fd"] * len(row)
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
        st.info("**UTM before ANY purchase**\n```\n?utm_source=collaborator&utm_medium=sponsored\n&utm_campaign=march2026&utm_content={outlet}\n```")
        st.success("**Workflow:** Use filters above → pick top score per pillar → verify on Collaborator → add to March plan")


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

pg = st.navigation({
    "": [
        st.Page(page_dashboard,      title="Dashboard",       icon="🤖", default=True),
    ],
    "Stages": [
        st.Page(page_market_intel,   title="Market Intel",    icon="📊"),
        st.Page(page_kolo_metrics,   title="Kolo Metrics",    icon="📈"),
        st.Page(page_content_plan,   title="Content Plan",    icon="✍️"),
        st.Page(page_outlet_matching,title="Outlet Matching", icon="🗞️"),
    ],
})
pg.run()
