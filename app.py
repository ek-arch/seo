"""
app.py — Kolo SEO & GEO Intelligence Agent
============================================
Clean entry point: page config + sidebar + st.navigation().
All page logic lives in pages/*.py. All constants in config.py.
"""
from __future__ import annotations

import streamlit as st
from utils.api_keys import setup_sidebar

# ── Page imports ──────────────────────────────────────────────────────────────
from pages.dashboard import page_dashboard
from pages.kolo_metrics import page_kolo_metrics
from pages.content_plan import page_content_plan
from pages.outlet_matching import page_outlet_matching
from pages.pub_roi import page_publication_roi
from pages.pr_generator import page_pr_generator
from pages.distribution import page_content_distribution
from pages.monthly_eval import page_monthly_eval
from pages.monthly_planner import page_monthly_planner
from pages.pseo import page_programmatic_seo
from pages.geo_tracker import page_geo_tracker

# ── App config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kolo SEO & GEO Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar (API keys, pipeline status) ───────────────────────────────────────
setup_sidebar()

# ── Navigation ────────────────────────────────────────────────────────────────
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
        st.Page(page_programmatic_seo,       title="SEO Factory",      icon="🚀"),
        st.Page(page_geo_tracker,            title="GEO Tracker",      icon="🎯"),
    ],
})
pg.run()
