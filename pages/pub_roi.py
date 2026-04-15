"""Page 5 — Publication ROI: per-publication ROI calculator (4-layer model), batch ROI, LTV benchmarks."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt

from data_sources import DATA
from collaborator_outlets import LANG_LABELS, RAW_OUTLETS
from publication_roi import (
    calculate_publication_roi, batch_roi, roi_label,
    LTV_BY_LANG, CONVERSION_RATE_BY_LANG, LTV_BY_MARKET_LANG,
)
from config import LANG_MAP


def page_publication_roi():
    st.title("💰 Stage 5 · Publication ROI")
    st.caption("4-layer model: direct referral + SEO compound + GEO/AI citation + revenue")

    with st.expander("ℹ️ How the ROI model works", expanded=False):
        st.markdown("""
**4 traffic layers per publication:**

1. **Direct referral** — visitors who click the link in your article → tracked via UTM
2. **SEO compound** — the backlink improves your ranking → more organic traffic over 90 days
3. **GEO/AI citation** — AI engines (ChatGPT, Perplexity) cite the outlet → additional visitors
4. **Revenue** = total visitors × conversion rate × LTV

**Revenue:** total visitors × conversion rate (by language) × LTV (by market+language). Russian = 2x LTV vs English.

**3 scenarios** with multipliers: conservative (0.5×/0.4×/0.3×), mid (1×), optimistic (1.6×/2×/2.5×)
""")

    # ── Assumption Controls ───────────────────────────────────────
    with st.expander("⚙️ Model Assumptions", expanded=False):
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            article_ctr = st.slider("% of outlet traffic that sees article",
                                     0.05, 0.50, 0.20, 0.05,
                                     help="Typical sponsored post: 0.10–0.25% of monthly visitors")
            ref_ctr = st.slider("% of article readers who click to kolo.in",
                                 0.5, 5.0, 1.5, 0.5,
                                 help="Crypto-interested audience: 1–3%")
        with ac2:
            seo_months = st.slider("SEO compound window (months)", 1, 6, 3,
                                    help="How many months to count the backlink traffic lift")
            default_rank = st.slider("Assumed current rank if unknown", 10, 30, 20,
                                      help="Where kolo.in ranks for target keyword without this link")
            ai_search_share = st.slider("AI share of search (%)", 2, 20, 8,
                                         help="% of search traffic now going through AI engines")
            ai_search_frac = ai_search_share / 100.0
        with ac3:
            st.markdown("**LTV by language (from Hex)**")
            for lang, ltv in LTV_BY_LANG.items():
                cr = CONVERSION_RATE_BY_LANG[lang]
                st.markdown(f"`{lang.upper()}` — LTV **${ltv:,}** · CR **{cr*100:.2f}%**")

    # ── Tabs ──────────────────────────────────────────────────────
    tab_batch, tab_calc, tab_ltv = st.tabs([
        "📋 March 2026 Portfolio", "🔬 Single-outlet Calculator", "📊 LTV Benchmark"
    ])

    # ── TAB 1: MARCH 2026 PORTFOLIO ──────────────────────────────
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
                    "outlet": s["name"], "lang": LANG_MAP.get(lang_key.upper(), "en"),
                    "price": price, "traffic": traffic, "dr": dr,
                    "has_crypto": True, "ai_citability": s.get("ai_citability", 1),
                })

        results = batch_roi(outlet_inputs, article_ctr, ref_ctr, seo_months, ai_search_frac)

        rows = []
        for r in results:
            m, lo, hi = r.mid(), r.low(), r.best()
            rows.append({
                "Outlet": r.outlet, "Lang": r.lang.upper(), "Price ($)": r.price,
                "DR": r.outlet_dr, "Traffic": r.outlet_traffic, "LTV ($)": int(r.ltv),
                "Conservative": f"{lo.roi_x}×", "Mid": f"{m.roi_x}×", "Optimistic": f"{hi.roi_x}×",
                "90d Revenue": m.revenue, "Registrations": m.registrations,
                "CAC ($)": m.cac, "Rating": roi_label(m.roi_x), "_roi": m.roi_x,
            })

        roi_df = pd.DataFrame(rows)

        def color_roi(row):
            v = row["_roi"]
            if v >= 10: return ["background-color: #c3e6cb"] * len(row)
            if v >= 5:  return ["background-color: #d4edda"] * len(row)
            if v >= 2:  return ["background-color: #e8f4fd"] * len(row)
            if v >= 1:  return ["background-color: #fff3cd"] * len(row)
            return ["background-color: #ffd6d6"] * len(row)

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
        chart_df = roi_df.groupby("Lang").agg(Spend=("Price ($)", "sum"), Revenue=("90d Revenue", "sum")).reset_index()
        chart_df["ROI"] = (chart_df["Revenue"] / chart_df["Spend"]).round(1)
        chart_melted = chart_df.melt(id_vars="Lang", value_vars=["Spend", "Revenue"], var_name="Type", value_name="USD")
        bar = (
            alt.Chart(chart_melted).mark_bar().encode(
                x=alt.X("Lang:N", title="Language Pillar"),
                y=alt.Y("USD:Q", title="USD ($)", stack=None),
                color=alt.Color("Type:N", scale=alt.Scale(domain=["Spend", "Revenue"], range=["#6c757d", "#28a745"])),
                tooltip=["Lang", "Type", alt.Tooltip("USD:Q", format="$,.0f")],
            ).properties(title="Spend vs 90-day Revenue by Language Pillar", height=280)
        )
        st.altair_chart(bar, use_container_width=True)

    # ── TAB 2: SINGLE OUTLET CALCULATOR ──────────────────────────
    with tab_calc:
        st.subheader("Single-outlet ROI Calculator")
        st.caption("Model any outlet — useful for evaluating new opportunities before buying.")

        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            c_outlet   = st.text_input("Outlet domain", "businessabc.net")
            c_lang     = st.selectbox("Language", list(LANG_LABELS.keys()), format_func=lambda k: LANG_LABELS[k])
            c_price    = st.number_input("Price ($)", 10, 1000, 100, 5)
        with cc2:
            c_traffic  = st.number_input("Monthly traffic", 1_000, 10_000_000, 100_000, 5_000)
            c_dr       = st.slider("DR", 20, 90, 60)
            c_crypto   = st.toggle("Crypto / Finance category", value=True)
        with cc3:
            c_kw_vol   = st.number_input("Target keyword monthly volume (0 = unknown)", 0, 500_000, 0, 500)
            c_rank     = st.slider("Current rank for that keyword", 1, 30, default_rank)
            c_market   = st.text_input("Market override (e.g. ARE, ISR, KAZ — optional)", "")
            c_ai_cite  = st.slider("AI Citability (GEO)", 0, 3, 1, help="0=Never cited by AI, 3=Frequently cited")

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
                st.metric("ROI",             f"{s.roi_x}×", roi_label(s.roi_x))
                st.metric("Registrations",   f"{s.registrations:.1f} users")
                st.metric("CAC",             f"${s.cac:.0f}/user")
                st.metric("Payback",         f"{s.payback_days} days")
                st.caption(f"Referral: {s.referral_visits:,} · SEO: {s.seo_visits_90d:,} · AI: {s.ai_visits_90d:,} visits")

        st.info(
            f"**Assumptions:** LTV = ${roi.ltv:,}/user · "
            f"Conversion rate = {roi.cr*100:.2f}% · "
            f"Article CTR = {article_ctr:.2f}% of outlet traffic"
        )

    # ── TAB 3: LTV BENCHMARK ─────────────────────────────────────
    with tab_ltv:
        st.subheader("LTV × Conversion Rate by Language Pillar")
        st.caption("Why language choice matters more than outlet DR. Source: Hex BigQuery cohort.")

        ltv_rows = []
        for lang, ltv in LTV_BY_LANG.items():
            cr = CONVERSION_RATE_BY_LANG[lang]
            rev_per_1k = ltv * cr * 1000
            ltv_rows.append({
                "Language": LANG_LABELS[lang], "LTV/user ($)": ltv,
                "Conv. rate": cr, "Rev / 1K visits": round(rev_per_1k),
                "vs EN baseline": f"{ltv / LTV_BY_LANG['en']:.1f}×",
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
        ml_rows = [
            {"Market-Lang": f"{m}-{l.upper()}", "LTV/user ($)": v, "vs EN": f"{v/LTV_BY_LANG['en']:.1f}×"}
            for (m, l), v in sorted(LTV_BY_MARKET_LANG.items(), key=lambda x: x[1], reverse=True)
        ]
        st.subheader("High-value Market × Language Combos")
        st.caption("Outlets that reach these specific audience segments command premium ROI.")
        st.dataframe(
            pd.DataFrame(ml_rows), use_container_width=True, hide_index=True,
            column_config={"LTV/user ($)": st.column_config.NumberColumn("LTV/user ($)", format="$%d")},
        )
