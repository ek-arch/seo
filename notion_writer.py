"""
notion_writer.py — Notion REST API writes for Kolo SEO Agent
==============================================================
Creates Content Plan entries, PR draft pages, monthly plan pages,
and logs publication results.  Uses the Notion REST API directly
(not MCP) so the Streamlit app can write without an active Claude session.
"""

from __future__ import annotations

import requests
from datetime import date
from typing import Any, Optional

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Notion page / DB IDs (from project memory)
CONTENT_PLAN_DB = "1d92d3e8-3695-4620-b620-d5ac51700857"
SEO_HUB_PAGE = "31f255c3-552c-811d-920a-c168f0326cba"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _rich_text(text: str) -> list[dict]:
    """Build a Notion rich_text array from a plain string."""
    return [{"type": "text", "text": {"content": text[:2000]}}]


def _select(value: str) -> dict:
    return {"select": {"name": value}}


def _number(value: float | int | None) -> dict:
    return {"number": value}


def _url_prop(value: str | None) -> dict:
    return {"url": value}


def _date_prop(d: date | str | None) -> dict:
    if d is None:
        return {"date": None}
    return {"date": {"start": str(d)}}


def _title_prop(text: str) -> dict:
    return {"title": [{"type": "text", "text": {"content": text[:2000]}}]}


# ── Content Plan DB writes ────────────────────────────────────────────────────

def create_content_plan_entry(
    token: str,
    *,
    title: str,
    lang: str = "EN",
    outlet: str = "",
    month_tag: str = "",
    priority: str = "Medium",
    content_type: str = "Press Release",
    publish_date: Optional[date] = None,
    text_deadline: Optional[date] = None,
    source_draft_url: Optional[str] = None,
    publication_url: Optional[str] = None,
    price_usd: Optional[float] = None,
    projected_roi: Optional[float] = None,
) -> dict:
    """Create a row in the Content Plan Kolo database."""
    properties: dict[str, Any] = {
        "Name": _title_prop(title),
        "Status": _select("Planned"),
        "Priority": _select(priority),
        "Content Type": {"rich_text": _rich_text(content_type)},
    }
    if lang:
        properties["Language"] = _select(lang.upper())
    if outlet:
        properties["Outlet"] = {"rich_text": _rich_text(outlet)}
    if month_tag:
        properties["Month"] = _select(month_tag)
    if publish_date:
        properties["Date"] = _date_prop(publish_date)
    if text_deadline:
        properties["Text Deadline"] = _date_prop(text_deadline)
    if source_draft_url:
        properties["Source Draft URL"] = _url_prop(source_draft_url)
    if publication_url:
        properties["Publication URL"] = _url_prop(publication_url)
    if price_usd is not None:
        properties["Price USD"] = _number(price_usd)
    if projected_roi is not None:
        properties["Projected ROI"] = _number(round(projected_roi, 1))

    payload = {
        "parent": {"database_id": CONTENT_PLAN_DB},
        "properties": properties,
    }
    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def update_content_plan_entry(
    token: str,
    page_id: str,
    **props: Any,
) -> dict:
    """Update an existing Content Plan row.

    Accepted keyword args map to Notion property names:
      status, priority, publication_url, actual_traffic,
      actual_registrations, actual_revenue, roi_status.
    """
    properties: dict[str, Any] = {}

    _map = {
        "status":               lambda v: ("Status", _select(v)),
        "priority":             lambda v: ("Priority", _select(v)),
        "publication_url":      lambda v: ("Publication URL", _url_prop(v)),
        "actual_traffic":       lambda v: ("Actual Traffic", _number(v)),
        "actual_registrations": lambda v: ("Actual Registrations", _number(v)),
        "actual_revenue":       lambda v: ("Actual Revenue", _number(v)),
        "roi_status":           lambda v: ("ROI Status", _select(v)),
        "source_draft_url":     lambda v: ("Source Draft URL", _url_prop(v)),
    }

    for key, val in props.items():
        if key in _map and val is not None:
            prop_name, prop_val = _map[key](val)
            properties[prop_name] = prop_val

    if not properties:
        return {}

    resp = requests.patch(
        f"{NOTION_API}/pages/{page_id}",
        headers=_headers(token),
        json={"properties": properties},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── PR Draft pages ────────────────────────────────────────────────────────────

def create_pr_draft_page(
    token: str,
    *,
    title: str,
    content_markdown: str,
    lang: str = "EN",
    parent_page_id: str = SEO_HUB_PAGE,
) -> dict:
    """Create a Notion page with the press release draft.

    Content is stored as a single paragraph block (Notion API
    limitation: markdown isn't natively supported in create,
    so we store as a code block for readability).
    """
    # Split content into chunks of 2000 chars for Notion blocks
    chunks = [content_markdown[i:i+2000] for i in range(0, len(content_markdown), 2000)]
    children = []
    for chunk in chunks:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}],
            },
        })

    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": _title_prop(f"[{lang.upper()}] {title}"),
        },
        "children": children[:100],  # Notion limit: 100 blocks per request
    }
    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Monthly plan pages ────────────────────────────────────────────────────────

def create_monthly_plan_page(
    token: str,
    *,
    month: str,
    plan_data: dict,
    parent_page_id: str = SEO_HUB_PAGE,
) -> dict:
    """Create a monthly SEO plan page under the Hub.

    plan_data keys: recommended_outlets, content_angles, pillar_budgets, reasoning.
    """
    # Build page content as blocks
    children: list[dict] = []

    # Header
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": _rich_text("Recommended Outlets")},
    })
    for o in plan_data.get("recommended_outlets", []):
        line = f"{o['outlet']} ({o['lang'].upper()}) — ${o.get('price', 0)} — {o.get('rationale', '')}"
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rich_text(line)},
        })

    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": _rich_text("Content Angles")},
    })
    for a in plan_data.get("content_angles", []):
        line = f"[{a.get('lang', 'en').upper()}] {a['title']} — {a.get('market', '')} — KW: {a.get('keyword', '')}"
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rich_text(line)},
        })

    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": _rich_text("Budget Allocation")},
    })
    for pillar, amount in plan_data.get("pillar_budgets", {}).items():
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rich_text(f"{pillar}: ${amount:,.0f}")},
        })

    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": _rich_text("Reasoning")},
    })
    reasoning = plan_data.get("reasoning", "")
    for para in reasoning.split("\n\n"):
        if para.strip():
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": _rich_text(para.strip())},
            })

    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": _title_prop(f"{month} SEO Plan"),
        },
        "children": children[:100],
    }
    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Result logging ────────────────────────────────────────────────────────────

def log_publication_result(
    token: str,
    page_id: str,
    *,
    publication_url: Optional[str] = None,
    actual_traffic: Optional[int] = None,
    actual_registrations: Optional[int] = None,
    actual_revenue: Optional[float] = None,
    roi_status: Optional[str] = None,
) -> dict:
    """Update a Content Plan entry with actual publication results."""
    return update_content_plan_entry(
        token,
        page_id,
        publication_url=publication_url,
        actual_traffic=actual_traffic,
        actual_registrations=actual_registrations,
        actual_revenue=actual_revenue,
        roi_status=roi_status,
        status="Done" if publication_url else None,
    )
