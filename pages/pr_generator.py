"""Page 6 — PR Generator: Claude-powered article generation, revision, translation, and publication tracking."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from config import BRIEFS
from data_sources import DATA
from llm_client import (
    generate_press_release, revise_press_release,
    translate_press_release, LANG_NAMES,
)


def _get_all_briefs():
    """Return BRIEFS + any gap briefs from GEO audit."""
    all_briefs = list(BRIEFS)
    geo_results = st.session_state.get("geo_audit_results", [])
    if geo_results:
        existing_kws = {b["KW"].lower() for b in BRIEFS}
        not_visible = [r for r in geo_results if not r.get("error") and not r.get("kolo_visible")]
        for i, r in enumerate(not_visible):
            q = r["query"]
            if any(q.lower() in kw for kw in existing_kws):
                continue
            all_briefs.append({
                "#": 100 + i,
                "Title": f"{q.replace('crypto', 'Crypto').title()} — Complete Guide 2026",
                "Lang": "EN", "Market": "Global", "KW": q,
                "Words": 1200, "Priority": "GEO Gap",
            })
    return all_briefs


def page_pr_generator():
    st.title("📝 Stage 6 · PR Generator")
    st.caption("Generate SEO+GEO-optimized press releases, revise with AI, translate, and track publications")

    with st.expander("ℹ️ How PR generation works", expanded=False):
        st.markdown("""
**GEO-optimized article structure** — designed to be cited by AI engines:
- **H2 headers as questions** — matches "People Also Ask" format that AI engines extract
- **Quotable stat paragraphs** — dense facts AI can cite (e.g. "Kolo supports 40+ countries with 0% FX markup")
- **Comparison tables** — Kolo vs competitors in structured format AI engines parse easily
- **FAQ section** — direct Q&A format preferred by ChatGPT, Perplexity, Google AI Overviews

**Flow:** Select brief → Claude generates EN draft → AI revise (add stats, questions) → translate to RU/IT/ES/PL/PT/ID → track publication URLs + UTM params

**Translation:** Claude adapts content per market (not literal translation). RU version emphasizes different features than ID version.
""")

    api_key = st.session_state.get("anthropic_token")

    tab_gen, tab_trans, tab_track = st.tabs(["Generate Draft", "Translate", "Track Publications"])

    # ── Tab 1: Generate Draft ──────────────────────────────────────
    with tab_gen:
        st.subheader("Generate English Draft")
        mode = st.radio("Source", ["Pick from briefs", "Custom brief"], horizontal=True)

        if mode == "Pick from briefs":
            all_briefs = _get_all_briefs()
            brief_titles = [f"{'🔍 GEO GAP — ' if b['#'] >= 100 else ''}#{b['#']} — {b['Title']}" for b in all_briefs]
            sel = st.selectbox("Select brief", brief_titles)
            idx = brief_titles.index(sel)
            brief = all_briefs[idx]
            label = "**🔍 GEO Gap** · " if brief.get("Priority") == "GEO Gap" else ""
            st.markdown(f"{label}**KW:** {brief['KW']} · **Market:** {brief['Market']} · **Words:** ~{brief['Words']}")
        else:
            brief = {
                "Title": st.text_input("Title", placeholder="Best crypto card for..."),
                "KW": st.text_input("Primary keyword", placeholder="crypto card UK"),
                "Market": st.text_input("Target market", value="Global"),
                "Words": st.number_input("Word count", value=1200, step=100),
                "Priority": "Medium",
            }

        col1, col2 = st.columns(2)
        with col1:
            brief["angle"] = st.text_input("Angle (optional)", placeholder="e.g. expat relocation guide")
        with col2:
            brief["hooks"] = st.text_input("Hooks to include (optional)", placeholder="e.g. USDT TRC20, Telegram mini-app")

        if st.button("🚀 Generate EN Draft", type="primary", disabled=not api_key):
            if not api_key:
                st.error("Add your Anthropic API key in the sidebar.")
            else:
                with st.spinner("Generating press release..."):
                    try:
                        draft = generate_press_release(api_key, brief)
                        st.session_state["pr_en_draft"] = draft
                        st.session_state["pr_draft_version"] = st.session_state.get("pr_draft_version", 0) + 1
                        st.session_state["pr_brief"] = brief
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

        if not api_key:
            st.info("Enter your Anthropic API key in the sidebar to enable generation.")

        draft = st.session_state.get("pr_en_draft", "")
        if draft:
            ver = st.session_state.get("pr_draft_version", 0)
            edited = st.text_area("Edit draft", value=draft, height=400, key=f"pr_draft_editor_{ver}")
            st.session_state["pr_en_draft"] = edited
            st.download_button("Download .md", data=edited, file_name="press_release_en.md", mime="text/markdown")

            # AI Revision
            st.divider()
            st.subheader("Revise with AI")
            revision_instructions = st.text_area(
                "What should be changed?",
                placeholder="e.g. Make it shorter, add more data about UAE market, change tone to more formal...",
                height=100, key="revision_instructions",
            )
            if st.button("✏️ Revise Draft", type="primary", disabled=not api_key or not revision_instructions):
                with st.spinner("Revising..."):
                    try:
                        revised = revise_press_release(api_key, edited, revision_instructions)
                        st.session_state["pr_en_draft"] = revised
                        st.session_state["pr_draft_version"] = ver + 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Revision failed: {e}")

    # ── Tab 2: Translate ──────────────────────────────────────────
    with tab_trans:
        st.subheader("Translate to Target Languages")
        source = st.session_state.get("pr_en_draft", "")
        if not source:
            st.warning("Generate an English draft first (Tab 1).")
        else:
            st.text_area("Source (EN)", value=source[:500] + "..." if len(source) > 500 else source, height=150, disabled=True)
            target_langs = st.multiselect(
                "Target languages", options=["ru", "it", "es", "pl", "pt", "id", "ro"],
                default=["ru", "it", "es", "pl", "pt", "id"],
                format_func=lambda x: LANG_NAMES.get(x, x),
            )
            if st.button("🌍 Translate All", type="primary", disabled=not api_key):
                translations = st.session_state.get("pr_translations", {})
                progress = st.progress(0)
                for i, lang in enumerate(target_langs):
                    with st.spinner(f"Translating to {LANG_NAMES.get(lang, lang)}..."):
                        try:
                            translations[lang] = translate_press_release(api_key, source, lang)
                        except Exception as e:
                            st.error(f"Translation to {lang} failed: {e}")
                    progress.progress((i + 1) / len(target_langs))
                st.session_state["pr_translations"] = translations
                st.success(f"Translated to {len(translations)} languages!")

            translations = st.session_state.get("pr_translations", {})
            for lang, text in translations.items():
                with st.expander(f"🌐 {LANG_NAMES.get(lang, lang).upper()}", expanded=False):
                    edited = st.text_area(f"Edit {lang}", value=text, height=400, key=f"trans_{lang}")
                    translations[lang] = edited
                    st.download_button(
                        f"Download {lang}.md", data=edited,
                        file_name=f"press_release_{lang}.md", mime="text/markdown", key=f"dl_{lang}",
                    )
            if translations:
                st.session_state["pr_translations"] = translations

    # ── Tab 3: Track Publications ──────────────────────────────────
    with tab_track:
        st.subheader("Track Published Articles")
        st.caption("Add publication links when articles are paid and live. Data feeds into Monthly Evaluation.")

        if "publications" not in st.session_state:
            rows = []
            for lang_key, sites in DATA["march_outlets"].items():
                for s in sites:
                    if "TBD" in s["name"]:
                        continue
                    rows.append({
                        "Outlet": s["name"], "Lang": lang_key.upper(),
                        "Price ($)": s.get("price") or 0, "Status": "Planned",
                        "Publication URL": "", "Post to X": "",
                    })
            st.session_state["publications"] = pd.DataFrame(rows)

        pub_df = st.data_editor(
            st.session_state["publications"],
            use_container_width=True, num_rows="dynamic",
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    options=["Planned", "Draft Sent", "Paid", "Published", "Rejected"], default="Planned",
                ),
                "Publication URL": st.column_config.LinkColumn("Publication URL"),
                "Post to X": st.column_config.LinkColumn("Post to X"),
            },
            key="pub_editor",
        )
        st.session_state["publications"] = pub_df

        if not pub_df.empty:
            total = len(pub_df)
            published = len(pub_df[pub_df["Status"] == "Published"])
            paid = len(pub_df[pub_df["Status"] == "Paid"])
            total_spent = pub_df[pub_df["Status"].isin(["Paid", "Published"])]["Price ($)"].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Articles", total)
            col2.metric("Published", published)
            col3.metric("Paid (awaiting)", paid)
            col4.metric("Total Spent", f"${total_spent:,.0f}")
