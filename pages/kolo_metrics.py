"""Page 2 — Kolo Metrics: platform stats, P&L, country breakdown."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt
from data_sources import DATA


def page_kolo_metrics():
    st.title("📈 Stage 2 · Kolo Metrics")
    st.caption("Language & country analysis for SEO/GEO targeting · F&F excluded · STANDARD referrals only")

    st.warning(
        "⚠️ **Friends & Family users excluded** from all metrics. "
        "Data shows organic/standard users only — PRT, ARE and other markets "
        "may show lower numbers than before but are more accurate for SEO ROI projections."
    )

    # ── Language Clusters ──────────────────────────────────────────
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

    # ── Country Table ──────────────────────────────────────────────
    st.header("Country Performance (99 Active Markets)")
    countries = pd.DataFrame(DATA["countries"])
    tier_filter = st.multiselect(
        "Filter by tier", options=["1", "2", "3"], default=["1", "2"],
        format_func=lambda x: {"1": "Tier 1 (>$400K)", "2": "Tier 2 ($100K–$400K)",
                                "3": "Tier 3 ($30K–$100K)"}.get(x, x),
    )
    filtered = countries[countries["tier"].astype(str).isin(tier_filter)].copy()
    filtered = filtered.fillna(0)
    filtered["spend_fmt"] = filtered["card_spend"].apply(lambda x: f"${x/1e3:.0f}K" if x else "$0")
    filtered["spu_fmt"]   = filtered["spend_per_user"].apply(lambda x: f"${int(x):,}" if x else "$0")
    filtered["conv_fmt"]  = filtered["conversion"].apply(lambda x: f"{x*100:.0f}%" if x else "0%")

    def highlight_row(row):
        if row["Tier"] == "whale":
            return ["background-color: #fff3cd"] * len(row)
        try:
            conv = float(str(row.get("Conv.", "0")).replace("%", ""))
            if conv >= 80:
                return ["background-color: #d4edda"] * len(row)
        except (ValueError, TypeError):
            pass
        return [""] * len(row)

    st.dataframe(
        filtered[["flag", "country", "card_users", "spend_fmt", "spu_fmt", "conv_fmt", "tier"]]
        .rename(columns={"flag": "", "country": "Country", "card_users": "Users", "spend_fmt": "Spend",
                         "spu_fmt": "$/User", "conv_fmt": "Conv.", "tier": "Tier"})
        .style.apply(highlight_row, axis=1),
        use_container_width=True, hide_index=True,
    )
    st.caption("🟢 = ≥80% conversion")
    st.caption("Articles remain indexed 12+ months. Year-one ROI: estimated 4–15×.")
