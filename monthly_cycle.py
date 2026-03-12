"""
monthly_cycle.py — Monthly SEO cycle: evaluate -> plan -> push
===============================================================
Business logic for the monthly review/planning loop.
No UI code — pure data transforms and orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from publication_roi import (
    PublicationROI,
    calculate_publication_roi,
    batch_roi,
    LTV_BY_LANG,
    CONVERSION_RATE_BY_LANG,
)
import ahrefs_hook


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class PublicationResult:
    """Actual result for one publication."""
    outlet: str
    lang: str
    price: float
    # Manual input (Phase 1)
    publication_url: Optional[str] = None
    published_date: Optional[date] = None
    actual_referral_traffic: int = 0
    actual_rankings: dict = field(default_factory=dict)  # {keyword: position}
    actual_registrations: int = 0
    actual_revenue: float = 0.0
    # Ahrefs data (Phase 2 — hook)
    ahrefs_backlinks: Optional[int] = None
    ahrefs_referring_domains: Optional[int] = None
    ahrefs_organic_traffic: Optional[int] = None
    ahrefs_dr_change: Optional[float] = None
    # Projected (from ROI model)
    projected: Optional[PublicationROI] = None
    # Notion tracking
    notion_page_id: Optional[str] = None


@dataclass
class MonthlyEvaluation:
    """Full evaluation of one month's SEO performance."""
    month: str  # "2026-03"
    publications: list[PublicationResult] = field(default_factory=list)
    total_spend: float = 0.0
    total_actual_revenue: float = 0.0
    total_projected_revenue_mid: float = 0.0
    actual_vs_projected_ratio: float = 0.0  # >1 = outperformed
    top_performer: Optional[str] = None
    worst_performer: Optional[str] = None
    insights: list[str] = field(default_factory=list)


@dataclass
class MonthlyPlan:
    """Proposed plan for next month."""
    month: str  # "2026-04"
    budget: float = 0.0
    outlet_allocations: list[dict] = field(default_factory=list)
    content_angles: list[dict] = field(default_factory=list)
    pillar_budgets: dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    status: str = "draft"  # draft | approved | pushed


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_month(
    month: str,
    results: list[PublicationResult],
    projections: Optional[list[PublicationROI]] = None,
) -> MonthlyEvaluation:
    """Compare actual vs projected performance for a month.

    If *projections* is provided, matches them to *results* by
    outlet + lang key and attaches to each PublicationResult.projected.
    """
    # Try to enrich with Ahrefs data
    for r in results:
        ahrefs_hook.enrich_publication_result(r)

    # Match projections to results
    if projections:
        proj_map = {(p.outlet.lower(), p.lang.lower()): p for p in projections}
        for r in results:
            key = (r.outlet.lower(), r.lang.lower())
            if key in proj_map:
                r.projected = proj_map[key]

    total_spend = sum(r.price for r in results)
    total_actual = sum(r.actual_revenue for r in results)
    total_projected = sum(
        r.projected.scenarios[1].revenue if r.projected and len(r.projected.scenarios) > 1 else 0
        for r in results
    )

    ratio = total_actual / total_projected if total_projected > 0 else 0.0

    # Find top / worst
    by_roi = sorted(
        [r for r in results if r.price > 0],
        key=lambda r: r.actual_revenue / r.price if r.price else 0,
        reverse=True,
    )
    top = by_roi[0].outlet if by_roi and by_roi[0].actual_revenue > 0 else None
    worst = by_roi[-1].outlet if len(by_roi) > 1 else None

    # Generate insights
    insights = []
    if ratio > 1.2:
        insights.append(f"Overall performance exceeded projections by {(ratio-1)*100:.0f}%.")
    elif ratio < 0.8 and total_projected > 0:
        insights.append(f"Overall performance was {(1-ratio)*100:.0f}% below projections.")

    # Language performance breakdown
    lang_revenue: dict[str, float] = {}
    lang_spend: dict[str, float] = {}
    for r in results:
        lang_revenue[r.lang] = lang_revenue.get(r.lang, 0) + r.actual_revenue
        lang_spend[r.lang] = lang_spend.get(r.lang, 0) + r.price
    for lang, rev in sorted(lang_revenue.items(), key=lambda x: x[1], reverse=True):
        spend = lang_spend.get(lang, 0)
        if spend > 0:
            insights.append(f"{lang.upper()} pillar: ${rev:,.0f} revenue on ${spend:,.0f} spend ({rev/spend:.1f}x ROI)")

    return MonthlyEvaluation(
        month=month,
        publications=results,
        total_spend=total_spend,
        total_actual_revenue=total_actual,
        total_projected_revenue_mid=total_projected,
        actual_vs_projected_ratio=ratio,
        top_performer=top,
        worst_performer=worst,
        insights=insights,
    )


# ── Plan generation helpers ───────────────────────────────────────────────────

def generate_plan_inputs(
    evaluation: MonthlyEvaluation,
    available_outlets: dict[str, list],
    budget: float,
    country_data: list[dict],
    language_data: list[dict],
) -> dict:
    """Prepare structured input for llm_client.recommend_monthly_plan().

    Returns a dict ready to be passed as *last_month_results*.
    """
    pub_summaries = []
    for r in evaluation.publications:
        s = {
            "outlet": r.outlet,
            "lang": r.lang,
            "price": r.price,
            "actual_revenue": r.actual_revenue,
            "actual_registrations": r.actual_registrations,
            "actual_traffic": r.actual_referral_traffic,
            "roi": round(r.actual_revenue / r.price, 1) if r.price else 0,
            "published": bool(r.publication_url),
        }
        if r.projected and len(r.projected.scenarios) > 1:
            s["projected_revenue_mid"] = r.projected.scenarios[1].revenue
            s["projected_roi_mid"] = r.projected.scenarios[1].roi_x
        pub_summaries.append(s)

    # Top 5 countries by revenue
    top_countries = sorted(country_data, key=lambda c: c.get("revenue", 0), reverse=True)[:5]

    return {
        "month": evaluation.month,
        "total_spend": evaluation.total_spend,
        "total_actual_revenue": evaluation.total_actual_revenue,
        "actual_vs_projected": evaluation.actual_vs_projected_ratio,
        "publications": pub_summaries,
        "insights": evaluation.insights,
        "top_countries": [
            {"country": c.get("country"), "revenue": c.get("revenue"), "users": c.get("users")}
            for c in top_countries
        ],
        "language_ltv": {lang: ltv for lang, ltv in LTV_BY_LANG.items()},
        "budget": budget,
    }


def parse_plan_recommendation(llm_response: dict, month: str, budget: float) -> MonthlyPlan:
    """Parse LLM recommendation JSON into a MonthlyPlan."""
    return MonthlyPlan(
        month=month,
        budget=budget,
        outlet_allocations=llm_response.get("recommended_outlets", []),
        content_angles=llm_response.get("content_angles", []),
        pillar_budgets=llm_response.get("pillar_budgets", {}),
        reasoning=llm_response.get("reasoning", ""),
        status="draft",
    )


def plan_to_notion_entries(plan: MonthlyPlan) -> list[dict]:
    """Convert a MonthlyPlan to dicts ready for notion_writer.create_content_plan_entry()."""
    entries = []
    # Map content angles to outlets where possible
    angle_by_lang: dict[str, list[dict]] = {}
    for a in plan.content_angles:
        lang = a.get("lang", "en").lower()
        angle_by_lang.setdefault(lang, []).append(a)

    for o in plan.outlet_allocations:
        lang = o.get("lang", "en").lower()
        # Find a matching content angle
        angles = angle_by_lang.get(lang, [])
        angle = angles.pop(0) if angles else {}
        entries.append({
            "title": angle.get("title", f"Article for {o['outlet']}"),
            "lang": o.get("lang", "en").upper(),
            "outlet": o.get("outlet", ""),
            "month_tag": plan.month,
            "priority": angle.get("priority", "Medium"),
            "price_usd": o.get("price"),
            "content_type": "Press Release",
        })

    return entries
