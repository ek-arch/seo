"""Page 3 — Content Plan: unified SEO + GEO + Social calendar with Sheets sync."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from config import PLAN_DEFAULT
from utils.api_keys import get_sheets_creds

try:
    from sheets_client import load_content_plan, save_content_plan
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    def load_content_plan(*a, **kw): return []
    def save_content_plan(*a, **kw): return 0


def _load_plan():
    """Load content plan from Google Sheets (persistent), fall back to default."""
    creds = get_sheets_creds()
    if creds:
        try:
            rows = load_content_plan(creds)
            if rows:
                return rows
        except Exception:
            pass
    return list(PLAN_DEFAULT)


def _save_plan(plan):
    """Save content plan to Google Sheets for persistence."""
    creds = get_sheets_creds()
    if creds:
        try:
            save_content_plan(creds, plan)
        except Exception:
            pass


def page_content_plan():
    st.title("✍️ Stage 3 · Content Plan")
    st.caption("Unified SEO + GEO + Social plan · Edit in place · Track with links")

    # Load plan
    if "content_plan" not in st.session_state:
        st.session_state["content_plan"] = _load_plan()

    plan = st.session_state["content_plan"]
    plan_df = pd.DataFrame(plan)

    # Summary metrics
    total = len(plan_df)
    done = len(plan_df[plan_df["Status"].fillna("") == "Done"]) if "Status" in plan_df.columns else 0
    in_progress = len(plan_df[plan_df["Status"].fillna("") == "In Progress"]) if "Status" in plan_df.columns else 0
    seo_tasks = len(plan_df[plan_df["Type"].str.contains("SEO", na=False)])
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
    _save_plan(updated_plan)

    # Push to Google Sheets
    st.divider()
    gsheets_creds = get_sheets_creds()
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
