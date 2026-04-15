"""Page 12 — Keyword & AI Prompt Intelligence: taxonomy, discovery, geo audit, AI audit, expansion."""
from __future__ import annotations

import time
import streamlit as st
import pandas as pd

from keyword_research import (
    Keyword, build_taxonomy, taxonomy_to_dicts, filter_keywords,
    expand_keywords_serpapi, classify_keyword, detect_language, detect_market,
    score_keyword, generate_keyword_matrix as generate_kw_matrix,
    get_google_autocomplete, expand_with_autocomplete,
)
from perplexity_geo import (
    query_perplexity, analyze_perplexity_response, audit_prompt as perplexity_audit_prompt,
    run_geo_audit, summarize_geo_audit, DEFAULT_GEO_PROMPTS,
    GEO_MARKETS, generate_geo_prompts, run_geo_market_audit, summarize_by_market,
)


def page_keyword_intel():
    st.title("🧠 Keyword & AI Prompt Intelligence")
    st.caption("Competitive keyword research + Perplexity AI citation tracking")

    serp_key = st.session_state.get("serpapi_key")
    pplx_key = st.session_state.get("perplexity_key")
    ahrefs_key = st.session_state.get("ahrefs_key")

    tab_taxonomy, tab_discover, tab_geo_audit, tab_ai_audit, tab_expand = st.tabs([
        "📊 Taxonomy", "🔬 Discovery", "🌍 Geo Market Audit", "🤖 AI Prompt Audit", "🌱 Expansion"
    ])

    # ── TAB 1: Keyword Taxonomy ──────────────────────────────────
    with tab_taxonomy:
        st.subheader("Ranked Keyword Taxonomy")
        with st.expander("ℹ️ How keyword scoring works", expanded=False):
            st.markdown("""
**Priority score** (max ~100 pts) ranks which keywords to target first:
- **Volume** (0-30 pts) — log-scaled search volume
- **Difficulty** (0-25 pts) — inverse: easy keywords score higher
- **AI overview bonus** (+10 pts) — Google shows AI answer = GEO opportunity
- **Untapped bonus** (+10 pts) — Kolo doesn't rank yet
- **Category bonus** — comparison +10, problem/B2B +8, long-tail +5, branded -5
- **Language LTV multiplier** — RU ×1.5, EN ×1.0, IT/ES ×0.9, PL/RO ×0.8, ID ×0.5
""")

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
            filtered = taxonomy
            if lang_filter != "all":
                filtered = [k for k in filtered if k.language == lang_filter]
            if market_filter != "all":
                filtered = [k for k in filtered if k.market == market_filter]
            if cat_filter != "all":
                filtered = [k for k in filtered if k.category == cat_filter]

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Total Keywords", len(taxonomy))
            col_b.metric("Filtered", len(filtered))
            col_c.metric("Languages", len(set(k.language for k in taxonomy)))
            col_d.metric("Markets", len(set(k.market for k in taxonomy)))

            st.subheader("By Category")
            cat_counts = {}
            for k in filtered:
                cat_counts[k.category] = cat_counts.get(k.category, 0) + 1
            cat_df = pd.DataFrame([{"category": c, "count": n} for c, n in sorted(cat_counts.items(), key=lambda x: -x[1])])
            if not cat_df.empty:
                st.bar_chart(cat_df.set_index("category"))

            st.subheader("By Language")
            lang_counts = {}
            for k in filtered:
                lang_counts[k.language] = lang_counts.get(k.language, 0) + 1
            lang_df = pd.DataFrame([{"language": l, "count": n} for l, n in sorted(lang_counts.items(), key=lambda x: -x[1])])
            if not lang_df.empty:
                st.bar_chart(lang_df.set_index("language"))

            st.subheader(f"Keywords ({len(filtered)})")
            kw_dicts = taxonomy_to_dicts(filtered)
            df = pd.DataFrame(kw_dicts)
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)

            csv = df.to_csv(index=False)
            st.download_button("📥 Download taxonomy CSV", data=csv,
                               file_name=f"keyword_taxonomy_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── TAB 2: Discovery Pipeline ─────────────────────────────────
    with tab_discover:
        st.subheader("Keyword Discovery Pipeline")
        st.markdown("**One flow:** Generate → Select → Autocomplete validate → AI check → Final ranked list")

        with st.expander("ℹ️ How the pipeline works", expanded=False):
            st.markdown("""
**5-step sequential pipeline** — each step feeds the next:
1. **Generate Matrix** (free) — products × markets × languages × intent modifiers
2. **Select & Filter** — narrow down by language, market, category
3. **Autocomplete Validation** (free) — Google Autocomplete API
4. **AI Visibility Check** (~$0.005/query) — Perplexity AI
5. **Final Ranked Results** — combined table with priority + autocomplete + AI visibility
""")

        # Step 1: Generate
        st.markdown("### Step 1 · Generate Keyword Matrix")
        col1, col2, col3 = st.columns(3)
        with col1:
            incl_en = st.checkbox("English keywords", value=True, key="pipe_en")
            incl_ru = st.checkbox("Russian keywords", value=True, key="pipe_ru", help="RU = 2x LTV")
        with col2:
            incl_b2b = st.checkbox("B2B keywords", value=True, key="pipe_b2b")
            max_per = st.slider("Max per market", 10, 50, 30, key="pipe_max")
        with col3:
            st.caption("Markets: 15 EN + 16 RU")
            st.caption("Products: 4 EN + 3 RU")

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
                st.session_state.pop("pipe_ai_results", None)
            st.success(f"Generated **{len(kws)}** keywords")

        # Step 2: Select
        if "pipe_candidates" in st.session_state:
            kws = st.session_state["pipe_candidates"]
            st.divider()
            st.markdown("### Step 2 · Select Keywords to Validate")

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Total generated", len(kws))
            col_b.metric("Languages", len(set(k.language for k in kws)))
            col_c.metric("Markets", len(set(k.market for k in kws)))
            col_d.metric("Categories", len(set(k.category for k in kws)))

            f1, f2, f3 = st.columns(3)
            with f1:
                filt_lang = st.multiselect("Filter language", sorted(set(k.language for k in kws)), key="pipe_fl")
            with f2:
                filt_market = st.multiselect("Filter market", sorted(set(k.market for k in kws)), key="pipe_fm")
            with f3:
                filt_cat = st.multiselect("Filter category", sorted(set(k.category for k in kws)), key="pipe_fc")
            top_n = st.slider("Select top N", 10, min(200, len(kws)), min(50, len(kws)), key="pipe_topn")

            filtered = kws
            if filt_lang:
                filtered = [k for k in filtered if k.language in filt_lang]
            if filt_market:
                filtered = [k for k in filtered if k.market in filt_market]
            if filt_cat:
                filtered = [k for k in filtered if k.category in filt_cat]
            selected = filtered[:top_n]

            st.markdown(f"**Selected {len(selected)} keywords** (from {len(filtered)} after filters)")
            df_sel = pd.DataFrame(taxonomy_to_dicts(selected))
            st.dataframe(df_sel, use_container_width=True, hide_index=True, height=300)

            if st.button("✅ Confirm selection → proceed to Autocomplete", type="primary", key="pipe_confirm"):
                st.session_state["pipe_selected"] = selected
                st.session_state.pop("pipe_ac_results", None)
                st.session_state.pop("pipe_ai_results", None)

        # Step 3: Autocomplete
        if "pipe_selected" in st.session_state:
            selected = st.session_state["pipe_selected"]
            st.divider()
            st.markdown("### Step 3 · Google Autocomplete Validation")
            st.caption(f"Checks {len(selected)} keywords against Google Autocomplete (free)")

            if st.button("🔍 Validate via Autocomplete", type="primary", key="pipe_ac"):
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
                ac_df = pd.DataFrame(ac_results)
                st.dataframe(ac_df.sort_values("autocomplete_hits", ascending=False), use_container_width=True, hide_index=True, height=300)

        # Step 4: AI Visibility
        if "pipe_ac_results" in st.session_state:
            st.divider()
            st.markdown("### Step 4 · AI Visibility Check (Perplexity)")
            if not pplx_key:
                st.warning("Add Perplexity API key in sidebar")
            else:
                ac_results = st.session_state["pipe_ac_results"]
                confirmed = [r for r in ac_results if r["autocomplete_hits"] > 0]
                max_ai = st.slider("Max AI checks", 5, min(50, len(confirmed)), min(20, len(confirmed)), key="pipe_ai_max")
                est = max_ai * 0.005
                st.caption(f"~${est:.3f} estimated cost")

                if st.button("🤖 Check AI Visibility", type="primary", key="pipe_ai"):
                    progress = st.progress(0)
                    ai_results = []
                    for i, r in enumerate(confirmed[:max_ai]):
                        result = perplexity_audit_prompt(pplx_key, r["keyword"])
                        result["keyword"] = r["keyword"]
                        result["priority_score"] = r["priority_score"]
                        result["autocomplete_hits"] = r["autocomplete_hits"]
                        ai_results.append(result)
                        progress.progress((i + 1) / max_ai)
                        time.sleep(0.5)
                    st.session_state["pipe_ai_results"] = ai_results
                    progress.empty()

                if "pipe_ai_results" in st.session_state:
                    ai_results = st.session_state["pipe_ai_results"]
                    visible = sum(1 for r in ai_results if r.get("kolo_visible"))
                    st.metric("Kolo Visible", f"{visible}/{len(ai_results)}")
                    ai_df = pd.DataFrame([{
                        "keyword": r["keyword"], "kolo_visible": r.get("kolo_visible", False),
                        "competitors": ", ".join(r.get("competitors_mentioned", [])[:3]),
                        "priority": r.get("priority_score", 0),
                        "autocomplete": r.get("autocomplete_hits", 0),
                    } for r in ai_results])
                    st.dataframe(ai_df, use_container_width=True, hide_index=True)

                    csv = ai_df.to_csv(index=False)
                    st.download_button("📥 Download results", data=csv,
                        file_name=f"keyword_ai_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── TAB 3: Geo Market Audit ──────────────────────────────────
    with tab_geo_audit:
        st.subheader("Geo-Targeted AI Visibility Audit")
        st.info("Test AI visibility per market. Generates localized prompts in EN + local language.")

        if not pplx_key:
            st.warning("Add Perplexity API key in sidebar")
        else:
            available_markets = list(GEO_MARKETS.keys())
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_markets = st.multiselect("Markets", available_markets,
                    default=["UAE", "UK", "Italy", "Spain", "Georgia"], key="geo_mkt")
            with col2:
                selected_cats = st.multiselect("Categories",
                    ["product_comparison", "how_to", "geo_specific", "use_case", "cost_fees"],
                    default=["product_comparison", "geo_specific"], key="geo_cat")
            with col3:
                incl_local = st.checkbox("Include local language", value=True)
                max_per = st.slider("Max prompts per market", 3, 15, 5, key="geo_max_per")

            if st.button("🌍 Run Geo Audit", type="primary", key="geo_run"):
                results = []
                market_count = {}
                progress = st.progress(0, text="Generating prompts...")

                all_prompts = generate_geo_prompts(selected_markets, categories=selected_cats, include_local_lang=incl_local)
                filtered_prompts = []
                for p in all_prompts:
                    mc = p["market"]
                    if market_count.get(mc, 0) < max_per:
                        filtered_prompts.append(p)
                        market_count[mc] = market_count.get(mc, 0) + 1

                for i, p in enumerate(filtered_prompts):
                    progress.progress((i + 1) / len(filtered_prompts), text=f"[{p['market']}] {p['prompt'][:50]}...")
                    result = perplexity_audit_prompt(pplx_key, p["prompt"])
                    result["market"] = p["market"]
                    result["language"] = p["language"]
                    result["category"] = p["category"]
                    results.append(result)
                    time.sleep(0.5)

                progress.progress(1.0, text="Done!")
                st.session_state["geo_market_results"] = results

            if "geo_market_results" in st.session_state:
                results = st.session_state["geo_market_results"]
                by_market = summarize_by_market(results)

                total = len(results)
                kolo_total = sum(1 for r in results if r.get("kolo_visible"))
                errors = sum(1 for r in results if r.get("error"))

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Markets Tested", len(by_market))
                col_b.metric("Total Prompts", total)
                col_c.metric("Kolo Visible Overall", f"{kolo_total}/{total - errors}")

                st.subheader("Per-Market Results")
                sorted_markets = sorted(by_market.values(), key=lambda x: x["kolo_pct"])
                for ms in sorted_markets:
                    kolo_pct = ms["kolo_pct"]
                    icon = "🔴" if kolo_pct == 0 else ("🟡" if kolo_pct < 50 else "🟢")
                    comps_str = ", ".join(f"{c[0]} ({c[1]}x)" for c in ms["top_competitors"]) or "None"
                    with st.expander(f"{icon} **{ms['market_name']}** — {ms['kolo_visible']}/{ms['prompts_tested']} ({kolo_pct}%) | {comps_str}"):
                        for r in ms["results"]:
                            vis = "✅" if r.get("kolo_visible") else "❌"
                            lang = r.get("language", "en").upper()
                            cat = r.get("category", "")
                            st.markdown(f"{vis} [{lang}] *{cat}* — **{r['prompt'][:80]}**")

                st.subheader("Market Comparison")
                table_rows = [{"Market": ms["market_name"],
                    "Kolo Visible": f"{ms['kolo_visible']}/{ms['prompts_tested']}", "Kolo %": ms["kolo_pct"],
                    "Top Competitor": ms["top_competitors"][0][0] if ms["top_competitors"] else "—",
                    "Status": "🔴 Not visible" if ms["kolo_pct"] == 0 else ("🟡 Partial" if ms["kolo_pct"] < 50 else "🟢 Good"),
                } for ms in sorted_markets]
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                export_rows = [{"market": r.get("market", ""), "language": r.get("language", ""),
                    "category": r.get("category", ""), "prompt": r.get("prompt", ""),
                    "kolo_visible": r.get("kolo_visible", False),
                    "competitors": ", ".join(r.get("competitors_mentioned", [])),
                    "citations": " | ".join(r.get("citations", [])[:3]),
                } for r in results]
                csv = pd.DataFrame(export_rows).to_csv(index=False)
                st.download_button("📥 Download geo audit CSV", data=csv,
                    file_name=f"geo_market_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── TAB 4: AI Prompt Audit ────────────────────────────────────
    with tab_ai_audit:
        st.subheader("AI Citation Visibility Audit")
        with st.expander("ℹ️ How AI audit works", expanded=False):
            st.markdown("""
**Sends prompts to Perplexity AI and checks 3 layers:**
1. **Text mention** — does Perplexity mention Kolo?
2. **Source citations** — does Perplexity cite kolo.in?
3. **Competitor tracking** — who else appears?

**Cost:** ~$0.005 per prompt. 24 default prompts = ~$0.12.
""")

        if not pplx_key:
            st.warning("Enter your Perplexity API key in the sidebar.")
        else:
            with st.expander("Default AI prompts (24)", expanded=False):
                for i, p in enumerate(DEFAULT_GEO_PROMPTS, 1):
                    st.markdown(f"{i}. **{p}**")

            col1, col2 = st.columns(2)
            with col1:
                prompt_source = st.radio("Prompt source", ["Default (24 prompts)", "Custom"])
            with col2:
                custom_prompts = ""
                if prompt_source == "Custom":
                    custom_prompts = st.text_area("One prompt per line", height=200)

            max_prompts = st.slider("Max prompts to run", 1, 24, 10, help="Each costs ~$0.005")

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

                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Prompts Tested", summary["total_prompts"])
                col_b.metric("Kolo in Text", f"{summary['kolo_in_text_count']} ({summary['kolo_in_text_pct']}%)")
                col_c.metric("Kolo in Citations", f"{summary['kolo_in_citations_count']} ({summary['kolo_in_citations_pct']}%)")
                col_d.metric("Est. Cost", f"${summary['estimated_cost_usd']:.3f}")

                if summary["kolo_visible_pct"] == 0:
                    st.error(f"⚠️ Kolo NOT visible. Competitors: {', '.join(c[0] for c in summary['top_competitors_in_ai'][:3])}")
                elif summary["kolo_visible_pct"] < 30:
                    st.warning(f"Kolo visible in {summary['kolo_visible_pct']}% of answers")
                else:
                    st.success(f"Kolo visible in {summary['kolo_visible_pct']}% of AI answers!")

                if summary["top_competitors_in_ai"]:
                    st.subheader("Competitors in AI Answers")
                    comp_df = pd.DataFrame([{"Competitor": c, "Mentioned in": f"{n}/{summary['total_prompts']}"}
                                            for c, n in summary["top_competitors_in_ai"]])
                    st.dataframe(comp_df, hide_index=True)

                st.subheader("Per-Prompt Results")
                for r in results:
                    icon = "✅" if r.get("kolo_visible") else "❌"
                    with st.expander(f"{icon} {r['prompt'][:80]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Kolo in text:** {'Yes' if r.get('kolo_in_text') else 'No'}")
                            st.markdown(f"**Kolo in citations:** {'Yes' if r.get('kolo_in_citations') else 'No'}")
                            if r.get("competitors_mentioned"):
                                st.markdown(f"**Competitors:** {', '.join(r['competitors_mentioned'])}")
                        with col2:
                            st.markdown(f"**Citations ({r.get('citation_count', 0)}):**")
                            for url in r.get("citations", [])[:5]:
                                st.markdown(f"- {url}")
                        if r.get("answer_preview"):
                            st.text(r["answer_preview"][:400])

                export_rows = [{"prompt": r["prompt"], "kolo_in_text": r.get("kolo_in_text"),
                    "kolo_in_citations": r.get("kolo_in_citations"),
                    "competitors": ", ".join(r.get("competitors_mentioned", [])),
                    "citations": " | ".join(r.get("citations", [])[:3]),
                } for r in results]
                csv = pd.DataFrame(export_rows).to_csv(index=False)
                st.download_button("📥 Download AI audit CSV", data=csv,
                    file_name=f"ai_audit_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── TAB 5: Keyword Expansion ──────────────────────────────────
    with tab_expand:
        st.subheader("Keyword Expansion via Google")
        with st.expander("ℹ️ How keyword expansion works", expanded=False):
            st.markdown("""
**Uses SerpAPI** to extract Google's own keyword suggestions:
- **People Also Ask** — questions Google shows in search results
- **Related Searches** — keywords at the bottom of Google results

**Cost:** 1 SerpAPI credit per seed keyword.
""")

        if not serp_key:
            st.warning("Enter SerpAPI key in the sidebar")
        else:
            seed_input = st.text_input("Seed keyword", value="crypto visa card Europe")

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
                        st.info("No PAA found")
                with col2:
                    st.markdown("### Related Searches")
                    for q in expansion.get("related_searches", []):
                        st.markdown(f"- {q}")
                    if not expansion.get("related_searches"):
                        st.info("No related searches found")

                all_new = expansion.get("people_also_ask", []) + expansion.get("related_searches", [])
                if all_new:
                    st.divider()
                    st.markdown(f"**{len(all_new)} new keyword ideas** discovered")
                    if st.button("➕ Add all to taxonomy"):
                        existing = st.session_state.get("kw_taxonomy", [])
                        existing_set = {k.keyword.lower() for k in existing}
                        added = 0
                        for q in all_new:
                            if q.lower() not in existing_set:
                                kw = Keyword(keyword=q, language=detect_language(q),
                                             market=detect_market(q), category=classify_keyword(q))
                                kw.priority_score = score_keyword(kw)
                                existing.append(kw)
                                added += 1
                        existing.sort(key=lambda k: -k.priority_score)
                        st.session_state["kw_taxonomy"] = existing
                        st.success(f"Added {added} new keywords to taxonomy")
