"""
publication_roi.py — Per-publication ROI model for Kolo SEO & GEO agent
=======================================================================
Three-layer model:
  1. Direct referral traffic  (UTM-trackable)
  2. SEO compound traffic     (backlink → ranking improvement, 90-day window)
  3. GEO / AI citation traffic (AI engines citing the outlet → additional visits)
  4. Revenue = total visits × conversion rate × LTV

LTV figures from Hex BigQuery (Oct 2025 – Mar 2026 cohort).
Conversion rates calibrated to match observed SEO CAC range $18–55.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── LTV by language pillar ────────────────────────────────────────────────────
# Source: Hex BigQuery, language-level cohort analysis
LTV_BY_LANG: dict[str, float] = {
    "en": 3_502,
    "ru": 6_975,   # 2× English — highest-value cohort
    "it": 2_850,   # proxy: ITA market revenue / estimated user count
    "es": 3_100,   # proxy: ESP market blended
    "pl": 2_400,   # POL +59% growth, newer cohort → lower LTV for now
    "pt": 1_601,   # confirmed BRA $1,601/user from Hex
    "id": 900,     # emerging market, lower purchasing power
    "ro": 2_200,   # ROU +183% growth; proxy estimate pending Hex data
}

# ── LTV by market-language combo (where Hex has explicit data) ────────────────
LTV_BY_MARKET_LANG: dict[tuple[str, str], float] = {
    ("ARE", "ru"): 21_640,  # Dubai Russian expat — #1 ROI target
    ("ARE", "en"):  9_203,
    ("ESP", "ru"):  7_302,
    ("ESP", "en"):  4_233,
    ("GBR", "en"):  4_800,  # $1.67M / ~350 users estimate
    ("ISR", "ru"): 53_000,  # Hidden whale: $906K / 17 users
    ("KAZ", "ru"):  8_597,  # $327K, 83% conversion
}

# ── Conversion rates by language ──────────────────────────────────────────────
# Calibrated so: median publication cost / (median_traffic × CTR × CR) ≈ $18–55 CAC
# i.e. $100 publication, 1000 referral visits → ~3–5 registrations → CAC $20–33
CONVERSION_RATE_BY_LANG: dict[str, float] = {
    "en": 0.0040,   # 0.40 %
    "ru": 0.0055,   # 0.55 % — higher intent, crypto-native audience
    "it": 0.0042,
    "es": 0.0042,
    "pl": 0.0048,
    "pt": 0.0035,
    "id": 0.0025,
    "ro": 0.0045,   # ROU — MiCA adopted, growing crypto adoption
}

# ── CTR from organic position ─────────────────────────────────────────────────
# Source: Sistrix 2024 CTR study (average across all queries)
POSITION_CTR: dict[int, float] = {
    1: 0.285, 2: 0.153, 3: 0.110, 4: 0.082, 5: 0.064,
    6: 0.051, 7: 0.041, 8: 0.034, 9: 0.028, 10: 0.022,
    11: 0.015, 12: 0.013, 13: 0.011, 14: 0.010, 15: 0.009,
    16: 0.008, 17: 0.007, 18: 0.006, 19: 0.005, 20: 0.004,
}


def _ctr(pos: float) -> float:
    """Interpolated CTR for a non-integer ranking position."""
    pos = max(1.0, min(pos, 20.0))
    lo, hi = int(pos), min(int(pos) + 1, 20)
    frac = pos - lo
    return POSITION_CTR[lo] * (1 - frac) + POSITION_CTR[hi] * frac


# ── DR → ranking positions gained ────────────────────────────────────────────
# Conservative model: one quality backlink moves the needle modestly.
# Calibrated against Ahrefs case studies for DR 40–80 range.
def _positions_gained(dr: int, category_fit: bool = True) -> float:
    """Estimated position improvement from one backlink of given DR."""
    if dr >= 75:   base = 3.0
    elif dr >= 60: base = 2.0
    elif dr >= 50: base = 1.5
    elif dr >= 40: base = 1.0
    else:          base = 0.5
    return base * (1.3 if category_fit else 1.0)  # crypto/finance fit bonus


# ── Core model ────────────────────────────────────────────────────────────────

@dataclass
class PublicationScenario:
    label: str
    referral_visits: float
    seo_visits_90d: float
    ai_visits_90d: float   # GEO: AI citation traffic
    registrations: float
    revenue: float
    roi_x: float          # revenue / price
    payback_days: int
    cac: float            # price / registrations


@dataclass
class PublicationROI:
    outlet: str
    lang: str
    price: float
    outlet_traffic: int
    outlet_dr: int
    keyword_volume: int
    current_rank: int
    scenarios: dict[str, PublicationScenario] = field(default_factory=dict)
    ltv: float = 0.0
    cr: float = 0.0

    def best(self) -> PublicationScenario:
        return self.scenarios["optimistic"]

    def mid(self) -> PublicationScenario:
        return self.scenarios["mid"]

    def low(self) -> PublicationScenario:
        return self.scenarios["conservative"]


def calculate_publication_roi(
    outlet: str,
    lang: str,
    price: float,
    outlet_traffic: int,
    outlet_dr: int,
    *,
    keyword_volume: int = 0,
    current_rank: int = 20,
    article_ctr_pct: float = 0.20,       # % of monthly traffic that sees article
    referral_to_site_pct: float = 1.5,   # % of article readers who click through
    seo_months: int = 3,                  # window for SEO compound effect
    market: Optional[str] = None,         # override LTV with market-lang combo
    has_crypto_category: bool = True,
    ai_citability: int = 1,              # GEO: 0-3 AI citation score
    ai_share_of_search: float = 0.08,    # GEO: % of search now via AI engines
) -> PublicationROI:
    """
    Calculate conservative / mid / optimistic ROI for one publication.

    Parameters
    ----------
    outlet              : domain name (for display)
    lang                : language code (en/ru/it/es/pl/pt/id)
    price               : publication cost in USD
    outlet_traffic      : outlet's monthly organic traffic (Ahrefs)
    outlet_dr           : outlet's Domain Rating
    keyword_volume      : monthly search volume for target keyword (0 = unknown)
    current_rank        : kolo.in's current ranking for target keyword (default 20)
    article_ctr_pct     : % of outlet's monthly visitors who see the article
    referral_to_site_pct: % of article readers who click through to kolo.in
    seo_months          : compound SEO window in months
    market              : ISO-3166 country code for market-specific LTV override
    has_crypto_category : whether outlet has crypto/finance category
    ai_citability       : GEO score 0-3 (how likely AI engines cite this outlet)
    ai_share_of_search  : fraction of search traffic now going through AI engines
    """
    # LTV — prefer market-lang combo if available
    if market:
        ltv = LTV_BY_MARKET_LANG.get((market.upper(), lang.lower()),
                                      LTV_BY_LANG.get(lang, 3_500))
    else:
        ltv = LTV_BY_LANG.get(lang, 3_500)

    cr = CONVERSION_RATE_BY_LANG.get(lang, 0.004)

    # ── Layer 1: Direct referral traffic ─────────────────────────────────────
    article_readers = outlet_traffic * (article_ctr_pct / 100)
    referral_base = article_readers * (referral_to_site_pct / 100)

    # ── Layer 2: SEO compound traffic (90-day / seo_months) ──────────────────
    if keyword_volume > 0:
        pos_gain = _positions_gained(outlet_dr, has_crypto_category)
        new_rank = max(1.0, current_rank - pos_gain)
        monthly_delta = keyword_volume * (_ctr(new_rank) - _ctr(current_rank))
        seo_base_monthly = max(0.0, monthly_delta)
    else:
        # Fallback: DR-normalised proxy (no keyword data)
        dr_factor = min(outlet_dr / 55.0, 2.0)
        seo_base_monthly = outlet_traffic * 0.0003 * dr_factor

    seo_base_90d = seo_base_monthly * seo_months

    # ── Layer 3: AI citation traffic (GEO) ────────────────────────────────────
    # Model: AI engines (ChatGPT, Perplexity, Google AI Overviews) cite
    # high-authority outlets. Probability scales with DR and ai_citability score.
    ai_cite_prob = min(ai_citability / 3.0, 1.0) * min(outlet_dr / 80.0, 1.0) * 0.15
    if keyword_volume > 0:
        ai_base_monthly = keyword_volume * ai_share_of_search * ai_cite_prob
    else:
        ai_base_monthly = outlet_traffic * 0.0001 * ai_citability
    ai_base_90d = ai_base_monthly * seo_months

    # ── Scenarios ─────────────────────────────────────────────────────────────
    scenarios: dict[str, PublicationScenario] = {}
    for label, (r_mult, s_mult, a_mult, cr_mult) in {
        "conservative": (0.50, 0.40, 0.30, 0.75),
        "mid":          (1.00, 1.00, 1.00, 1.00),
        "optimistic":   (1.60, 2.00, 2.50, 1.30),
    }.items():
        ref_v   = referral_base * r_mult
        seo_v   = seo_base_90d  * s_mult
        ai_v    = ai_base_90d   * a_mult
        total_v = ref_v + seo_v + ai_v
        regs    = total_v * cr * cr_mult
        rev     = regs * ltv
        roi_x   = rev / price if price > 0 else 0.0
        payback = int(price / (rev / 90)) if rev > 0 else 9_999
        cac     = price / regs if regs > 0 else 9_999

        scenarios[label] = PublicationScenario(
            label=label,
            referral_visits=round(ref_v),
            seo_visits_90d=round(seo_v),
            ai_visits_90d=round(ai_v),
            registrations=round(regs, 1),
            revenue=round(rev),
            roi_x=round(roi_x, 1),
            payback_days=payback,
            cac=round(cac, 1),
        )

    return PublicationROI(
        outlet=outlet,
        lang=lang,
        price=price,
        outlet_traffic=outlet_traffic,
        outlet_dr=outlet_dr,
        keyword_volume=keyword_volume,
        current_rank=current_rank,
        scenarios=scenarios,
        ltv=ltv,
        cr=cr,
    )


# ── Batch helper ──────────────────────────────────────────────────────────────

def batch_roi(
    outlet_list: list[dict],
    article_ctr_pct: float = 0.20,
    referral_to_site_pct: float = 1.5,
    seo_months: int = 3,
    ai_share_of_search: float = 0.08,
) -> list[PublicationROI]:
    """
    Calculate ROI for a list of outlet dicts.

    Each dict must have: outlet, lang, price, traffic, dr
    Optional: keyword_volume, current_rank, market, has_crypto, ai_citability
    """
    results = []
    for o in outlet_list:
        results.append(calculate_publication_roi(
            outlet=o["outlet"],
            lang=o["lang"],
            price=float(o["price"] or 0),
            outlet_traffic=int(o.get("traffic", 50_000)),
            outlet_dr=int(o.get("dr", 50)),
            keyword_volume=int(o.get("keyword_volume", 0)),
            current_rank=int(o.get("current_rank", 20)),
            article_ctr_pct=article_ctr_pct,
            referral_to_site_pct=referral_to_site_pct,
            seo_months=seo_months,
            market=o.get("market"),
            has_crypto_category=bool(o.get("has_crypto", True)),
            ai_citability=int(o.get("ai_citability", 1)),
            ai_share_of_search=ai_share_of_search,
        ))
    results.sort(key=lambda r: r.mid().roi_x, reverse=True)
    return results


# ── ROI label ─────────────────────────────────────────────────────────────────

def roi_label(roi_x: float) -> str:
    if roi_x >= 20:  return "🚀 Exceptional"
    if roi_x >= 10:  return "🏆 Excellent"
    if roi_x >= 5:   return "⭐ Strong"
    if roi_x >= 2:   return "✅ Good"
    if roi_x >= 1:   return "🟡 Break-even"
    return "🔴 Loss"
