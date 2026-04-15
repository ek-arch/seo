"""
utils/api_keys.py — Sidebar API key management
================================================
Centralizes all API key loading (from Streamlit secrets + sidebar inputs)
and Google Sheets credential handling.
"""
from __future__ import annotations

import json
import streamlit as st


def _try_secret(name: str) -> str:
    """Try to load a secret from Streamlit secrets, return empty string on failure."""
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


def setup_sidebar() -> None:
    """Render the shared sidebar: branding, API keys, pipeline status."""
    with st.sidebar:
        st.image("https://kolo.in/favicon.ico", width=32)
        st.title("Kolo SEO & GEO Agent")
        st.caption("kolo.in · crypto Visa card")
        st.divider()

        # ── API Keys ──────────────────────────────────────────────
        st.subheader("🔑 API Keys")
        hex_token = st.text_input(
            "Hex API token", type="password",
            placeholder="hxtp_...", help="app.hex.tech → Settings → API keys",
        )
        collab_token = st.text_input(
            "Collaborator.pro token", type="password",
            placeholder="etVxo-...", help="collaborator.pro/user/api",
        )
        anthropic_token = st.text_input(
            "Anthropic API key", type="password",
            value=_try_secret("ANTHROPIC_API_KEY"),
            placeholder="sk-ant-...", help="console.anthropic.com → API keys",
        )
        serpapi_key = st.text_input(
            "SerpAPI key", type="password",
            value=_try_secret("SERPAPI_KEY"),
            placeholder="...", help="serpapi.com → free 100 searches/month",
        )
        perplexity_key = st.text_input(
            "Perplexity API key", type="password",
            value=_try_secret("PERPLEXITY_KEY"),
            placeholder="pplx-...", help="perplexity.ai/settings/api · ~$0.005/query",
        )

        # Google Sheets creds from secrets
        gsheets_creds = ""
        try:
            gsheets_creds = json.dumps(dict(st.secrets["gsheets"]))
        except Exception:
            pass

        # Store all keys in session state
        key_map = {
            "hex_token": hex_token,
            "collab_token": collab_token,
            "anthropic_token": anthropic_token,
            "serpapi_key": serpapi_key,
            "perplexity_key": perplexity_key,
            "gsheets_json": gsheets_creds,
        }
        for k, v in key_map.items():
            if v:
                st.session_state[k] = v

        # ── Pipeline Status ───────────────────────────────────────
        st.divider()
        st.subheader("📋 Pipeline")
        stages = [
            ("Stage 2 · Kolo Metrics", "✅"),
            ("Stage 3 · Content Plan", "✅"),
            ("Stage 4 · Outlet Match", "✅"),
            ("Stage 5 · Pub ROI", "✅"),
            ("Stage 6 · PR Generator", "🆕"),
            ("Stage 7 · Distribution", "🆕"),
            ("Stage 8b · Keyword Intel", "🆕"),
            ("Stage 9 · Monthly Eval", "🆕"),
            ("Stage 10 · Monthly Planner", "🆕"),
        ]
        for name, status in stages:
            st.markdown(f"{status} {name}")

        st.divider()
        st.caption(
            "Source: Hex BigQuery · exchanger2_db_looker\n"
            "180-day window · F&F excluded · Refreshed 2026-03-24"
        )


def get_api_key(name: str) -> str:
    """Get an API key from session state. Returns empty string if not set."""
    return st.session_state.get(name, "")


def get_sheets_creds() -> str:
    """Get Google Sheets credentials from session state or Streamlit secrets."""
    creds = st.session_state.get("gsheets_json", "")
    if creds:
        return creds
    try:
        return json.dumps(dict(st.secrets["gsheets"]))
    except Exception:
        return ""
