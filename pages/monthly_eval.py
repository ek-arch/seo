"""Page 7 — Monthly Evaluation: compare actual vs projected ROI for published articles."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt

from data_sources import DATA
from publication_roi import batch_roi as _batch_roi
from monthly_cycle import PublicationResult, evaluate_month
import ahrefs_hook


def page_monthly_eval():
    st.title("📉 Stage 7 · Monthly Evaluation")
    st.caption("Compare actual vs projected ROI for published articles")

    with st.expander("ℹ️ How monthly evaluation works", expanded=False):
        st.markdown("""
**Tracks actual performance vs ROI projections:**
- Input actual data per publication: referral visits, registrations, backlink status
- System compares against the 3-layer ROI model's conservative/mid/optimistic forecasts
- Identifies top and worst performers → feeds into next month's planning
- Ahrefs integration (optional): pull real backlink data and organic keyword gains
""")


    tab_input, tab_report, tab_ahrefs = st.tabs(["Input Results", "Evaluation Report", "Ahrefs Data"])

    # ── Tab 1: Input Results ──────────────────────────────────────
    with tab_input:
        st.subheader("Enter Publication Results")
        eval_month = st.selectbox("Month to evaluate", ["2026-03", "2026-04", "2026-05", "2026-06"], key="eval_month_sel")

        if eval_month == "2026-03":
            default_rows = []
            for lang_key, sites in DATA["march_outlets"].items():
                for s in sites:
                    if "TBD" in s["name"]:
                        continue
                    default_rows.append({
                        "Outlet": s["name"], "Lang": lang_key.upper(),
                        "Price": s.get("price") or 0, "Publication URL": "",
                        "Referral Traffic": 0, "Registrations": 0, "Revenue ($)": 0.0,
                    })
        else:
            default_rows = [{"Outlet": "", "Lang": "EN", "Price": 0, "Publication URL": "",
                            "Referral Traffic": 0, "Registrations": 0, "Revenue ($)": 0.0}]

        if f"eval_data_{eval_month}" not in st.session_state:
            st.session_state[f"eval_data_{eval_month}"] = pd.DataFrame(default_rows)

        edited_df = st.data_editor(
            st.session_state[f"eval_data_{eval_month}"],
            use_container_width=True, num_rows="dynamic", key=f"eval_editor_{eval_month}",
        )
        st.session_state[f"eval_data_{eval_month}"] = edited_df

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Results"):
                results = []
                for _, row in edited_df.iterrows():
                    results.append(PublicationResult(
                        outlet=row.get("Outlet", ""), lang=row.get("Lang", "en").lower(),
                        price=float(row.get("Price", 0)),
                        publication_url=row.get("Publication URL") or None,
                        actual_referral_traffic=int(row.get("Referral Traffic", 0)),
                        actual_registrations=int(row.get("Registrations", 0)),
                        actual_revenue=float(row.get("Revenue ($)", 0)),
                    ))
                st.session_state[f"eval_results_{eval_month}"] = results
                st.success(f"Saved {len(results)} results for {eval_month}")

        with col2:
            if st.button("📥 Import from Track Publications"):
                pubs = st.session_state.get("publications")
                if pubs is not None and not pubs.empty:
                    published = pubs[pubs["Status"].isin(["Paid", "Published"])]
                    if not published.empty:
                        import_rows = [{
                            "Outlet": row["Outlet"], "Lang": row["Lang"],
                            "Price": float(row.get("Price ($)", 0)),
                            "Publication URL": row.get("Publication URL", ""),
                            "Referral Traffic": 0, "Registrations": 0, "Revenue ($)": 0.0,
                        } for _, row in published.iterrows()]
                        st.session_state[f"eval_data_{eval_month}"] = pd.DataFrame(import_rows)
                        st.rerun()
                    else:
                        st.warning("No paid/published articles found in Track Publications.")
                else:
                    st.info("No tracking data yet. Add articles in PR Generator → Track Publications.")

    # ── Tab 2: Evaluation Report ──────────────────────────────────
    with tab_report:
        st.subheader("Actual vs Projected")
        eval_month = st.session_state.get("eval_month_sel", "2026-03")
        results = st.session_state.get(f"eval_results_{eval_month}")

        if not results:
            st.info("Save results in the Input tab first.")
        else:
            outlet_inputs = [{"outlet": r.outlet, "lang": r.lang, "price": r.price,
                              "traffic": 20_000, "dr": 50, "has_crypto": True} for r in results]
            projections = _batch_roi(outlet_inputs) if outlet_inputs else []
            evaluation = evaluate_month(eval_month, results, projections)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Spend", f"${evaluation.total_spend:,.0f}")
            c2.metric("Actual Revenue", f"${evaluation.total_actual_revenue:,.0f}")
            c3.metric("Projected Revenue", f"${evaluation.total_projected_revenue_mid:,.0f}")
            ratio_pct = (evaluation.actual_vs_projected_ratio - 1) * 100
            c4.metric("vs Projected", f"{evaluation.actual_vs_projected_ratio:.1f}x",
                      delta=f"{ratio_pct:+.0f}%" if evaluation.total_projected_revenue_mid > 0 else None)

            rows = []
            for r in evaluation.publications:
                proj_rev = r.projected.scenarios[1].revenue if r.projected and len(r.projected.scenarios) > 1 else 0
                rows.append({
                    "Outlet": r.outlet, "Lang": r.lang.upper(), "Price ($)": r.price,
                    "Actual Revenue ($)": r.actual_revenue, "Projected Revenue ($)": proj_rev,
                    "Actual ROI": f"{r.actual_revenue / r.price:.1f}x" if r.price else "—",
                    "Registrations": r.actual_registrations,
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if rows:
                chart_data = pd.DataFrame(rows)
                chart_data = chart_data[chart_data["Actual Revenue ($)"] > 0]
                if not chart_data.empty:
                    melted = pd.melt(chart_data, id_vars=["Outlet"],
                        value_vars=["Actual Revenue ($)", "Projected Revenue ($)"],
                        var_name="Type", value_name="Revenue")
                    chart = alt.Chart(melted).mark_bar().encode(
                        x=alt.X("Outlet:N", sort="-y"), y="Revenue:Q",
                        color="Type:N", xOffset="Type:N",
                    ).properties(height=350)
                    st.altair_chart(chart, use_container_width=True)

            if evaluation.insights:
                st.subheader("Key Insights")
                for insight in evaluation.insights:
                    st.markdown(f"- {insight}")
            if evaluation.top_performer:
                st.success(f"🏆 Top performer: **{evaluation.top_performer}**")
            if evaluation.worst_performer and evaluation.worst_performer != evaluation.top_performer:
                st.warning(f"⚠️ Worst performer: **{evaluation.worst_performer}**")

            st.session_state[f"eval_report_{eval_month}"] = evaluation

    # ── Tab 3: Ahrefs Data ────────────────────────────────────────
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
