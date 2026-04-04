"""
app.py — Kolo SEO & GEO Intelligence Agent
Single-file Streamlit app using st.navigation().
All data lives in data_sources.py.
GEO = Generative Engine Optimization (AI answer visibility).
"""
from __future__ import annotations

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
from llm_client import generate_press_release, revise_press_release, revise_comment, translate_press_release, recommend_monthly_plan, generate_comment_reply, LANG_NAMES
from geo_visibility import DEFAULT_QUERIES, audit_query, run_full_audit, summarize_audit
from perplexity_geo import (
    query_perplexity, analyze_perplexity_response, audit_prompt as perplexity_audit_prompt,
    run_geo_audit, summarize_geo_audit, DEFAULT_GEO_PROMPTS,
    GEO_MARKETS, generate_geo_prompts, run_geo_market_audit, summarize_by_market,
)
from keyword_research import (
    Keyword, SEED_KEYWORDS, COMPETITOR_DOMAINS,
    build_taxonomy, taxonomy_to_dicts, filter_keywords,
    get_competitor_keywords, expand_keywords_serpapi,
    classify_keyword, detect_language, detect_market, score_keyword,
    generate_keyword_matrix as generate_kw_matrix, discover_keywords_perplexity,
    get_google_autocomplete, expand_with_autocomplete, chain_discover,
)
try:
    from sheets_client import push_comments, push_audit_results, push_publications, load_content_plan, save_content_plan
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    def push_comments(*a, **kw): return 0
    def push_audit_results(*a, **kw): return 0
    def push_publications(*a, **kw): return 0
    def load_content_plan(*a, **kw): return []
    def save_content_plan(*a, **kw): return 0
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
from programmatic_seo import (
    generate_keyword_matrix, score_and_filter_keywords,
    validate_keywords_autocomplete,
    check_serp_competition, batch_competition_check,
    enrich_with_serp_viability,
    generate_page_specs, generate_html_page,
    export_specs_json, export_specs_csv,
    COUNTRIES,
)
from seo_builder import (
    cluster_keywords_to_pages, generate_content_batch,
    build_all_pages, build_manifest, build_sitemap_fragment,
    export_pages_local,
)

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
    # Auto-load from Streamlit secrets, fallback to sidebar input
    _notion_default = ""
    _anthropic_default = ""
    _serpapi_default = ""
    try:
        _notion_default = st.secrets.get("NOTION_TOKEN", "")
    except Exception:
        pass
    try:
        _anthropic_default = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    try:
        _serpapi_default = st.secrets.get("SERPAPI_KEY", "")
    except Exception:
        pass
    notion_token = st.text_input("Notion token", type="password", value=_notion_default, placeholder="secret_...", help="Required for writing to Notion")
    anthropic_token = st.text_input("Anthropic API key", type="password", value=_anthropic_default, placeholder="sk-ant-...", help="console.anthropic.com → API keys")
    serpapi_key = st.text_input("SerpAPI key", type="password", value=_serpapi_default, placeholder="...", help="serpapi.com → free 100 searches/month")
    perplexity_key = st.text_input("Perplexity API key", type="password", placeholder="pplx-...", help="perplexity.ai/settings/api · ~$0.005/query")
    # Auto-load Google Sheets credentials from Streamlit secrets
    import json as _json
    _gsheets_creds = ""
    try:
        _gsheets_creds = _json.dumps(dict(st.secrets["gsheets"]))
    except Exception:
        pass
    for k, v in [("hex_token", hex_token), ("collab_token", collab_token), ("notion_token", notion_token), ("anthropic_token", anthropic_token), ("serpapi_key", serpapi_key), ("perplexity_key", perplexity_key), ("gsheets_json", _gsheets_creds)]:
        if v:
            st.session_state[k] = v
    st.divider()
    st.subheader("📋 Pipeline")
    for name, status in [("Stage 2 · Kolo Metrics", "✅"),
                          ("Stage 3 · Content Plan", "✅"), ("Stage 4 · Outlet Match",  "✅"),
                          ("Stage 5 · Pub ROI",       "✅"),
                          ("Stage 6 · PR Generator",  "🆕"), ("Stage 7 · Distribution", "🆕"),
                          ("Stage 8b · Keyword Intel","🆕"),
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
    filtered = filtered.fillna(0)
    filtered["spend_fmt"] = filtered["card_spend"].apply(lambda x: f"${x/1e3:.0f}K" if x else "$0")
    filtered["spu_fmt"]   = filtered["spend_per_user"].apply(lambda x: f"${int(x):,}" if x else "$0")
    filtered["conv_fmt"]  = filtered["conversion"].apply(lambda x: f"{x*100:.0f}%" if x else "0%")
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

_PLAN_DEFAULT = [
        {"Task": "Crypto card UAE expats — Spend USDT in Dubai",  "Type": "SEO+GEO", "Market": "🇦🇪 ARE", "Outlet Options": "uaehelper.com ($50, DR53, 86% search) · thetradable.com ($100, DR54) · theemiratestimes.com ($99, DR44) · khaleejtimes.com ($200, DR80, premium)", "Price": "$50–200", "GEO": "FAQ + comparison table required", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Lead: How to spend crypto with Visa 2026",      "Type": "SEO+GEO", "Market": "🌍 Global", "Outlet Options": "businessabc.net ($100, DR81) · bignewsnetwork.com ($20, DR75) · tycoonstory.com ($150, DR77) · greenrecord.co.uk ($40, DR73) · technology.org ($190, DR73)", "Price": "$20–190", "GEO": "FAQ + 3 stats + question headers", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Trustee Plus alternative (UA language)",         "Type": "SEO",     "Market": "🌍 CIS/UKR", "Outlet Options": "in-ukraine.biz.ua ($14, DR78, 93% search) · moya-provinciya ($6, DR52) · euroua.com ($30, UA) · track-package ($4, DR54) · finance.com.ua ($10, DR58, Crypto) · kurs.com.ua ($7, DR51)", "Price": "$4–30", "GEO": "Comparison table CRITICAL", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Kolo vs Oobit vs Crypto.com Dubai comparison",  "Type": "GEO",     "Market": "🇦🇪 ARE", "Outlet Options": "theemiratestimes.com ($99, DR44) · khaleejtimes.com ($200, DR80) · thetradable.com ($100, DR54) · businessabc.net ($100, DR81, global EN)", "Price": "$99–200", "GEO": "CRITICAL: comparison table + FAQ + 5 stats", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Best crypto card UK 2026",                      "Type": "SEO+GEO", "Market": "🇬🇧 GBR", "Outlet Options": "businessage.com ($30, DR64) · financial-news.co.uk ($125, DR54) · greenrecord.co.uk ($40, DR73) · newspioneer.co.uk ($65, DR54) · d-themes.com ($30, DR85)", "Price": "$30–125", "GEO": "FAQ + comparison table", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Migliore carta crypto Italia",                  "Type": "SEO",     "Market": "🇮🇹 ITA", "Outlet Options": "kompass.com/IT ($135, DR77, 81% search) · viverepesaro.it ($100, DR40) · ildenaro.it ($190, DR64) · newsanyway.com ($50, DR60) · comunicati-stampa.net ($110, DR58)", "Price": "$50–190", "GEO": "FAQ + question headers", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Kolo vs Crypto.com vs Coinbase comparison",     "Type": "GEO",     "Market": "🌍 Global", "Outlet Options": "businessabc.net ($100, DR81) · newspioneer.co.uk ($65, DR54) · bignewsnetwork.com ($20, DR75) · apsense.com ($45, DR73, Crypto) · kompass.com ($100, DR77)", "Price": "$20–100", "GEO": "CRITICAL: targets 4 AI queries", "Week": "3", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Kartu kripto Indonesia",                        "Type": "SEO",     "Market": "🇮🇩 IDN", "Outlet Options": "pluginongkoskirim.com ($30, DR41, 63% search) · web.id ($60, DR40, 83% search) · goinsan.com ($120, DR56) · investbro.id ($200, DR37, Crypto) · mahasiswaindonesia.id ($30, DR33)", "Price": "$30–200", "GEO": "FAQ recommended", "Week": "3", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Najlepsza karta krypto Polska",                 "Type": "SEO",     "Market": "🇵🇱 POL", "Outlet Options": "netbe.pl ($24, DR48, Crypto) · nenws.com ($72, DR44, Crypto) · bankbiznes.pl ($50, DR72, Finance) · warsawski.eu ($68, DR55, Crypto) · akcyzawarszawa.pl ($85, DR47, Crypto) · biznes.newseria.pl ($100, DR72)", "Price": "$24–100", "GEO": "FAQ recommended", "Week": "4", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Tarjeta cripto España",                         "Type": "SEO",     "Market": "🇪🇸 ESP", "Outlet Options": "crypto-economy.com ($190, DR60, Crypto) · kompass.com/ES ($150, DR77, 67% search) · diariosigloxxi.com ($112, DR72) · technocio.com ($73, DR44, Crypto) · lawandtrends.com ($49, DR61) · nuevarioja.com.ar ($70, DR42, Crypto)", "Price": "$49–190", "GEO": "FAQ recommended", "Week": "4", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Crypto card for business (B2B)",                "Type": "SEO+GEO", "Market": "🌍 B2B",  "Outlet Options": "businessabc.net ($100, DR81) · tycoonstory.com ($150, DR77) · kompass.com ($100, DR77) · technology.org ($190, DR73) · speakrj.com ($100, DR73)", "Price": "$100–190", "GEO": "FAQ + comparison table", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Cel mai bun card crypto România 2026",          "Type": "SEO",     "Market": "🇷🇴 ROU", "Outlet Options": "economica.net ($55, DR58, Crypto) · crypto.ro ($65, DR42, Crypto) · revistabiz.ro ($50, DR50) · curierulnational.ro ($30, DR47) · profit.ro ($90, DR63, Crypto)", "Price": "$30–90", "GEO": "FAQ recommended", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Melhor cartão cripto Brasil",                   "Type": "SEO",     "Market": "🇧🇷 BRA", "Outlet Options": "adital.com.br ($100, DR53, Crypto) · uai.com.br ($58, DR73) · inmais.com.br ($50, DR62, Crypto) · meubanco.digital ($60, DR54, Crypto) · folhadepiedade.com.br ($40, DR55)", "Price": "$40–100", "GEO": "FAQ recommended", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        # ── CIS expansion (UZB, KGZ, ARM, AZE, GEO) — Russian-language, $6,975 LTV/user ──
        {"Task": "Почему Bybit/Nexo/KuCoin не выпускают карты для СНГ — альтернатива", "Type": "GEO",     "Market": "🌍 CIS",    "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · finlist.com.ua ($14, DR60, Crypto) · kompass.com/RU ($8, DR77) · vashe.info ($36, DR72)", "Price": "$8–90",  "GEO": "CRITICAL: captures Bybit/Nexo brand searches from CIS users", "Week": "1",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Лучшая криптокарта для СНГ 2026 — полный обзор",                     "Type": "SEO+GEO", "Market": "🌍 CIS",    "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · finance.com.ua ($10, DR58, Crypto) · kurs.com.ua ($7, DR51, Crypto) · finlist.com.ua ($14, DR60)", "Price": "$7–90",  "GEO": "GEO hub page — AI answer for 'best crypto card CIS'", "Week": "1",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Криптокарта для IT-фрилансеров в Армении без банка",                  "Type": "SEO",     "Market": "🇦🇲 ARM",   "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · novostionline.net ($7, DR63) · vashe.info ($36, DR72) · kompass.com/RU ($8, DR77)", "Price": "$7–90",  "GEO": "FAQ recommended — target relocated Russian IT workers in Yerevan", "Week": "2",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Как потратить USDT картой Visa в Узбекистане 2026",                   "Type": "SEO",     "Market": "🇺🇿 UZB",   "Outlet Options": "finlist.com.ua ($14, DR60, Crypto) · finance.com.ua ($10, DR58) · kurs.com.ua ($7, DR51) · in-ukraine.biz.ua ($14, DR78)", "Price": "$7–14",  "GEO": "High intent — TRC20 USDT dominant in UZB, no Bybit/Nexo card", "Week": "2",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Криптокарта для Кыргызстана — что работает в 2026",                   "Type": "SEO",     "Market": "🇰🇬 KGZ",   "Outlet Options": "moya-provinciya.com.ua ($6, DR52) · track-package.com.ua ($4, DR54) · kurs.com.ua ($7, DR51) · ibra.com.ua ($5, DR39)", "Price": "$4–7",   "GEO": "Comparison table — only Oobit competes in KGZ, Kolo has advantage", "Week": "3",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Crypto card for digital nomads in Georgia (Tbilisi) 2026",             "Type": "SEO+GEO", "Market": "🇬🇪 GEO",   "Outlet Options": "greenrecord.co.uk ($40, DR73, EN) · bignewsnetwork.com ($20, DR75, EN) · businessabc.net ($100, DR81, EN) · axprassion.com ($90, RU Crypto)", "Price": "$20–100", "GEO": "FAQ + EN/RU — high nomad traffic, RU expat community post-2022", "Week": "3",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "USDT TRC20 карта Visa — как тратить в 2026 (СНГ)",                   "Type": "GEO",     "Market": "🌍 CIS",    "Outlet Options": "finlist.com.ua ($14, DR60, Crypto) · axprassion.com ($90, DR64, Crypto) · finance.com.ua ($10, DR58) · kurs.com.ua ($7, DR51)", "Price": "$7–90",  "GEO": "TRC20/USDT dominant in UZB/KGZ — zero competitors targeting this keyword", "Week": "4",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Reddit: answer 'best crypto card' threads",     "Type": "Social",  "Market": "🌍 Global", "Outlet Options": "r/cryptocurrency · r/CryptoCards · r/defi", "Price": "$0", "GEO": "High GEO impact — AI indexes Reddit", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Quora: answer crypto card comparison questions", "Type": "Social",  "Market": "🌍 Global", "Outlet Options": "Quora crypto card topics", "Price": "$0", "GEO": "High GEO impact — AI indexes Quora", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Reddit: answer UAE/Dubai crypto card threads",   "Type": "Social",  "Market": "🇦🇪 ARE", "Outlet Options": "r/dubai · r/cryptocurrency", "Price": "$0", "GEO": "Supports UAE SEO articles", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
        {"Task": "Reddit: r/digitalnomad Georgia/CIS crypto card threads", "Type": "Social", "Market": "🌍 CIS", "Outlet Options": "r/digitalnomad · r/tbilisi · r/ExpatFiance", "Price": "$0", "GEO": "Supports CIS SEO articles + GEO", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    ]


def _load_content_plan():
    """Load content plan from Google Sheets (persistent), fall back to default."""
    creds = _get_sheets_creds()
    if creds:
        try:
            rows = load_content_plan(creds)
            if rows:
                return rows
        except Exception:
            pass
    return list(_PLAN_DEFAULT)


def _save_content_plan(plan):
    """Save content plan to Google Sheets for persistence."""
    creds = _get_sheets_creds()
    if creds:
        try:
            save_content_plan(creds, plan)
        except Exception:
            pass


def _get_sheets_creds():
    """Get Google Sheets credentials from session state or Streamlit secrets."""
    creds = st.session_state.get("gsheets_json", "")
    if creds:
        return creds
    try:
        import json
        return json.dumps(dict(st.secrets["gsheets"]))
    except Exception:
        return ""


def page_content_plan():
    st.title("✍️ Stage 3 · Content Plan")
    st.caption("Unified SEO + GEO + Social plan · Edit in place · Track with links")

    # Load plan
    if "content_plan" not in st.session_state:
        st.session_state["content_plan"] = _load_content_plan()

    plan = st.session_state["content_plan"]
    plan_df = pd.DataFrame(plan)

    # Summary metrics
    total = len(plan_df)
    done = len(plan_df[plan_df["Status"].fillna("") == "Done"]) if "Status" in plan_df.columns else 0
    in_progress = len(plan_df[plan_df["Status"].fillna("") == "In Progress"]) if "Status" in plan_df.columns else 0
    seo_tasks = len(plan_df[plan_df["Type"].str.contains("SEO", na=False)])
    geo_tasks = len(plan_df[plan_df["Type"].str.contains("GEO", na=False)])
    social_tasks = len(plan_df[plan_df["Type"].fillna("") == "Social"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Tasks", total)
    c2.metric("Done", done)
    c3.metric("In Progress", in_progress)
    c4.metric("SEO Articles", seo_tasks)
    c5.metric("Social Posts", social_tasks)

    st.divider()

    # Editable table
    edited_df = st.data_editor(
        plan_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                options=["To Do", "In Progress", "Done", "Skipped"],
                default="To Do",
            ),
            "Type": st.column_config.SelectboxColumn(
                options=["SEO", "GEO", "SEO+GEO", "Social"],
                default="SEO",
            ),
            "Week": st.column_config.SelectboxColumn(
                options=["1", "2", "3", "4", "Apr", "May", "Ongoing"],
                default="1",
            ),
            "Publication URL": st.column_config.LinkColumn("Publication URL"),
            "Reddit/Quora URL": st.column_config.LinkColumn("Reddit/Quora URL"),
        },
        key="plan_editor",
    )

    # Save on any change
    updated_plan = edited_df.to_dict("records")
    st.session_state["content_plan"] = updated_plan
    _save_content_plan(updated_plan)

    # Push to Google Sheets
    st.divider()
    gsheets_creds = _get_sheets_creds()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save to Google Sheets", type="primary", disabled=not gsheets_creds):
            with st.spinner("Saving..."):
                try:
                    n = save_content_plan(gsheets_creds, updated_plan)
                    st.success(f"Saved {n} tasks to [Google Sheet](https://docs.google.com/spreadsheets/d/1EoXaNgpF9Rg4Q-KksFL9d5k5ScDtAF0m7qbg4JxHW4k)")
                except Exception as e:
                    st.error(f"Failed: {e}")
    with col2:
        csv = edited_df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name="content_plan.csv", mime="text/csv")

    # Quick guide
    with st.expander("How to use this plan"):
        st.markdown("""
**Type column:**
- **SEO** = Publish article on paid outlet for backlinks + search traffic
- **GEO** = Comparison/FAQ article optimized for AI engine citations
- **SEO+GEO** = Both — publish on outlet AND optimize for AI
- **Social** = Reddit/Quora comments (free, high GEO impact)

**Workflow:**
1. Set status to **In Progress** when you start
2. Publish article → paste **Publication URL**
3. Post Reddit/Quora comment → paste **Reddit/Quora URL**
4. Set status to **Done**
5. Push to Google Sheets for permanent record

**GEO column** tells you what structure the article needs (FAQ, comparison table, etc.)
""")


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
    caps = {"English": 500, "Russian": 200, "RU/UA": 500, "Italian": 200, "Spanish": 300,
            "Polish": 100, "Portuguese": 200, "Indonesian": 100, "Romanian": 150, "UAE": 350, "CIS": 200}
    pillar_budget["Cap"]       = pillar_budget["Pillar"].map(caps).fillna(200)
    pillar_budget["Remaining"] = pillar_budget["Cap"] - pillar_budget["Spent"]
    pillar_budget["Util %"]    = (pillar_budget["Spent"].fillna(0) / pillar_budget["Cap"].fillna(200).replace(0, 1) * 100).round(0).fillna(0).astype(float).astype(int)
    def color_util(val):
        if val >= 90: return "background-color: #ffd6d6"
        if val >= 60: return "background-color: #fff3cd"
        return "background-color: #d4edda"
    st.dataframe(
        pillar_budget.style.map(color_util, subset=["Util %"]),
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
        st.caption("Format: `kolo.xyz/?utm_source=outletname`")

        # Auto-generate UTM links for all confirmed outlets
        all_outlets = []
        for lang_key, sites in DATA["march_outlets"].items():
            for s in sites:
                if "TBD" not in s["name"]:
                    all_outlets.append({"outlet": s["name"], "lang": lang_key})

        if all_outlets:
            utm_rows = []
            for o in all_outlets:
                # Clean slug: domain-style, lowercase, no spaces
                slug = o["outlet"].strip().lower().replace(" ", "").replace("www.", "")
                link = f"https://kolo.xyz/?utm_source={slug}"
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
            custom_outlet = st.text_input("Outlet name", placeholder="e.g. greenrecord", key="utm_custom_outlet")
            if custom_outlet:
                slug = custom_outlet.strip().lower().replace(" ", "").replace("www.", "")
                link = f"https://kolo.xyz/?utm_source={slug}"
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
            "PL": "pl", "PT": "pt", "ID": "id", "RO": "ro",
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
    {"#": 10, "Title": "Best Crypto Card Dubai 2026: Kolo vs Oobit vs Crypto.com", "Lang": "EN", "Market": "ARE",      "KW": "best crypto card Dubai 2026",           "Words": 1400, "Priority": "High"},
    {"#": 11, "Title": "Crypto Card for Business 2026: Pay with USDT",          "Lang": "EN",    "Market": "Global B2B",  "KW": "crypto card business / USDT card B2B",  "Words": 1400, "Priority": "Medium"},
    {"#": 12, "Title": "Kolo vs Crypto.com vs Coinbase: Card Comparison 2026",  "Lang": "EN",    "Market": "Global",      "KW": "crypto card comparison 2026",           "Words": 1500, "Priority": "High"},
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


_DIST_CACHE = "distribution_cache.json"


def _save_distribution_state():
    """Persist fetched posts + comment queue to local JSON."""
    import json as _j
    state = {
        "fetched_posts": st.session_state.get("fetched_posts", []),
        "comment_queue": st.session_state.get("comment_queue", []),
        "reddit_found": st.session_state.get("reddit_found", []),
    }
    with open(_DIST_CACHE, "w") as f:
        _j.dump(state, f, default=str)


def _load_distribution_state():
    """Load persisted distribution state on startup."""
    import json as _j, os
    if os.path.exists(_DIST_CACHE):
        try:
            with open(_DIST_CACHE) as f:
                state = _j.load(f)
            for key in ["fetched_posts", "comment_queue", "reddit_found"]:
                if key in state and key not in st.session_state:
                    st.session_state[key] = state[key]
        except Exception:
            pass


def page_content_distribution():
    st.title("📣 Stage 9 · Social Listening & Distribution")
    st.caption("Find relevant Reddit & Quora posts → draft helpful comments → track posting")

    # Load persisted data on first render
    _load_distribution_state()

    api_key = st.session_state.get("anthropic_token")

    # Optional article URL to reference
    st.sidebar.divider()
    st.sidebar.subheader("📣 Distribution")
    ref_url = st.sidebar.text_input("Article URL to reference (optional)", placeholder="https://...", key="dist_ref_url")

    tab_search, tab_drafts, tab_tracker = st.tabs(["🔍 Find Posts", "✏️ Draft Comments", "📋 Queue"])

    # ── Tab 0: Find Posts (SerpAPI — Reddit / Quora / Twitter) ──────
    with tab_search:
        import re as _re_s
        import requests as _req_s

        serpapi_key = st.session_state.get("serpapi_key", "")

        if not serpapi_key:
            st.warning("Add your **SerpAPI key** in the sidebar to search.")

        # Platform sub-tabs
        plat_reddit, plat_quora, plat_twitter = st.tabs(["🔴 Reddit", "🔵 Quora", "🐦 Twitter / X"])

        PLATFORM_QUERIES = {
            "Reddit": [
                "site:reddit.com crypto card recommendation",
                "site:reddit.com which crypto card do you use",
                "site:reddit.com best crypto debit card",
                "site:reddit.com USDT card spend",
                "site:reddit.com crypto card digital nomad",
                "site:reddit.com crypto card Europe",
                "site:reddit.com TRC20 USDT card",
                "site:reddit.com crypto card fees comparison",
            ],
            "Quora": [
                "site:quora.com best crypto card",
                "site:quora.com how to spend USDT",
                "site:quora.com crypto debit card review",
                "site:quora.com crypto card Europe",
                "site:quora.com USDT Visa card",
                "site:quora.com crypto card vs bank card",
                "site:quora.com best way to spend cryptocurrency",
                "site:quora.com Telegram crypto wallet",
            ],
            "Twitter": [
                "site:twitter.com OR site:x.com crypto card recommendation",
                "site:twitter.com OR site:x.com best crypto debit card",
                "site:twitter.com OR site:x.com USDT card",
                "site:twitter.com OR site:x.com crypto card review",
                "site:twitter.com OR site:x.com crypto card Europe",
                "site:twitter.com OR site:x.com crypto card fees",
            ],
        }

        def _serpapi_search(platform, custom_q, num_q, state_key):
            """Shared search function for all platforms."""
            queries = []
            site_prefix = {"Reddit": "site:reddit.com", "Quora": "site:quora.com", "Twitter": "site:twitter.com OR site:x.com"}[platform]
            if custom_q:
                queries.append(f"{site_prefix} {custom_q}")
            queries.extend(PLATFORM_QUERIES[platform][:num_q])

            all_posts = []
            seen = set()
            progress = st.progress(0)

            for i, q in enumerate(queries):
                try:
                    resp = _req_s.get("https://serpapi.com/search.json", params={
                        "api_key": serpapi_key, "engine": "google", "q": q, "num": 10,
                        "tbs": "qdr:m6",  # Last 6 months only — excludes archived Reddit posts
                    }, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("organic_results", []):
                            link = item.get("link", "")
                            if link in seen:
                                continue
                            seen.add(link)
                            # Extract community name
                            community = ""
                            if platform == "Reddit":
                                m = _re_s.search(r'reddit\.com/r/(\w+)', link)
                                community = f"r/{m.group(1)}" if m else ""
                                if not m or "/comments/" not in link:
                                    continue
                            elif platform == "Quora":
                                community = "Quora"
                            elif platform == "Twitter":
                                m = _re_s.search(r'(?:twitter|x)\.com/(\w+)/status', link)
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

        def _show_results(state_key, platform, prefix):
            """Shared display function for search results."""
            found = st.session_state.get(state_key, [])
            if found:
                st.success(f"Found {len(found)} {platform} posts")

                # Select All / Send All
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
                        # Also cache post metadata (title, snippet) for Draft Comments
                        post_cache = st.session_state.get("post_metadata_cache", {})
                        found = st.session_state.get(state_key, [])
                        for p in found:
                            if p["url"] in selected_urls:
                                post_cache[p["url"]] = {
                                    "title": p.get("title", ""),
                                    "snippet": p.get("snippet", ""),
                                    "community": p.get("community", ""),
                                    "platform": platform,
                                }
                        st.session_state["post_metadata_cache"] = post_cache
                        st.success(f"Added {len(selected_urls)} URLs! Switch to **Draft Comments** tab.")

        # ── Reddit ────────────────────────────────────────────────
        with plat_reddit:
            st.subheader("Find Reddit Posts")
            col1, col2 = st.columns([3, 1])
            with col1:
                reddit_q = st.text_input("Custom search", placeholder="e.g. spend USDT abroad", key="reddit_q")
            with col2:
                reddit_n = st.number_input("Queries", value=3, min_value=1, max_value=8, key="reddit_n",
                                           help="1 SerpAPI credit per query")
            if st.button("🔍 Search Reddit", type="primary", disabled=not serpapi_key, key="btn_reddit"):
                results = _serpapi_search("Reddit", reddit_q, reddit_n, "reddit_found")
                st.success(f"Found {len(results)} Reddit posts")
                st.rerun()
            _show_results("reddit_found", "Reddit", "rsel")

        # ── Quora ─────────────────────────────────────────────────
        with plat_quora:
            st.subheader("Find Quora Questions")
            col1, col2 = st.columns([3, 1])
            with col1:
                quora_q = st.text_input("Custom search", placeholder="e.g. crypto card for travel", key="quora_q")
            with col2:
                quora_n = st.number_input("Queries", value=3, min_value=1, max_value=8, key="quora_n",
                                          help="1 SerpAPI credit per query")
            if st.button("🔍 Search Quora", type="primary", disabled=not serpapi_key, key="btn_quora"):
                results = _serpapi_search("Quora", quora_q, quora_n, "quora_found")
                st.success(f"Found {len(results)} Quora questions")
                st.rerun()
            _show_results("quora_found", "Quora", "qsel")

        # ── Twitter / X ──────────────────────────────────────────
        with plat_twitter:
            st.subheader("Find Twitter / X Posts")
            col1, col2 = st.columns([3, 1])
            with col1:
                twitter_q = st.text_input("Custom search", placeholder="e.g. crypto card review", key="twitter_q")
            with col2:
                twitter_n = st.number_input("Queries", value=3, min_value=1, max_value=6, key="twitter_n",
                                            help="1 SerpAPI credit per query")
            if st.button("🔍 Search Twitter", type="primary", disabled=not serpapi_key, key="btn_twitter"):
                results = _serpapi_search("Twitter", twitter_q, twitter_n, "twitter_found")
                st.success(f"Found {len(results)} tweets")
                st.rerun()
            _show_results("twitter_found", "Twitter", "tsel")

    # ── Tab 1: Draft Comments ─────────────────────────────────────────
    with tab_drafts:
        import re as _re
        import requests as _requests

        st.subheader("Draft Comments")
        st.markdown("Paste Reddit/Quora URLs → fetch → generate comments → all go to the Queue.")

        # ── Step 1: Paste URLs ────────────────────────────────────
        # Auto-fill from Find Posts tab if user sent URLs
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
            placeholder="https://www.reddit.com/r/cryptocurrency/comments/abc123/which_crypto_card_do_you_use/\nhttps://www.reddit.com/r/digitalnomad/comments/def456/best_card_for_traveling/\nhttps://www.quora.com/What-is-the-best-crypto-debit-card-in-2026",
            key=f"bulk_urls_{url_ver}",
        )

        def _fetch_post(url):
            """Fetch a post's title and body. Supports Reddit, Quora, Twitter."""
            post = {"url": url, "title": "", "body": "", "subreddit": "", "platform": "Reddit", "score": 0, "num_comments": 0}

            # ── Check cached metadata from Find Posts (FIRST — before any early returns) ──
            post_cache = st.session_state.get("post_metadata_cache", {})
            if url in post_cache:
                cached = post_cache[url]
                post["platform"] = cached.get("platform", post["platform"])
                post["title"] = cached.get("title", "") or post["title"]
                post["body"] = cached.get("snippet", "") or ""
                post["subreddit"] = cached.get("community", "") or ""
                if post["title"] and post["body"]:
                    return post

            # ── Quora (title from URL slug if not in cache) ──────────
            if "quora.com" in url:
                post["platform"] = "Quora"
                if not post["title"]:
                    slug = url.split("/")[-1]
                    slug = _re.sub(r'^https?-www-quora-com-', '', slug)
                    slug = _re.sub(r'-\d+$', '', slug)
                    slug = _re.sub(r'-answer-[\w-]+$', '', slug)
                    post["title"] = slug.replace("-", " ").strip() or "Quora question"
                return post

            # ── Twitter / X ───────────────────────────────────────
            if "twitter.com" in url or "x.com" in url:
                post["platform"] = "Twitter"
                m = _re.search(r'(?:twitter|x)\.com/(\w+)/status', url)
                post["subreddit"] = f"@{m.group(1)}" if m else ""
                post["title"] = f"Tweet by {post['subreddit']}" if post["subreddit"] else "Tweet"
                # Try to get tweet content via SerpAPI
                serpapi_key = st.session_state.get("serpapi_key", "")
                if serpapi_key and not post.get("body"):
                    try:
                        resp = _requests.get("https://serpapi.com/search.json", params={
                            "api_key": serpapi_key, "engine": "google",
                            "q": f"{url}", "num": 1,
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

            # ── HackerNews ────────────────────────────────────────
            if "news.ycombinator" in url:
                post["platform"] = "HackerNews"
                post["title"] = "HN discussion"
                return post

            # ── Reddit (fetch via JSON API) ───────────────────────
            reddit_match = _re.search(r'reddit\.com/r/(\w+)', url)
            if reddit_match:
                post["subreddit"] = reddit_match.group(1)
                try:
                    json_url = url.rstrip("/") + ".json"
                    resp = _requests.get(json_url, headers={"User-Agent": "KoloSEOAgent/1.0"}, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and data:
                            rd = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
                            post["title"] = rd.get("title", "")
                            post["body"] = (rd.get("selftext", "") or "")[:500]
                            post["score"] = rd.get("score", 0)
                            post["num_comments"] = rd.get("num_comments", 0)
                            # Check if archived (can't comment on archived posts)
                            if rd.get("archived", False) or rd.get("locked", False):
                                post["archived"] = True
                            else:
                                post["archived"] = False
                except Exception:
                    pass

            # Fallback title from URL slug
            if not post["title"]:
                slug_match = _re.search(r'/comments/\w+/([^/]+)', url)
                if slug_match:
                    post["title"] = slug_match.group(1).replace("_", " ")
                else:
                    post["title"] = url.split("/")[-1].replace("_", " ").replace("-", " ")
            return post

        # Fetch + show posts
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
            if st.button("🤖 Generate All Comments", type="primary",
                         disabled=not api_key or not fetched):
                queue = st.session_state.get("comment_queue", [])
                progress = st.progress(0)
                status = st.empty()
                for i, post in enumerate(fetched):
                    # Skip archived/locked Reddit posts
                    if post.get("archived"):
                        progress.progress((i + 1) / len(fetched))
                        continue
                    # Skip if already in queue
                    if any(q["url"] == post["url"] for q in queue):
                        progress.progress((i + 1) / len(fetched))
                        continue
                    status.text(f"Generating comment for: {post['title'][:50]}...")
                    try:
                        comment = generate_comment_reply(
                            api_key,
                            post_title=post["title"],
                            post_body=post.get("body", ""),
                            platform=post["platform"],
                            subreddit=post.get("subreddit", ""),
                            article_url=ref_url,
                        )
                        queue.append({
                            "url": post["url"],
                            "title": post["title"],
                            "platform": post["platform"],
                            "subreddit": post.get("subreddit", ""),
                            "comment": comment,
                            "status": "draft",
                        })
                    except Exception as e:
                        queue.append({
                            "url": post["url"],
                            "title": post["title"],
                            "platform": post["platform"],
                            "subreddit": post.get("subreddit", ""),
                            "comment": f"[Error: {e}]",
                            "status": "error",
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
            active_count = len(fetched) - archived_count
            if archived_count:
                st.warning(f"⚠️ {archived_count} posts are archived/locked and will be skipped.")
            for i, post in enumerate(fetched):
                sub = f"r/{post['subreddit']}" if post["subreddit"] else post["platform"]
                score = f" · ⬆️ {post['score']} · 💬 {post['num_comments']}" if post.get("score") else ""
                archived = " · 🔒 **ARCHIVED**" if post.get("archived") else ""
                st.markdown(f"{i+1}. {'~~' if post.get('archived') else ''}**{post['title'][:80]}**{'~~' if post.get('archived') else ''} — {sub}{score}{archived}")

            # Show queue status
            queue = st.session_state.get("comment_queue", [])
            if queue:
                st.success(f"💬 {len(queue)} comments generated! Switch to the **Queue** tab to review and post.")

    # ── Tab 3: Queue ─────────────────────────────────────────────────
    with tab_tracker:
        st.subheader("Comment Queue")
        st.markdown("All generated comments in one place. Edit, revise, then copy & post.")

        queue = st.session_state.get("comment_queue", [])

        # Clear queue button
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
            # Summary
            total = len(queue)
            posted = sum(1 for q in queue if q["status"] == "posted")
            drafts_count = sum(1 for q in queue if q["status"] == "draft")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", total)
            c2.metric("Drafts", drafts_count)
            c3.metric("Posted", posted)

            # Revise All button
            with c4:
                revise_all_text = st.text_input("Revise all drafts:", placeholder="e.g. make shorter", key="revise_all_input", label_visibility="collapsed")
            if st.button("✏️ Revise All Drafts", type="primary", disabled=not api_key or not revise_all_text):
                drafts_to_revise = [i for i, q in enumerate(queue) if q["status"] == "draft"]
                if drafts_to_revise:
                    progress = st.progress(0)
                    for j, idx in enumerate(drafts_to_revise):
                        item = queue[idx]
                        try:
                            revised = revise_comment(
                                api_key,
                                current_comment=item["comment"],
                                instructions=revise_all_text,
                            )
                            queue[idx]["comment"] = revised
                            # Bump version for text area
                            ver = st.session_state.get(f"q_ver_{idx}", 0)
                            st.session_state[f"q_ver_{idx}"] = ver + 1
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
                    # Header
                    sub = f"r/{item['subreddit']}" if item["subreddit"] else item["platform"]
                    status_icon = {"draft": "📝", "posted": "✅", "error": "❌"}.get(item["status"], "📝")
                    st.markdown(f"{status_icon} **[{item['title'][:70]}]({item['url']})** — {sub}")

                    # Editable comment
                    ver = st.session_state.get(f"q_ver_{i}", 0)
                    edited = st.text_area(
                        "Comment", value=item["comment"], height=120,
                        key=f"q_comment_{i}_{ver}", label_visibility="collapsed",
                    )
                    queue[i]["comment"] = edited

                    # Revision input BEFORE buttons so value is available on click
                    rev_text = st.text_input("What to change?", placeholder="shorter, less promotional, add fee comparison",
                                             key=f"q_rev_{i}", label_visibility="collapsed")

                    # Action buttons
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                    with col1:
                        st.markdown(f"[Open post ↗]({item['url']})")
                    with col2:
                        if st.button("✏️ Revise", key=f"q_rev_btn_{i}", disabled=not api_key or not rev_text):
                            try:
                                revised = revise_comment(
                                    api_key,
                                    current_comment=edited,
                                    instructions=rev_text,
                                )
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
                        st.download_button("📋 Copy", data=edited, file_name=f"comment_{i}.txt",
                                           mime="text/plain", key=f"q_dl_{i}")

            st.session_state["comment_queue"] = queue
            _save_distribution_state()

            st.divider()

            # Export to CSV (Google Sheets compatible)
            export_rows = []
            for item in queue:
                export_rows.append({
                    "Post URL": item["url"],
                    "Post Title": item["title"],
                    "Platform": item["platform"],
                    "Subreddit": item.get("subreddit", ""),
                    "Comment": item["comment"],
                    "Status": item["status"],
                    "Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                })
            export_df = pd.DataFrame(export_rows)
            csv_data = export_df.to_csv(index=False)

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    "📥 Export All to CSV",
                    data=csv_data,
                    file_name=f"reddit_comments_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="export_queue_csv",
                )
            with col_exp2:
                # Export only drafts (not yet posted)
                draft_rows = [r for r in export_rows if r["Status"] == "draft"]
                if draft_rows:
                    draft_csv = pd.DataFrame(draft_rows).to_csv(index=False)
                    st.download_button(
                        f"📥 Export {len(draft_rows)} Drafts Only",
                        data=draft_csv,
                        file_name=f"reddit_drafts_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="export_drafts_csv",
                    )

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
            st.caption(
                "**GEO Impact:** Reddit & Quora comments are indexed by "
                "ChatGPT, Perplexity, and Google AI Overviews."
            )


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




# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ── Page 11: Programmatic SEO ─────────────────────────────────────────────────

def page_programmatic_seo():
    st.title("🚀 Programmatic SEO — Long-Tail Keyword Factory")
    st.caption("Generate → Validate (free) → Score competition → Auto-build pages")

    serp_key = st.session_state.get("serpapi_key")

    # ── Tab layout ──
    tab_matrix, tab_validate, tab_compete, tab_build = st.tabs([
        "1️⃣ Keyword Matrix", "2️⃣ Autocomplete Validation", "3️⃣ Competition Check", "4️⃣ Build Pages"
    ])

    # ──────────────────────────────────────────────────────────────────────
    # TAB 1: Generate Keyword Matrix
    # ──────────────────────────────────────────────────────────────────────
    with tab_matrix:
        st.subheader("Keyword Matrix Generator")
        st.info("Combines countries × cryptos × use cases × modifiers. **Zero API cost.**")

        col1, col2, col3 = st.columns(3)
        with col1:
            tiers = st.multiselect("Country tiers", [1, 2, 3], default=[1, 2],
                                   help="Tier 1 = top revenue, Tier 2 = growth, Tier 3 = emerging")
        with col2:
            include_ru = st.checkbox("Include Russian keywords", value=True,
                                     help="RU speakers = 2x LTV ($6,975 vs $3,502)")
        with col3:
            max_kw = st.number_input("Max keywords", 100, 5000, 2000, step=100)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            min_score = st.slider("Min keyword score", 0.3, 0.75, 0.45, 0.05,
                                  help="Pre-SERP max is 0.75. Recommended: 0.45+")
        with col_s2:
            min_pattern_avg = st.slider("Min pattern avg score", 0.3, 0.75, 0.5, 0.05,
                                        help="Entire template dropped if avg below this")

        if st.button("🔧 Generate → Score → Dedup → Filter", type="primary"):
            with st.spinner("Generating keyword combinations..."):
                raw_matrix = generate_keyword_matrix(tiers=tiers, include_ru=include_ru, max_combos=max_kw)
            with st.spinner(f"Scoring → deduplicating → evaluating patterns ({len(raw_matrix):,} keywords)..."):
                result = score_and_filter_keywords(raw_matrix, min_score=min_score,
                                                   min_pattern_avg=min_pattern_avg)
                st.session_state["pseo_matrix"] = result["kept"]
                st.session_state["pseo_score_result"] = result

        if "pseo_score_result" in st.session_state:
            result = st.session_state["pseo_score_result"]
            stats = result["stats"]
            kept = result["kept"]
            rejected = result["rejected"]

            st.success(f"**{stats['kept']}** keywords kept · **{stats['rejected']}** rejected ({stats['rejection_rate']}% filtered out)")

            # Pipeline funnel
            import pandas as _pd
            st.subheader("Pipeline Funnel")
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Raw Generated", stats["total_raw"])
            col_b.metric("After Scoring", stats["after_scoring"])
            col_c.metric("After Dedup", stats["after_dedup"],
                         delta=f"-{result['dedup_stats']['duplicates_removed']} dupes")
            col_d.metric("After Pattern Eval", stats["after_pattern_eval"])

            # Stats row
            col_e, col_f, col_g = st.columns(3)
            col_e.metric("Avg Score (pre-SERP)", stats["avg_score"])
            col_f.metric("Filter Rate", f"{stats['rejection_rate']}%")
            col_g.metric("Intent Clusters", result["dedup_stats"]["clusters"])

            # Score distribution
            st.subheader("Score Distribution (pre-SERP, max 0.75)")
            dist = stats["score_distribution"]
            dist_df = _pd.DataFrame([{"range": k, "count": v} for k, v in dist.items()])
            st.bar_chart(dist_df.set_index("range"))

            # Pattern evaluation
            st.subheader("Pattern Evaluation")
            pat_eval = result.get("pattern_eval", {})
            pat_rows = []
            for p, ps in sorted(pat_eval.items(), key=lambda x: -x[1]["avg_score"]):
                status = "✅" if ps["avg_score"] >= min_pattern_avg else "❌ dropped"
                pat_rows.append({
                    "Pattern": p, "Keywords": ps["count"],
                    "Avg Score": ps["avg_score"], "Top": ps["top_score"],
                    "Bottom": ps["bottom_score"], "Status": status
                })
            st.dataframe(_pd.DataFrame(pat_rows), hide_index=True)

            # By pattern (kept only)
            st.subheader("Kept Keywords by Pattern")
            pattern_counts = stats["by_pattern_count"]
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                with st.expander(f"**{pattern}** — {count} keywords"):
                    pat_kws = result["by_pattern"][pattern]
                    pat_df = _pd.DataFrame(pat_kws)
                    display_cols = [c for c in ["keyword", "lang", "country", "quality_score",
                                                "intent_score", "natural_score", "scale_score",
                                                "market_score", "cluster_size", "alternates"]
                                   if c in pat_df.columns]
                    st.dataframe(pat_df[display_cols].head(40), height=300)

            # Rejected samples
            with st.expander(f"Rejected keywords ({len(rejected)} total)", expanded=False):
                rej_df = _pd.DataFrame(rejected)
                display_cols = [c for c in ["keyword", "quality_score", "reject_reason",
                                            "intent_score", "natural_score"]
                                if c in rej_df.columns]
                st.dataframe(rej_df[display_cols].head(40), height=200)

    # ──────────────────────────────────────────────────────────────────────
    # TAB 2: Autocomplete Validation (FREE)
    # ──────────────────────────────────────────────────────────────────────
    with tab_validate:
        st.subheader("Google Autocomplete Validation")
        st.info("Checks if Google suggests these keywords → real demand exists. **100% free, no API key needed.**")

        if "pseo_matrix" not in st.session_state:
            st.warning("Generate & score a keyword matrix first (Tab 1)")
        else:
            matrix = st.session_state["pseo_matrix"]
            st.write(f"**{len(matrix):,}** quality-scored keywords ready for validation")

            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.number_input("Batch size", 10, 500, 100, step=10,
                                             help="Keywords to check per run. ~150ms each = 100 takes ~15 sec.")
            with col2:
                start_from = st.number_input("Start from index", 0, len(matrix) - 1, 0, step=10)

            if st.button("✅ Validate via Autocomplete", type="primary"):
                batch = matrix[start_from:start_from + batch_size]
                progress = st.progress(0, text="Checking Google Autocomplete...")
                status = st.empty()

                def _update(i, total):
                    progress.progress(i / total, text=f"Checking {i}/{total}...")
                    if i % 10 == 0:
                        status.caption(f"Current: {batch[min(i, len(batch)-1)]['keyword']}")

                validated = validate_keywords_autocomplete(batch, delay=0.15, progress_callback=_update)
                progress.progress(1.0, text="Done!")

                # Merge with existing results
                existing = st.session_state.get("pseo_validated", [])
                existing.extend(validated)
                st.session_state["pseo_validated"] = existing

        if "pseo_validated" in st.session_state:
            validated = st.session_state["pseo_validated"]
            import pandas as _pd
            vdf = _pd.DataFrame(validated)

            # Stats
            strong = vdf[vdf["demand_signal"] == "strong"]
            medium = vdf[vdf["demand_signal"] == "medium"]
            weak = vdf[vdf["demand_signal"] == "weak"]
            none_ = vdf[vdf["demand_signal"] == "none"]

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("🟢 Strong", len(strong))
            col_b.metric("🟡 Medium", len(medium))
            col_c.metric("🟠 Weak", len(weak))
            col_d.metric("🔴 No Signal", len(none_))

            # Show strong + medium (the ones worth checking competition)
            winners = vdf[vdf["demand_signal"].isin(["strong", "medium"])].sort_values("autocomplete_hits", ascending=False)
            st.write(f"**{len(winners)}** keywords with demand signal → ready for competition check")

            with st.expander(f"Keywords with demand ({len(winners)})", expanded=True):
                display_cols = ["keyword", "lang", "country", "demand_signal", "autocomplete_hits"]
                extra = [c for c in ["autocomplete_suggestions"] if c in winners.columns]
                st.dataframe(winners[display_cols + extra].head(100), height=400)

            # Export
            if st.button("💾 Export validated keywords (JSON)"):
                import json as _json
                outpath = "/Users/ek/SEO agent/validated_keywords.json"
                with open(outpath, "w") as f:
                    _json.dump([r for r in validated if r.get("demand_signal") in ("strong", "medium")],
                               f, indent=2, ensure_ascii=False)
                st.success(f"Exported to `{outpath}`")

    # ──────────────────────────────────────────────────────────────────────
    # TAB 3: Competition Check (SerpAPI)
    # ──────────────────────────────────────────────────────────────────────
    with tab_compete:
        st.subheader("SERP Viability & Competition Scoring")
        st.info("Checks top 10 results, scores SERP viability (0-0.25), recalculates final score. **1 SerpAPI credit per keyword.**")

        if not serp_key:
            st.warning("Enter your SerpAPI key in the sidebar")
        elif "pseo_validated" not in st.session_state:
            st.warning("Validate keywords first (Tab 2)")
        else:
            validated = st.session_state["pseo_validated"]
            winners = [kw for kw in validated if kw.get("demand_signal") in ("strong", "medium")]
            st.write(f"**{len(winners)}** validated keywords available")

            col1, col2 = st.columns(2)
            with col1:
                max_checks = st.number_input("Max SerpAPI checks", 5, 50, 20, step=5,
                                             help="Each check costs 1 SerpAPI credit (100 free/month)")
            with col2:
                st.caption(f"Budget: {max_checks} credits · Score = pre-SERP (0.75) + SERP viability (0.25)")

            if st.button("🔍 Check Competition + Score SERP Viability", type="primary"):
                progress = st.progress(0, text="Checking SERPs & scoring viability...")

                def _update(i, total):
                    progress.progress(i / total, text=f"SERP check {i}/{total}...")

                scored = enrich_with_serp_viability(
                    winners, serp_key, max_checks=max_checks,
                    delay=2.0, progress_callback=_update
                )
                progress.progress(1.0, text="Done!")
                st.session_state["pseo_scored"] = scored

        if "pseo_scored" in st.session_state:
            scored = st.session_state["pseo_scored"]
            import pandas as _pd
            sdf = _pd.DataFrame(scored)

            if "competition_score" in sdf.columns:
                high_opp = sdf[sdf["opportunity"] == "high"] if "opportunity" in sdf.columns else _pd.DataFrame()
                med_opp = sdf[sdf["opportunity"] == "medium"] if "opportunity" in sdf.columns else _pd.DataFrame()

                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("🎯 High Opportunity", len(high_opp))
                col_b.metric("🟡 Medium", len(med_opp))
                col_c.metric("Kolo Already Ranks", len(sdf[sdf["kolo_present"] == True]) if "kolo_present" in sdf.columns else 0)
                if "serp_score" in sdf.columns:
                    col_d.metric("Avg SERP Viability", f"{sdf['serp_score'].mean():.2f}/0.25")

                display_cols = [c for c in ["keyword", "lang", "country", "quality_score",
                                            "serp_score", "competition_score", "opportunity",
                                            "big_players", "weak_results", "forums_ugc",
                                            "kolo_present", "top_3_domains"]
                                if c in sdf.columns]
                st.dataframe(sdf[display_cols].sort_values("quality_score", ascending=False), height=400)

    # ──────────────────────────────────────────────────────────────────────
    # TAB 4: Build Pages
    # ──────────────────────────────────────────────────────────────────────
    with tab_build:
        st.subheader("Build & Export Pages")
        st.info("Clusters keywords → generates content via Claude → exports ready-to-deploy package with Designer brief.")

        api_key = st.session_state.get("anthropic_token")

        # Source keywords
        source = st.session_state.get("pseo_scored") or st.session_state.get("pseo_matrix")
        if not source:
            st.warning("Run Tab 1 (Keyword Matrix) first")
        else:
            st.write(f"**{len(source)}** keywords available")

            # Step 1: Cluster
            st.markdown("### Step 1 — Cluster into Pages")
            if st.button("📦 Cluster Keywords → Pages", type="primary"):
                clusters = cluster_keywords_to_pages(source)
                st.session_state["pseo_clusters"] = clusters

            if "pseo_clusters" in st.session_state:
                clusters = st.session_state["pseo_clusters"]
                st.success(f"**{len(clusters)}** pages (1 per country+language)")

                import pandas as _pd
                cluster_rows = []
                for c in clusters:
                    cluster_rows.append({
                        "slug": c.slug,
                        "primary_keyword": c.primary_keyword,
                        "secondary": len(c.secondary_keywords),
                        "lang": c.lang,
                        "country": c.country_name,
                        "template": c.template,
                        "score": c.avg_score,
                    })
                st.dataframe(_pd.DataFrame(cluster_rows), height=350, hide_index=True)

                # Step 2: Generate content
                st.markdown("### Step 2 — Generate Content (Claude API)")
                if not api_key:
                    st.warning("Enter Anthropic API key in sidebar")
                else:
                    model = st.selectbox("Model", ["claude-3-5-haiku-20241022", "claude-sonnet-4-20250514"], index=0,
                                         help="Haiku ≈ $0.002/page, Sonnet ≈ $0.01/page")
                    est_cost = len(clusters) * (0.002 if "haiku" in model else 0.01)
                    st.caption(f"Estimated cost: ~${est_cost:.2f} for {len(clusters)} pages")

                    if st.button("✍️ Generate All Content", type="primary"):
                        progress = st.progress(0, text="Generating content...")
                        def _update(i, total):
                            progress.progress(i / total, text=f"Page {i}/{total}: {clusters[i-1].slug}")

                        clusters = generate_content_batch(clusters, api_key, model=model,
                                                          delay=1.0, progress_callback=_update)
                        progress.progress(1.0, text="Done!")
                        st.session_state["pseo_clusters"] = clusters
                        st.session_state["pseo_content_generated"] = True

                # Step 3: Assemble & Export
                if st.session_state.get("pseo_content_generated"):
                    st.markdown("### Step 3 — Assemble & Export")

                    if st.button("🏗️ Build HTML Pages + Export Package", type="primary"):
                        clusters = st.session_state["pseo_clusters"]
                        clusters = build_all_pages(clusters)
                        st.session_state["pseo_clusters"] = clusters

                        # Export locally
                        import os
                        base_dir = os.path.join(os.path.dirname(__file__) or ".", "pages")
                        count = export_pages_local(clusters, base_dir)

                        # Generate Designer brief
                        _generate_designer_brief(clusters, base_dir)

                        st.success(f"**{count}** pages exported to `pages/`")
                        st.balloons()

                    if st.session_state.get("pseo_clusters") and st.session_state["pseo_clusters"][0].full_html:
                        clusters = st.session_state["pseo_clusters"]

                        # Preview
                        st.markdown("### Preview")
                        preview_idx = st.selectbox("Select page",
                                                   range(len(clusters)),
                                                   format_func=lambda i: f"{clusters[i].slug} — {clusters[i].h1}")
                        sel = clusters[preview_idx]
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown(f"**Slug:** `/crypto-card/{sel.slug}`")
                            st.markdown(f"**Title:** {sel.title}")
                            st.markdown(f"**Primary:** {sel.primary_keyword}")
                            st.markdown(f"**Secondary:** {', '.join(sel.secondary_keywords[:5])}")
                        with col2:
                            st.markdown(f"**Lang:** {sel.lang}")
                            st.markdown(f"**Country:** {sel.country_name}")
                            st.markdown(f"**Template:** {sel.template}")
                            st.markdown(f"**Score:** {sel.avg_score:.3f}")

                        with st.expander("HTML Source", expanded=False):
                            st.code(sel.full_html[:5000], language="html")
                        st.components.v1.html(sel.full_html, height=700, scrolling=True)


def _generate_designer_brief(clusters, base_dir):
    """Generate a plug-and-play brief for the Webflow Designer."""
    import os, json

    manifest = build_manifest(clusters)
    sitemap_frag = build_sitemap_fragment(clusters)

    brief = """# Webflow Designer Brief — Programmatic SEO Pages
## Plug & Play Setup Guide

### What This Is
{count} pre-built SEO pages for kolo.xyz/crypto-card/{{slug}}.
All content, titles, meta descriptions, and HTML are pre-generated.
You just need to create the CMS structure and paste the content.

---

### Step 1: Create CMS Collection (5 min)

1. Open Webflow Designer → **CMS** → **+ New Collection**
2. Name: **Crypto Card Pages**
3. Slug prefix: **crypto-card**
4. Add these fields:

| Field Name | Type | Notes |
|-----------|------|-------|
| Name | Plain Text | Page title (auto-created) |
| Slug | Auto-generated | Will be /crypto-card/{{slug}} |
| SEO Title | Plain Text | Copy from spreadsheet "title" column |
| SEO Description | Plain Text | Copy from spreadsheet "meta_description" column |
| H1 | Plain Text | Main heading |
| Hero Subtitle | Plain Text | Subheading under H1 |
| Body Content | Rich Text | Paste the HTML content |
| Language | Option (en/ru) | Page language |
| Country | Plain Text | Country name |
| Primary Keyword | Plain Text | For reference |
| Related Pages | Multi-reference | Link to related Crypto Card Pages |

### Step 2: Design the Template Page (15 min)

1. Go to **CMS Collection Pages** → **Crypto Card Pages Template**
2. Build layout:
   - **Nav bar** — use existing site nav component
   - **Hero section** — dark background, bind H1 + Hero Subtitle fields
   - **Body section** — bind Body Content (Rich Text) field
   - **CTA section** — "Get Your Kolo Card" button → link to kolo.xyz
   - **Related pages** — Dynamic list from Related Pages field
   - **Footer** — use existing site footer component
3. **SEO Settings** on the template page:
   - Title → bind to SEO Title field
   - Description → bind to SEO Description field
   - Open Graph → same bindings
4. Publish the template

### Step 3: Import Content (10 min)

**Option A — Manual (small batches):**
1. Open `pages/manifest.json` for the page list
2. For each page, open `pages/{{slug}}/index.html`
3. Copy the content between `<main>` tags
4. Paste into the Body Content rich text field in Webflow CMS
5. Fill in SEO Title, SEO Description, H1, Hero Subtitle from the manifest

**Option B — CSV Import (fastest):**
1. Open `pages/cms_import.csv` in the pages folder
2. Go to Webflow CMS → Crypto Card Pages → **Import** → upload CSV
3. Map columns to CMS fields
4. All {count} pages imported at once

**Option C — Webflow API (automated):**
If you have API access, run the deploy script from the SEO agent app.

### Step 4: Publish
1. Review a few pages in the Webflow Editor
2. **Publish** all changes
3. Check: kolo.xyz/crypto-card/uae should load

---

### Files Included

```
pages/
├── manifest.json          ← master list of all pages
├── cms_import.csv         ← ready for Webflow CSV import
├── sitemap_fragment.xml   ← add to sitemap if needed
├── uae/index.html         ← full HTML for UAE page
├── uk/index.html
├── italy/index.html
├── ru/uae/index.html
└── ...
```

### Page Summary

{page_table}

---
Generated by Kolo SEO Agent · {date}
""".format(
        count=len(clusters),
        page_table="\n".join(
            f"| `/crypto-card/{c.slug}` | {c.lang} | {c.country_name} | {c.primary_keyword} | +{len(c.secondary_keywords)} keywords |"
            for c in clusters
        ),
        date=__import__("datetime").date.today().isoformat(),
    )

    # Write brief
    brief_path = os.path.join(base_dir, "DESIGNER_BRIEF.md")
    with open(brief_path, "w") as f:
        f.write(brief)

    # Write CMS import CSV
    import csv
    csv_path = os.path.join(base_dir, "cms_import.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Slug", "SEO Title", "SEO Description", "H1",
                     "Hero Subtitle", "Language", "Country", "Primary Keyword"])
        for c in clusters:
            w.writerow([
                c.h1, c.slug, c.title, c.meta_description,
                c.h1, c.hero_subtitle, c.lang, c.country_name, c.primary_keyword,
            ])

    # Write manifest
    manifest_path = os.path.join(base_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Write sitemap fragment
    sitemap_path = os.path.join(base_dir, "sitemap_fragment.xml")
    with open(sitemap_path, "w") as f:
        f.write(sitemap_frag)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 12 · KEYWORD INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

def page_keyword_intel():
    st.title("🧠 Keyword & AI Prompt Intelligence")
    st.caption("Competitive keyword research + Perplexity AI citation tracking")

    serp_key = st.session_state.get("serpapi_key")
    pplx_key = st.session_state.get("perplexity_key")
    ahrefs_key = st.session_state.get("ahrefs_key")

    tab_taxonomy, tab_discover, tab_geo_audit, tab_ai_audit, tab_expand = st.tabs([
        "📊 Taxonomy", "🔬 Discovery", "🌍 Geo Market Audit", "🤖 AI Prompt Audit", "🌱 Expansion"
    ])

    # ── TAB 1: Keyword Taxonomy ──────────────────────────────────────────
    with tab_taxonomy:
        st.subheader("Ranked Keyword Taxonomy")
        st.info("60+ seed keywords across 8 languages, 15+ markets. Scored by volume, difficulty, AI opportunity, and market LTV.")

        col1, col2, col3 = st.columns(3)
        with col1:
            lang_filter = st.selectbox("Language", ["all", "en", "ru", "it", "es", "pl", "pt", "id", "ro"])
        with col2:
            market_filter = st.selectbox("Market", ["all", "global", "EU", "GBR", "ARE", "ITA", "ESP", "POL", "IDN", "UZB", "KGZ", "ARM", "GEO"])
        with col3:
            cat_filter = st.selectbox("Category", ["all", "head", "mid_tail", "long_tail", "comparison", "problem", "b2b", "branded"])

        if st.button("🔧 Build Taxonomy", type="primary"):
            with st.spinner("Building keyword taxonomy..."):
                taxonomy = build_taxonomy(ahrefs_key=ahrefs_key)
                st.session_state["kw_taxonomy"] = taxonomy

        if "kw_taxonomy" in st.session_state:
            taxonomy = st.session_state["kw_taxonomy"]

            # Apply filters
            filtered = taxonomy
            if lang_filter != "all":
                filtered = [k for k in filtered if k.language == lang_filter]
            if market_filter != "all":
                filtered = [k for k in filtered if k.market == market_filter]
            if cat_filter != "all":
                filtered = [k for k in filtered if k.category == cat_filter]

            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Total Keywords", len(taxonomy))
            col_b.metric("Filtered", len(filtered))
            col_c.metric("Languages", len(set(k.language for k in taxonomy)))
            col_d.metric("Markets", len(set(k.market for k in taxonomy)))

            # Category breakdown
            st.subheader("By Category")
            cat_counts = {}
            for k in filtered:
                cat_counts[k.category] = cat_counts.get(k.category, 0) + 1
            cat_df = pd.DataFrame([{"category": c, "count": n} for c, n in sorted(cat_counts.items(), key=lambda x: -x[1])])
            if not cat_df.empty:
                st.bar_chart(cat_df.set_index("category"))

            # Language breakdown
            st.subheader("By Language")
            lang_counts = {}
            for k in filtered:
                lang_counts[k.language] = lang_counts.get(k.language, 0) + 1
            lang_df = pd.DataFrame([{"language": l, "count": n} for l, n in sorted(lang_counts.items(), key=lambda x: -x[1])])
            if not lang_df.empty:
                st.bar_chart(lang_df.set_index("language"))

            # Full table
            st.subheader(f"Keywords ({len(filtered)})")
            kw_dicts = taxonomy_to_dicts(filtered)
            df = pd.DataFrame(kw_dicts)
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)

            # Export
            csv = df.to_csv(index=False)
            st.download_button("📥 Download taxonomy CSV", data=csv,
                               file_name=f"keyword_taxonomy_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv")

    # ── TAB 2: Discovery ───────────────────────────────────────────────────
    with tab_discover:
        st.subheader("Keyword Discovery Engine")
        st.markdown("""
Three discovery methods — from free to cheap:
1. **Keyword Matrix** — product × market × language × intent (free, instant)
2. **Google Autocomplete** — real search suggestions + alphabet expansion (free)
3. **Perplexity AI** — ask AI what people search for in each market (~$0.005/market)
""")

        disc_tab1, disc_tab2, disc_tab3 = st.tabs(["🧮 Matrix Generator", "🔤 Autocomplete", "🤖 AI Discovery"])

        with disc_tab1:
            st.markdown("**Generates:** `[product] × [market] × [language] × [intent modifier]`")
            col1, col2, col3 = st.columns(3)
            with col1:
                incl_en = st.checkbox("English keywords", value=True)
                incl_ru = st.checkbox("Russian keywords", value=True, help="RU = 2x LTV")
            with col2:
                incl_b2b = st.checkbox("B2B keywords", value=True, help="B2B = 41% of spend")
                max_per = st.slider("Max per market", 10, 50, 30)
            with col3:
                st.caption("Markets: 15 EN + 16 RU")
                st.caption("Products: 4 EN + 3 RU")
                st.caption("Intent types: 5")

            if st.button("🧮 Generate Matrix", type="primary"):
                with st.spinner("Generating keyword combinations..."):
                    matrix = generate_kw_matrix(
                        include_en=incl_en, include_ru=incl_ru,
                        include_b2b=incl_b2b, max_per_market=max_per,
                    )
                    # Convert to Keyword objects and score
                    kws = []
                    for m in matrix:
                        kw = Keyword(
                            keyword=m["q"], language=m["lang"], market=m["market"],
                            category=m.get("category", classify_keyword(m["q"])),
                            intent=m.get("intent", "transactional"),
                        )
                        kw.priority_score = score_keyword(kw)
                        kws.append(kw)
                    kws.sort(key=lambda k: -k.priority_score)
                    st.session_state["matrix_keywords"] = kws

                st.success(f"Generated **{len(kws)}** keywords")

            if "matrix_keywords" in st.session_state:
                kws = st.session_state["matrix_keywords"]
                # Stats
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Total", len(kws))
                col_b.metric("Languages", len(set(k.language for k in kws)))
                col_c.metric("Markets", len(set(k.market for k in kws)))
                col_d.metric("Categories", len(set(k.category for k in kws)))

                # By market
                market_counts = {}
                for k in kws:
                    market_counts[k.market] = market_counts.get(k.market, 0) + 1
                st.markdown("**By market:**")
                mdf = pd.DataFrame([{"market": m, "keywords": c} for m, c in sorted(market_counts.items(), key=lambda x: -x[1])])
                st.dataframe(mdf, hide_index=True, height=200)

                # Preview top keywords
                st.markdown("**Top 30 by priority:**")
                df = pd.DataFrame(taxonomy_to_dicts(kws[:30]))
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Merge into main taxonomy
                if st.button("➕ Merge into Taxonomy"):
                    existing = st.session_state.get("kw_taxonomy", [])
                    existing_set = {k.keyword.lower() for k in existing}
                    added = sum(1 for k in kws if k.keyword.lower() not in existing_set)
                    merged = existing + [k for k in kws if k.keyword.lower() not in existing_set]
                    merged.sort(key=lambda k: -k.priority_score)
                    st.session_state["kw_taxonomy"] = merged
                    st.success(f"Added **{added}** new keywords to taxonomy (total: {len(merged)})")

        with disc_tab2:
            st.markdown("**Google Autocomplete** — type a seed, get real search suggestions. Free, no API key. Alphabet trick: tries `seed a`, `seed b`, ... `seed z` for max coverage.")

            seed = st.text_input("Seed keyword", value="crypto card", key="ac_seed")
            col1, col2 = st.columns(2)
            with col1:
                ac_lang = st.selectbox("Language", ["en", "ru", "it", "es", "pl", "pt", "id"], key="ac_lang")
            with col2:
                use_alphabet = st.checkbox("Alphabet expansion (a-z)", value=True,
                                           help="27 requests instead of 1, takes ~3 seconds")

            if st.button("🔤 Get Autocomplete Suggestions", type="primary"):
                with st.spinner("Querying Google Autocomplete..."):
                    if use_alphabet:
                        results = expand_with_autocomplete(seed, language=ac_lang)
                    else:
                        raw = get_google_autocomplete(seed, language=ac_lang)
                        results = [{"q": r, "lang": ac_lang, "market": detect_market(r) or "global",
                                    "category": classify_keyword(r), "intent": "transactional",
                                    "source": "google_autocomplete"} for r in raw]
                    st.session_state["ac_results"] = results

            if "ac_results" in st.session_state:
                results = st.session_state["ac_results"]
                st.success(f"**{len(results)}** suggestions found")
                df = pd.DataFrame(results)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True, height=400)

                    if st.button("➕ Add all to Taxonomy", key="ac_add"):
                        existing = st.session_state.get("kw_taxonomy", [])
                        existing_set = {k.keyword.lower() for k in existing}
                        added = 0
                        for r in results:
                            if r["q"].lower() not in existing_set:
                                kw = Keyword(
                                    keyword=r["q"], language=r.get("lang", "en"),
                                    market=r.get("market", "global"),
                                    category=r.get("category", classify_keyword(r["q"])),
                                )
                                kw.priority_score = score_keyword(kw)
                                existing.append(kw)
                                added += 1
                        existing.sort(key=lambda k: -k.priority_score)
                        st.session_state["kw_taxonomy"] = existing
                        st.success(f"Added {added} new keywords")

        with disc_tab3:
            st.markdown("**Ask Perplexity AI:** 'What do people search for about crypto cards in [market]?' Returns real search queries people use. ~$0.005/market.")

            if not pplx_key:
                st.warning("Enter Perplexity API key in sidebar")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    disc_market = st.selectbox("Market to discover", [
                        "UAE", "UK", "Italy", "Spain", "Poland", "Germany",
                        "Europe", "Indonesia", "Romania", "Georgia", "Uzbekistan",
                    ], key="disc_market")
                with col2:
                    disc_lang = st.selectbox("Language", ["en", "ru"], key="disc_lang")

                if st.button("🤖 Discover Keywords via AI", type="primary"):
                    with st.spinner(f"Asking Perplexity about crypto cards in {disc_market}..."):
                        results = discover_keywords_perplexity(
                            pplx_key, disc_market, language=disc_lang,
                        )
                        st.session_state["pplx_discovery"] = results

                if "pplx_discovery" in st.session_state:
                    results = st.session_state["pplx_discovery"]
                    st.success(f"**{len(results)}** keyword ideas discovered")
                    df = pd.DataFrame(results)
                    if not df.empty:
                        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

                        if st.button("➕ Add all to Taxonomy", key="pplx_add"):
                            existing = st.session_state.get("kw_taxonomy", [])
                            existing_set = {k.keyword.lower() for k in existing}
                            added = 0
                            for r in results:
                                if r["q"].lower() not in existing_set:
                                    kw = Keyword(
                                        keyword=r["q"], language=r.get("lang", "en"),
                                        market=r.get("market", "global"),
                                        category=r.get("category", classify_keyword(r["q"])),
                                    )
                                    kw.priority_score = score_keyword(kw)
                                    existing.append(kw)
                                    added += 1
                            existing.sort(key=lambda k: -k.priority_score)
                            st.session_state["kw_taxonomy"] = existing
                            st.success(f"Added {added} new keywords")

    # ── TAB 3: Geo Market Audit ──────────────────────────────────────────
    with tab_geo_audit:
        st.subheader("🌍 Geo-Targeted AI Visibility Audit")
        st.markdown("""
Select your target markets → generates **local prompts** per market (EN + local language) → checks Perplexity AI for Kolo visibility.

Shows you **per-market**: is Kolo visible in AI answers? Which competitors dominate each geography?
""")

        if not pplx_key:
            st.warning("Enter Perplexity API key in the sidebar.")
        else:
            # Market selection
            all_markets = list(GEO_MARKETS.keys())
            market_labels = {k: f"{v.get('name', k)} ({v.get('lang', 'en').upper()})" for k, v in GEO_MARKETS.items()}

            col1, col2 = st.columns([2, 1])
            with col1:
                selected_markets = st.multiselect(
                    "Target markets",
                    all_markets,
                    default=["GBR", "ARE", "ITA", "ESP", "POL"],
                    format_func=lambda x: market_labels.get(x, x),
                )
            with col2:
                max_per = st.slider("Prompts per market", 2, 10, 5, help="More = deeper audit, more cost")
                incl_local = st.checkbox("Include local language", value=True, help="e.g. Italian for ITA, Russian for CIS")

            # Categories
            cat_options = ["head", "long_tail", "problem", "comparison", "b2b"]
            selected_cats = st.multiselect("Prompt categories", cat_options, default=["head", "long_tail", "problem"])

            # Preview prompts
            preview = generate_geo_prompts(selected_markets, categories=selected_cats, include_local_lang=incl_local)
            total_prompts = min(len(preview), len(selected_markets) * max_per)
            est_cost = total_prompts * 0.005

            with st.expander(f"Preview prompts ({len(preview)} generated, {total_prompts} will be run)"):
                for m in selected_markets:
                    market_prompts = [p for p in preview if p["market"] == m]
                    st.markdown(f"**{market_labels.get(m, m)}** ({len(market_prompts)} prompts)")
                    for p in market_prompts[:max_per]:
                        lang_tag = f"[{p['language'].upper()}]"
                        cat_tag = p['category']
                        st.markdown(f"- {lang_tag} *{cat_tag}* — {p['prompt']}")

            st.caption(f"Estimated cost: **${est_cost:.2f}** ({total_prompts} prompts × $0.005)")

            if st.button("🌍 Run Geo Market Audit", type="primary"):
                progress = st.progress(0, text="Running geo audit...")
                results = []
                market_count = {}

                all_prompts = generate_geo_prompts(selected_markets, categories=selected_cats, include_local_lang=incl_local)
                # Filter to max_per
                filtered_prompts = []
                for p in all_prompts:
                    mc = p["market"]
                    if market_count.get(mc, 0) < max_per:
                        filtered_prompts.append(p)
                        market_count[mc] = market_count.get(mc, 0) + 1

                for i, p in enumerate(filtered_prompts):
                    progress.progress((i + 1) / len(filtered_prompts),
                                      text=f"[{p['market']}] {p['prompt'][:50]}...")
                    result = perplexity_audit_prompt(pplx_key, p["prompt"])
                    result["market"] = p["market"]
                    result["language"] = p["language"]
                    result["category"] = p["category"]
                    results.append(result)
                    import time; time.sleep(0.5)

                progress.progress(1.0, text="Done!")
                st.session_state["geo_market_results"] = results

            if "geo_market_results" in st.session_state:
                results = st.session_state["geo_market_results"]
                by_market = summarize_by_market(results)

                # Overall metrics
                total = len(results)
                kolo_total = sum(1 for r in results if r.get("kolo_visible"))
                errors = sum(1 for r in results if r.get("error"))

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Markets Tested", len(by_market))
                col_b.metric("Total Prompts", total)
                col_c.metric("Kolo Visible Overall", f"{kolo_total}/{total - errors}")

                # Per-market summary cards
                st.subheader("Per-Market Results")

                # Sort markets by kolo visibility (worst first = needs most attention)
                sorted_markets = sorted(by_market.values(), key=lambda x: x["kolo_pct"])

                for ms in sorted_markets:
                    market_name = ms["market_name"]
                    kolo_pct = ms["kolo_pct"]

                    if kolo_pct == 0:
                        icon = "🔴"
                    elif kolo_pct < 50:
                        icon = "🟡"
                    else:
                        icon = "🟢"

                    comps_str = ", ".join(f"{c[0]} ({c[1]}x)" for c in ms["top_competitors"]) or "None detected"

                    with st.expander(f"{icon} **{market_name}** — Kolo visible: {ms['kolo_visible']}/{ms['prompts_tested']} ({kolo_pct}%) | Competitors: {comps_str}"):
                        for r in ms["results"]:
                            vis = "✅" if r.get("kolo_visible") else "❌"
                            lang = r.get("language", "en").upper()
                            cat = r.get("category", "")
                            comps = ", ".join(r.get("competitors_mentioned", [])) or "—"
                            st.markdown(f"{vis} [{lang}] *{cat}* — **{r['prompt'][:80]}**")
                            if r.get("competitors_mentioned"):
                                st.caption(f"   Competitors in answer: {comps}")
                            if r.get("citations"):
                                st.caption(f"   Sources: {', '.join(r['citations'][:3])}")

                # Market comparison table
                st.subheader("Market Comparison")
                table_rows = []
                for ms in sorted_markets:
                    top_comp = ms["top_competitors"][0][0] if ms["top_competitors"] else "—"
                    table_rows.append({
                        "Market": ms["market_name"],
                        "Kolo Visible": f"{ms['kolo_visible']}/{ms['prompts_tested']}",
                        "Kolo %": ms["kolo_pct"],
                        "Top Competitor": top_comp,
                        "Status": "🔴 Not visible" if ms["kolo_pct"] == 0 else ("🟡 Partial" if ms["kolo_pct"] < 50 else "🟢 Good"),
                    })
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                # Export
                export_rows = []
                for r in results:
                    export_rows.append({
                        "market": r.get("market", ""),
                        "language": r.get("language", ""),
                        "category": r.get("category", ""),
                        "prompt": r.get("prompt", ""),
                        "kolo_visible": r.get("kolo_visible", False),
                        "kolo_in_text": r.get("kolo_in_text", False),
                        "kolo_in_citations": r.get("kolo_in_citations", False),
                        "competitors": ", ".join(r.get("competitors_mentioned", [])),
                        "citations": " | ".join(r.get("citations", [])[:3]),
                    })
                csv = pd.DataFrame(export_rows).to_csv(index=False)
                st.download_button("📥 Download geo audit CSV", data=csv,
                                   file_name=f"geo_market_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv")

    # ── TAB 4: AI Prompt Audit (Perplexity) ──────────────────────────────
    with tab_ai_audit:
        st.subheader("AI Citation Visibility Audit")
        st.markdown("Sends prompts to **Perplexity AI** and checks if Kolo appears in the answer or cited sources. Cost: ~$0.005/prompt.")

        if not pplx_key:
            st.warning("Enter your Perplexity API key in the sidebar to run AI audits.")
            st.markdown("Get one at [perplexity.ai/settings/api](https://perplexity.ai/settings/api)")
        else:
            # Show default prompts
            with st.expander("Default AI prompts (24)", expanded=False):
                for i, p in enumerate(DEFAULT_GEO_PROMPTS, 1):
                    st.markdown(f"{i}. **{p}**")

            col1, col2 = st.columns(2)
            with col1:
                prompt_source = st.radio("Prompt source", ["Default (24 prompts)", "Custom"])
            with col2:
                if prompt_source == "Custom":
                    custom_prompts = st.text_area("One prompt per line", height=200)

            max_prompts = st.slider("Max prompts to run", 1, 24, 10, help="Each costs ~$0.005")
            est_cost = max_prompts * 0.005
            st.caption(f"Estimated cost: ~${est_cost:.3f}")

            if st.button("🤖 Run AI Prompt Audit", type="primary"):
                if prompt_source == "Custom" and custom_prompts:
                    prompts = [p.strip() for p in custom_prompts.strip().split("\n") if p.strip()]
                else:
                    prompts = DEFAULT_GEO_PROMPTS

                prompts = prompts[:max_prompts]

                progress = st.progress(0, text="Querying Perplexity AI...")
                results = []
                for i, prompt in enumerate(prompts):
                    progress.progress((i + 1) / len(prompts), text=f"Prompt {i+1}/{len(prompts)}: {prompt[:50]}...")
                    result = perplexity_audit_prompt(pplx_key, prompt)
                    results.append(result)
                progress.progress(1.0, text="Done!")

                st.session_state["ai_audit_results"] = results

            if "ai_audit_results" in st.session_state:
                results = st.session_state["ai_audit_results"]
                summary = summarize_geo_audit(results)

                # Metrics
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Prompts Tested", summary["total_prompts"])
                col_b.metric("Kolo in Text", f"{summary['kolo_in_text_count']} ({summary['kolo_in_text_pct']}%)")
                col_c.metric("Kolo in Citations", f"{summary['kolo_in_citations_count']} ({summary['kolo_in_citations_pct']}%)")
                col_d.metric("Est. Cost", f"${summary['estimated_cost_usd']:.3f}")

                # Kolo visibility status
                if summary["kolo_visible_pct"] == 0:
                    st.error(f"⚠️ Kolo is NOT visible in any AI answer. Competitors dominating: {', '.join(c[0] for c in summary['top_competitors_in_ai'][:3])}")
                elif summary["kolo_visible_pct"] < 30:
                    st.warning(f"Kolo visible in {summary['kolo_visible_pct']}% of AI answers. Main competitors: {', '.join(c[0] for c in summary['top_competitors_in_ai'][:3])}")
                else:
                    st.success(f"Kolo visible in {summary['kolo_visible_pct']}% of AI answers!")

                # Competitor presence in AI
                if summary["top_competitors_in_ai"]:
                    st.subheader("Competitors in AI Answers")
                    comp_df = pd.DataFrame([{"Competitor": c, "Mentioned in": f"{n}/{summary['total_prompts']} prompts"}
                                            for c, n in summary["top_competitors_in_ai"]])
                    st.dataframe(comp_df, hide_index=True)

                # Per-prompt results
                st.subheader("Per-Prompt Results")
                for r in results:
                    icon = "✅" if r.get("kolo_visible") else "❌"
                    with st.expander(f"{icon} {r['prompt'][:80]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Kolo in text:** {'Yes' if r.get('kolo_in_text') else 'No'}")
                            st.markdown(f"**Kolo in citations:** {'Yes' if r.get('kolo_in_citations') else 'No'}")
                            if r.get("competitors_mentioned"):
                                st.markdown(f"**Competitors mentioned:** {', '.join(r['competitors_mentioned'])}")
                        with col2:
                            st.markdown(f"**Citations ({r.get('citation_count', 0)}):**")
                            for url in r.get("citations", [])[:5]:
                                st.markdown(f"- {url}")
                        if r.get("answer_preview"):
                            st.markdown("**AI Answer Preview:**")
                            st.text(r["answer_preview"][:400])

                # Export
                export_rows = [{
                    "prompt": r["prompt"],
                    "kolo_in_text": r.get("kolo_in_text"),
                    "kolo_in_citations": r.get("kolo_in_citations"),
                    "competitors": ", ".join(r.get("competitors_mentioned", [])),
                    "citation_count": r.get("citation_count", 0),
                    "citations": " | ".join(r.get("citations", [])[:3]),
                } for r in results]
                csv = pd.DataFrame(export_rows).to_csv(index=False)
                st.download_button("📥 Download AI audit CSV", data=csv,
                                   file_name=f"ai_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv")

    # ── TAB 4: Keyword Expansion (SerpAPI — free) ────────────────────────
    with tab_expand:
        st.subheader("Keyword Expansion via Google")
        st.markdown("Uses SerpAPI to get **People Also Ask** and **Related Searches** for seed keywords. 1 credit per seed.")

        if not serp_key:
            st.warning("Enter SerpAPI key in the sidebar")
        else:
            seed_input = st.text_input("Seed keyword", value="crypto visa card Europe",
                                        help="Enter a seed keyword to expand")

            if st.button("🌱 Expand Keyword", type="primary"):
                with st.spinner("Searching Google..."):
                    expansion = expand_keywords_serpapi(serp_key, seed_input)
                    st.session_state["kw_expansion"] = expansion
                    st.session_state["kw_expansion_seed"] = seed_input

            if "kw_expansion" in st.session_state:
                expansion = st.session_state["kw_expansion"]
                seed = st.session_state["kw_expansion_seed"]

                st.markdown(f"**Seed:** {seed}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### People Also Ask")
                    for q in expansion.get("people_also_ask", []):
                        st.markdown(f"- {q}")
                    if not expansion.get("people_also_ask"):
                        st.info("No PAA found for this query")

                with col2:
                    st.markdown("### Related Searches")
                    for q in expansion.get("related_searches", []):
                        st.markdown(f"- {q}")
                    if not expansion.get("related_searches"):
                        st.info("No related searches found")

                # Quick add to taxonomy
                all_new = expansion.get("people_also_ask", []) + expansion.get("related_searches", [])
                if all_new:
                    st.divider()
                    st.markdown(f"**{len(all_new)} new keyword ideas** discovered")
                    if st.button("➕ Add all to taxonomy"):
                        new_seeds = [{"q": q, "lang": detect_language(q), "market": detect_market(q)} for q in all_new]
                        existing = st.session_state.get("kw_taxonomy", [])
                        existing_set = {k.keyword.lower() for k in existing}
                        added = 0
                        for seed_dict in new_seeds:
                            if seed_dict["q"].lower() not in existing_set:
                                kw = Keyword(
                                    keyword=seed_dict["q"],
                                    language=seed_dict["lang"],
                                    market=seed_dict["market"],
                                    category=classify_keyword(seed_dict["q"]),
                                )
                                kw.priority_score = score_keyword(kw)
                                existing.append(kw)
                                added += 1
                        existing.sort(key=lambda k: -k.priority_score)
                        st.session_state["kw_taxonomy"] = existing
                        st.success(f"Added {added} new keywords to taxonomy")


pg = st.navigation({
    "": [
        st.Page(page_dashboard,        title="Dashboard",        icon="🤖", default=True),
    ],
    "Stages": [
        st.Page(page_kolo_metrics,     title="Kolo Metrics",     icon="📈"),
        st.Page(page_content_plan,     title="Content Plan",     icon="✍️"),
        st.Page(page_outlet_matching,  title="Outlet Matching",  icon="🗞️"),
        st.Page(page_publication_roi,  title="Publication ROI",  icon="💰"),
    ],
    "Actions": [
        st.Page(page_pr_generator,           title="PR Generator",     icon="📝"),
        st.Page(page_content_distribution,   title="Distribution",     icon="📣"),
        st.Page(page_monthly_eval,           title="Monthly Eval",     icon="📉"),
        st.Page(page_monthly_planner,        title="Monthly Planner",  icon="🗓️"),
    ],
    "Growth": [
        st.Page(page_keyword_intel,          title="Keyword Intel",    icon="🧠"),
        st.Page(page_programmatic_seo,       title="Programmatic SEO", icon="🚀"),
    ],
})
pg.run()
