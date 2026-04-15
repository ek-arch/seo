"""Page 8 — Monthly Planner: evaluate last month → Claude recommends next → approve → push to Notion."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import altair as alt

from data_sources import DATA
from publication_roi import LTV_BY_LANG, batch_roi
from llm_client import recommend_monthly_plan
from monthly_cycle import (
    generate_plan_inputs, parse_plan_recommendation, plan_to_notion_entries,
)
from notion_writer import create_content_plan_entry, create_monthly_plan_page


def page_monthly_planner():
    st.title("🗓️ Stage 8 · Monthly Planner")
    st.caption("Full cycle: evaluate last month → recommend next → approve → push to Notion")

    with st.expander("ℹ️ How monthly planning works", expanded=False):
        st.markdown("""
**AI-powered budget allocation:**
1. **Analyze** — Claude reviews last month's evaluation data (ROI by outlet, language, market)
2. **Recommend** — suggests next month's outlet mix, budget split per language pillar, content angles
3. **Review** — you adjust the plan, override allocations, add/remove outlets
4. **Approve & Push** — saves final plan to Notion as content calendar entries

**Logic:** Doubles down on high-ROI outlets/languages, cuts underperformers, suggests new markets based on Hex data trends.
""")

    api_key = st.session_state.get("anthropic_token")
    notion_tok = st.session_state.get("notion_token")

    tab_rec, tab_review, tab_approve = st.tabs(["Analyze + Recommend", "Review Plan", "Approve + Push"])

    # ── Tab 1: Analyze + Recommend ────────────────────────────────
    with tab_rec:
        st.subheader("Generate Next Month's Plan")

        col1, col2 = st.columns(2)
        with col1:
            plan_month = st.selectbox("Planning for", ["2026-04", "2026-05", "2026-06"], key="plan_month_sel")
        with col2:
            budget = st.number_input("Budget ($)", value=2000, step=100, min_value=500, max_value=10000)

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
            with st.spinner("Analysing performance and generating plan..."):
                try:
                    if prev_eval:
                        last_month = generate_plan_inputs(
                            prev_eval, {}, budget,
                            DATA.get("countries", []), DATA.get("languages", []),
                        )
                    else:
                        last_month = {
                            "month": prev, "total_spend": 1717, "total_actual_revenue": 0,
                            "actual_vs_projected": 0, "publications": [],
                            "insights": ["No actual data yet — recommending based on projections."],
                            "top_countries": [], "language_ltv": dict(LTV_BY_LANG), "budget": budget,
                        }

                    available = []
                    from collaborator_outlets import get_outlets
                    for lang_code in ["en", "ru", "it", "es", "pl", "pt", "id"]:
                        try:
                            outlets = get_outlets(lang_code, min_dr=40, max_price=250)
                            for o in outlets[:10]:
                                available.append({
                                    "domain": o[0], "dr": o[1], "price": o[2],
                                    "search_pct": o[3], "traffic": o[4], "score": o[5], "lang": lang_code,
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

    # ── Tab 2: Review Plan ────────────────────────────────────────
    with tab_review:
        plan = st.session_state.get("plan_parsed")
        if not plan:
            st.info("Generate a recommendation first (Tab 1).")
        else:
            st.subheader(f"Recommended Plan: {plan.month}")

            st.markdown("### Outlet Allocations")
            if plan.outlet_allocations:
                alloc_df = pd.DataFrame(plan.outlet_allocations)
                edited_alloc = st.data_editor(alloc_df, use_container_width=True, num_rows="dynamic", key="plan_outlets_editor")
                plan.outlet_allocations = edited_alloc.to_dict("records")

            st.markdown("### Content Angles")
            if plan.content_angles:
                angles_df = pd.DataFrame(plan.content_angles)
                edited_angles = st.data_editor(angles_df, use_container_width=True, num_rows="dynamic", key="plan_angles_editor")
                plan.content_angles = edited_angles.to_dict("records")

            st.markdown("### Budget by Pillar")
            if plan.pillar_budgets:
                budget_df = pd.DataFrame([{"Pillar": k, "Budget ($)": v} for k, v in plan.pillar_budgets.items()])
                chart = alt.Chart(budget_df).mark_arc(innerRadius=50).encode(
                    theta="Budget ($):Q", color="Pillar:N", tooltip=["Pillar", "Budget ($)"],
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

                total = sum(plan.pillar_budgets.values())
                st.metric("Total Planned Spend", f"${total:,.0f}",
                          delta=f"${plan.budget - total:+,.0f} remaining" if total <= plan.budget else f"${total - plan.budget:,.0f} over budget")

            st.markdown("### Projected ROI")
            roi_inputs = [{"outlet": o.get("outlet", ""), "lang": o.get("lang", "en"),
                           "price": o.get("price", 100), "traffic": 20_000, "dr": 50,
                           "has_crypto": True} for o in plan.outlet_allocations]
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

            st.markdown("### Reasoning")
            st.markdown(plan.reasoning)
            st.session_state["plan_parsed"] = plan

    # ── Tab 3: Approve + Push ─────────────────────────────────────
    with tab_approve:
        plan = st.session_state.get("plan_parsed")
        if not plan:
            st.info("Generate and review a plan first.")
        else:
            st.subheader(f"Plan: {plan.month} — Status: {plan.status.upper()}")

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
