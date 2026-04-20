"""Page — Keyword Intelligence: generate → filter → autocomplete validate."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from keyword_research import (
    Keyword, taxonomy_to_dicts, classify_keyword, score_keyword,
    generate_keyword_matrix as generate_kw_matrix,
    get_google_autocomplete,
)


def page_keyword_intel():
    st.title("🧠 Keyword Intelligence")
    st.caption("Generate → Filter → Validate via Google Autocomplete. All free. AI visibility lives in GEO Tracker.")

    # Step 1: Generate
    st.markdown("### Step 1 · Generate Keyword Matrix")
    c1, c2, c3 = st.columns(3)
    with c1:
        incl_en = st.checkbox("English keywords", value=True, key="pipe_en")
        incl_ru = st.checkbox("Russian keywords", value=True, key="pipe_ru", help="RU = 2x LTV")
    with c2:
        incl_b2b = st.checkbox("B2B keywords", value=True, key="pipe_b2b")
        max_per = st.slider("Max per market", 10, 50, 30, key="pipe_max")
    with c3:
        st.caption("Markets: 15 EN + 16 RU · Products: 4 EN + 3 RU")

    if st.button("🧮 Generate Matrix", type="primary", key="pipe_gen"):
        with st.spinner("Generating keyword combinations..."):
            matrix = generate_kw_matrix(include_en=incl_en, include_ru=incl_ru,
                                        include_b2b=incl_b2b, max_per_market=max_per)
            kws = []
            for m in matrix:
                kw = Keyword(keyword=m["q"], language=m["lang"], market=m["market"],
                             category=m.get("category", classify_keyword(m["q"])),
                             intent=m.get("intent", "transactional"))
                kw.priority_score = score_keyword(kw)
                kws.append(kw)
            kws.sort(key=lambda k: -k.priority_score)
            st.session_state["pipe_candidates"] = kws
            st.session_state.pop("pipe_selected", None)
            st.session_state.pop("pipe_ac_results", None)
        st.success(f"Generated **{len(kws)}** keywords")

    # Step 2: Filter & select
    if "pipe_candidates" in st.session_state:
        kws = st.session_state["pipe_candidates"]
        st.divider()
        st.markdown("### Step 2 · Filter & Select")

        f1, f2, f3 = st.columns(3)
        with f1:
            filt_lang = st.multiselect("Language", sorted(set(k.language for k in kws)), key="pipe_fl")
        with f2:
            filt_market = st.multiselect("Market", sorted(set(k.market for k in kws)), key="pipe_fm")
        with f3:
            filt_cat = st.multiselect("Category", sorted(set(k.category for k in kws)), key="pipe_fc")
        top_n = st.slider("Top N", 10, min(200, len(kws)), min(50, len(kws)), key="pipe_topn")

        filtered = kws
        if filt_lang:
            filtered = [k for k in filtered if k.language in filt_lang]
        if filt_market:
            filtered = [k for k in filtered if k.market in filt_market]
        if filt_cat:
            filtered = [k for k in filtered if k.category in filt_cat]
        selected = filtered[:top_n]

        st.markdown(f"**Selected {len(selected)}** (from {len(filtered)} after filters)")
        st.dataframe(pd.DataFrame(taxonomy_to_dicts(selected)), use_container_width=True, hide_index=True, height=300)

        if st.button("✅ Confirm → Autocomplete validation", type="primary", key="pipe_confirm"):
            st.session_state["pipe_selected"] = selected
            st.session_state.pop("pipe_ac_results", None)

    # Step 3: Autocomplete
    if "pipe_selected" in st.session_state:
        selected = st.session_state["pipe_selected"]
        st.divider()
        st.markdown("### Step 3 · Google Autocomplete Validation")
        st.caption(f"Validates {len(selected)} keywords against Google Autocomplete (free)")

        if st.button("🔍 Validate", type="primary", key="pipe_ac"):
            progress = st.progress(0)
            ac_results = []
            for i, kw in enumerate(selected):
                suggestions = get_google_autocomplete(kw.keyword)
                ac_results.append({
                    "keyword": kw.keyword, "language": kw.language, "market": kw.market,
                    "priority_score": kw.priority_score,
                    "autocomplete_hits": len(suggestions),
                    "suggestions": suggestions[:5],
                })
                progress.progress((i + 1) / len(selected))
            st.session_state["pipe_ac_results"] = ac_results
            progress.empty()

        if "pipe_ac_results" in st.session_state:
            ac_results = st.session_state["pipe_ac_results"]
            confirmed = [r for r in ac_results if r["autocomplete_hits"] > 0]
            st.success(f"**{len(confirmed)}/{len(ac_results)}** keywords have autocomplete signals")
            ac_df = pd.DataFrame(ac_results).sort_values("autocomplete_hits", ascending=False)
            st.dataframe(ac_df, use_container_width=True, hide_index=True, height=400)
            st.download_button("📥 Download CSV", data=ac_df.to_csv(index=False),
                file_name=f"keywords_validated_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")
