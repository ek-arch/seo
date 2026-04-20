"""Page 12 — GEO Tracker: discover prompts via Claude → monitor Kolo mentions in Perplexity → find opportunities."""
from __future__ import annotations

import os
from datetime import datetime
import streamlit as st
import pandas as pd

from geo_prompt_research import (
    DISCOVERY_CATEGORIES, TARGET_MARKETS,
    discover_prompts_claude, get_builtin_prompts, monitor_prompts_batch,
    summarize_results, find_opportunities,
    save_results, load_results, list_cached_results,
)


def page_geo_tracker():
    st.title("🎯 GEO Tracker — AI Visibility Monitor")
    st.caption("Is Kolo mentioned when someone asks ChatGPT/Perplexity about crypto cards?")

    st.info("""
**What this does:** Sends crypto-card–related prompts to Perplexity AI and checks whether Kolo
appears in the answer, alongside which competitors got mentioned instead.

**Not about Google SEO** — for keyword research and landing-page generation, use the **SEO Factory** page.

**GEO = Generative Engine Optimization**: the AI-era equivalent of SEO.
""")

    with st.expander("ℹ️ How the 3 steps work", expanded=False):
        st.markdown("""
1. **Load prompts** — click Built-in for instant start, or let Claude discover more
2. **Monitor** — each prompt → Perplexity → we record if Kolo was mentioned and who else was (~$0.005/prompt)
3. **Results** — see the opportunity list: prompts where competitors show up but Kolo doesn't. Target those with PRs.
""")

    anthropic_key = (st.session_state.get("anthropic_token")
                     or st.session_state.get("anthropic_key")
                     or os.environ.get("ANTHROPIC_API_KEY", ""))
    perplexity_key = st.session_state.get("perplexity_key", "")

    tab_discover, tab_monitor, tab_results, tab_history = st.tabs([
        "1. Discover Prompts", "2. Monitor", "3. Results & Opportunities", "4. History"
    ])

    # ── Tab 1: Discover Prompts ───────────────────────────────────
    with tab_discover:
        st.subheader("AI Prompt Discovery")
        st.markdown("Use Claude to generate realistic prompts that real users type into AI assistants.")

        col1, col2 = st.columns(2)
        with col1:
            selected_categories = st.multiselect(
                "Categories", options=list(DISCOVERY_CATEGORIES.keys()),
                default=["product_comparison", "how_to", "geo_specific", "use_case"],
                format_func=lambda x: DISCOVERY_CATEGORIES[x]["label"],
            )
        with col2:
            selected_markets = st.multiselect(
                "Target Markets", options=list(TARGET_MARKETS.keys()),
                default=["UAE", "UK", "Italy", "Spain", "Georgia"],
            )

        col3, col4 = st.columns(2)
        with col3:
            selected_langs = st.multiselect("Languages", options=["en", "ru", "it", "es", "pl"], default=["en", "ru"])
        with col4:
            count_per_cat = st.slider("Prompts per category", 3, 20, 8)

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("📋 Load Built-in Prompts", type="primary"):
                prompts = get_builtin_prompts(
                    categories=selected_categories, markets=selected_markets,
                    languages=selected_langs,
                )
                st.session_state["geo_prompts"] = prompts
                st.success(f"Loaded {len(prompts)} built-in prompts — ready to monitor")
        with bcol2:
            if st.button("🔍 Discover more via Claude", disabled=not anthropic_key,
                         help="Optional: expand with fresh AI-generated prompts"):
                existing = [p["prompt"] for p in st.session_state.get("geo_prompts", [])]
                try:
                    with st.spinner(f"Claude is generating ~{count_per_cat * len(selected_categories)} prompts..."):
                        prompts = discover_prompts_claude(
                            anthropic_key, categories=selected_categories,
                            markets=selected_markets, languages=selected_langs,
                            count_per_category=count_per_cat, existing_prompts=existing,
                        )
                    st.session_state["geo_prompts"] = prompts
                    st.success(f"Discovered {len(prompts)} prompts")
                except Exception as e:
                    st.error(f"API error: {e}")

        prompts = st.session_state.get("geo_prompts", [])
        if prompts:
            df = pd.DataFrame(prompts)
            st.metric("Total Prompts", len(df))

            if "category" in df.columns:
                cats = df["category"].unique().tolist()
                filter_cat = st.multiselect("Filter by category", cats, default=cats, key="disc_filter")
                df = df[df["category"].isin(filter_cat)]

            st.dataframe(df[["prompt", "category", "language", "market", "intent"]], use_container_width=True, height=400)

            with st.expander("✏️ Add custom prompts"):
                custom = st.text_area("One prompt per line")
                custom_cat = st.selectbox("Category", list(DISCOVERY_CATEGORIES.keys()),
                                          format_func=lambda x: DISCOVERY_CATEGORIES[x]["label"])
                custom_lang = st.selectbox("Language", ["en", "ru", "it", "es", "pl"])
                custom_market = st.text_input("Market", "global")
                if st.button("Add Custom") and custom.strip():
                    for line in custom.strip().split("\n"):
                        line = line.strip()
                        if line:
                            prompts.append({"prompt": line, "category": custom_cat,
                                            "language": custom_lang, "market": custom_market, "intent": "informational"})
                    st.session_state["geo_prompts"] = prompts
                    st.rerun()

    # ── Tab 2: Monitor ────────────────────────────────────────────
    with tab_monitor:
        st.subheader("Monitor AI Visibility")
        st.markdown("Send each prompt to Perplexity and check if Kolo appears in the AI answer.")

        prompts = st.session_state.get("geo_prompts", [])
        if not prompts:
            st.info("Go to Tab 1 first and discover prompts")
        elif not perplexity_key:
            st.warning("Add Perplexity API key in sidebar")
        else:
            est_cost = len(prompts) * 0.005
            st.info(f"**{len(prompts)} prompts** to monitor · Est. cost: **${est_cost:.2f}** · ~{len(prompts) * 2}s")

            max_prompts = st.slider("Max prompts to monitor", 5, min(len(prompts), 200), min(len(prompts), 50))

            if st.button("▶️ Run Monitor", type="primary"):
                batch = prompts[:max_prompts]
                progress = st.progress(0, text="Monitoring prompts...")

                def on_progress(i, total, result):
                    progress.progress(i / total, text=f"Prompt {i}/{total}: {'✅' if result.kolo_visible else '❌'} {result.prompt[:60]}...")

                results = monitor_prompts_batch(perplexity_key, batch, delay=0.5, progress_callback=on_progress)
                progress.progress(1.0, text="Done!")
                st.session_state["geo_results"] = results

                save_path = save_results(results)
                st.success(f"Monitored {len(results)} prompts · Saved to {save_path}")

    # ── Tab 3: Results & Opportunities ────────────────────────────
    with tab_results:
        results = st.session_state.get("geo_results", [])
        if not results:
            st.info("Run the monitor first (Tab 2)")
        else:
            summary = summarize_results(results)

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Prompts", summary["total_prompts"])
            col2.metric("Kolo Visible", f"{summary['kolo_visible']} ({summary['kolo_visible_pct']}%)")
            col3.metric("Missing", f"{summary['missing']} ({summary['missing_pct']}%)")
            col4.metric("Avg Brands", summary["avg_brands_per_prompt"])
            col5.metric("Avg Sources", summary["avg_sources_per_prompt"])

            st.divider()

            # Prompt table
            st.subheader("Prompt Results")
            rows = [{"Prompt": r.prompt, "Mentioned": r.mentioned, "Brands": r.brands_count,
                      "Sources": r.sources_count, "Competitors": ", ".join(r.competitors_in_text[:3]),
                      "Category": r.category, "Market": r.market, "Lang": r.language} for r in results]
            df = pd.DataFrame(rows)

            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                show_filter = st.selectbox("Show", ["All", "Missing (0/1)", "Visible (1/1)"])
            with fcol2:
                cat_filter = st.multiselect("Category", df["Category"].unique().tolist(),
                                             default=df["Category"].unique().tolist(), key="res_cat")
            with fcol3:
                market_filter = st.multiselect("Market", df["Market"].unique().tolist(),
                                                default=df["Market"].unique().tolist(), key="res_mkt")

            filtered = df[df["Category"].isin(cat_filter) & df["Market"].isin(market_filter)]
            if show_filter == "Missing (0/1)":
                filtered = filtered[filtered["Mentioned"] == "0/1"]
            elif show_filter == "Visible (1/1)":
                filtered = filtered[filtered["Mentioned"] == "1/1"]

            st.dataframe(filtered, use_container_width=True, height=500)

            # Competitor leaderboard
            st.subheader("Competitor Leaderboard")
            if summary["top_competitors"]:
                comp_df = pd.DataFrame(summary["top_competitors"], columns=["Competitor", "Mentions"])
                comp_df["Share"] = (comp_df["Mentions"] / summary["total_prompts"] * 100).round(1).astype(str) + "%"
                st.dataframe(comp_df, use_container_width=True, hide_index=True)

            # Visibility by market
            st.subheader("Visibility by Market")
            if summary["by_market"]:
                mkt_rows = []
                for m, v in summary["by_market"].items():
                    pct = round(v["visible"] / max(v["total"], 1) * 100, 1)
                    mkt_rows.append({"Market": m, "Prompts": v["total"], "Visible": v["visible"], "Rate": f"{pct}%"})
                st.dataframe(pd.DataFrame(mkt_rows), use_container_width=True, hide_index=True)

            # Opportunities
            st.subheader("🎯 Opportunities — Missing but competitors present")
            opps = find_opportunities(results)
            if opps:
                opp_df = pd.DataFrame(opps)
                st.dataframe(opp_df[["prompt", "competitors_present", "brands_count", "market", "priority"]],
                             use_container_width=True, height=300)
                st.caption(f"**{len(opps)} opportunities** — target these with PR articles and content.")
            else:
                st.success("No gaps found — Kolo appears wherever competitors do!")

            # View AI answer
            st.subheader("View AI Answer")
            prompt_options = [r.prompt for r in results]
            selected = st.selectbox("Select prompt", prompt_options, key="view_answer")
            if selected:
                match = next((r for r in results if r.prompt == selected), None)
                if match:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kolo Visible", "✅" if match.kolo_visible else "❌")
                    c2.metric("Brands", match.brands_count)
                    c3.metric("Sources", match.sources_count)
                    if match.brands_list:
                        st.write("**Brands mentioned:**", ", ".join(match.brands_list))
                    st.text_area("AI Answer Preview", match.answer_preview, height=200, disabled=True)

            # Download
            csv_data = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv_data,
                               file_name=f"geo_tracker_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── Tab 4: History ────────────────────────────────────────────
    with tab_history:
        st.subheader("Previous Scans")
        cached = list_cached_results()
        if not cached:
            st.info("No previous scans found. Run a monitor scan first.")
        else:
            hist_df = pd.DataFrame(cached)
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

            selected_file = st.selectbox("Load scan", [c["filename"] for c in cached])
            if st.button("Load") and selected_file:
                loaded = load_results(selected_file)
                st.session_state["geo_results"] = loaded
                st.success(f"Loaded {len(loaded)} results — switch to Results tab")
                st.rerun()
