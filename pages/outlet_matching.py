"""Page 4 — Outlet Matching: live Collaborator.pro search, 5-dim scoring, budget analysis."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt

from data_sources import DATA, score_outlet_notion, outlet_verdict
from collaborator_outlets import (
    get_outlets, get_top_outlets_all_langs,
    LANG_LABELS, score_label, RAW_OUTLETS,
)
from config import PILLAR_BUDGET_CAPS


def page_outlet_matching():
    st.title("🗞️ Stage 4 · Outlet Matching")
    st.caption("Scoring: 6-dimension 0–18 system (SEO + GEO) · Source of truth for all outlet decisions")

    with st.expander("ℹ️ How outlet scoring works", expanded=False):
        st.markdown("""
**6-dimension scoring model (0-18 points max):**
Each outlet is scored on 6 factors, each worth 0-3 points:

1. **Domain Rating (DR)** — Ahrefs authority: DR≥60 = 3pts, DR≥45 = 2pts, DR≥30 = 1pt
2. **Traffic** — monthly organic visitors: ≥100K = 3pts, ≥30K = 2pts, ≥5K = 1pt
3. **Crypto category** — has dedicated crypto/finance section: yes = 3pts
4. **Price** — cost per publication: ≤$50 = 3pts, ≤$100 = 2pts, ≤$200 = 1pt
5. **GEO citability** — how likely AI engines cite this outlet: high = 3pts
6. **Language fit** — matches a priority market language: exact match = 3pts

**Verdict:** ≥14 = must-buy, ≥11 = strong, ≥8 = viable, <8 = skip
""")

    st.success(
        "✅ **Catalog scraped via browser session** — "
        f"{sum(len(v) for v in RAW_OUTLETS.values())} sites across 7 languages "
        "· Filters: DR ≥ 30, price ≤ $250, categories: Crypto + Business & Finance · Refreshed 2026-03-11"
    )

    # ── Scoring Model ──────────────────────────────────────────────
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

    # ── Live Catalog Search ───────────────────────────────────────
    st.header("🔍 Live Catalog Search")
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1, 1, 1, 1])
    with fc1:
        selected_langs = st.multiselect(
            "Languages", options=list(LANG_LABELS.keys()),
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
            use_container_width=True, hide_index=True,
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

    # ── Top Picks per Pillar ──────────────────────────────────────
    st.header("🏆 Top Picks per Pillar")
    st.caption("Best 5 per language · DR ≥ 40 · Price ≤ $200 · sorted by score then DR · catalog scores 0-15 (add +0-3 for AI citability)")
    top = get_top_outlets_all_langs(min_dr=40, max_price=200, top_n=5)
    visible_langs = [l for l in selected_langs if top.get(l)]
    cols = st.columns(len(visible_langs) or 1)
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

    # ── March 2026 Confirmed Outlets ──────────────────────────────
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
                "Lang": lang.upper(), "Outlet": s["name"], "Price": s["price"],
                "DR": s["dr"], "Pillar": s["pillar"], "Score": notion_score,
                "Verdict": verdict, "Status": status, "Notes": s.get("notes", ""),
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
        use_container_width=True, hide_index=True,
        column_config={
            "Price":  st.column_config.NumberColumn("Price ($)", format="$%d"),
            "DR":     st.column_config.NumberColumn("DR"),
            "Score":  st.column_config.NumberColumn("Score /15"),
        },
    )

    # ── Key Callouts ──────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.success("**🆕 pt.egamersworld.com added (score 13/15)**\n\nIn Notion guide as 'Must buy' — DR>65, >100K traffic, >50% search. Price TBD. Portuguese/Brazil pillar.")
        st.warning("**⚠️ financial-news.co.uk — NOT in Notion guide**\n\nIn March plan but never scored by the guide. Verify independently (DR 54, \\$125) before purchasing.")
    with col_b:
        st.warning("**⚠️ sevillaBN — NOT in Notion guide**\n\nIn March plan but never scored. Verify independently before purchasing.")
        st.info("**sticknoticias.com → Score 3 → Skip**\n\ncoinarbitragebot → Score 9 → Skip (0% search)\n\nBoth in Notion guide as hard Skips — do not buy.")

    # ── Budget Breakdown ──────────────────────────────────────────
    st.header("Pillar Budget Allocation")
    pillar_budget = (
        outlets_df.dropna(subset=["Price"])
        .groupby("Pillar")["Price"].sum()
        .reset_index()
    )
    pillar_budget.columns = ["Pillar", "Spent"]
    pillar_budget["Cap"]       = pillar_budget["Pillar"].map(PILLAR_BUDGET_CAPS).fillna(200)
    pillar_budget["Remaining"] = pillar_budget["Cap"] - pillar_budget["Spent"]
    pillar_budget["Util %"]    = (pillar_budget["Spent"].fillna(0) / pillar_budget["Cap"].fillna(200).replace(0, 1) * 100).round(0).fillna(0).astype(float).astype(int)

    def color_util(val):
        if val >= 90: return "background-color: #ffd6d6"
        if val >= 60: return "background-color: #fff3cd"
        return "background-color: #d4edda"

    st.dataframe(
        pillar_budget.style.map(color_util, subset=["Util %"]),
        use_container_width=True, hide_index=True,
        column_config={
            "Spent":     st.column_config.NumberColumn("Spent ($)", format="$%d"),
            "Cap":       st.column_config.NumberColumn("Cap ($)",   format="$%d"),
            "Remaining": st.column_config.NumberColumn("Remaining ($)", format="$%d"),
        },
    )
