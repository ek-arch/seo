"""
data_sources.py — Kolo SEO Intelligence Agent
All data, API clients, and scoring logic in one place.
Swap the stub functions for live calls once API access is unlocked.
"""

import requests
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# STATIC DATA  (source: Hex.tech BigQuery · exchanger2_db_looker · Mar 2026)
# Refreshed: 2026-03-12 — ISR, KAZ & TUR excluded (card issuance no longer available)
# ─────────────────────────────────────────────────────────────────────────────

DATA = {
    "platform": {
        "period": "Oct 10, 2025 – Mar 1, 2026",
        "pre_cashback": {
            "label": "Pre-Cashback (Oct 10 – Dec 9)",
            "active_users": 1744,
            "transactions": 62868,
            "card_spend": 4290000,
            "avg_daily_spend": 70359,
            "avg_daily_tx": 1031,
        },
        "post_cashback": {
            "label": "Post-Cashback (Dec 10 – Mar 1)",
            "active_users": 3319,
            "transactions": 161284,
            "card_spend": 9040000,
            "avg_daily_spend": 110263,
            "avg_daily_tx": 1967,
        },
    },
    "pnl": {
        "months":          ["Dec",   "Jan",    "Feb"],
        "card_spend_fee":  [19040,   29627,    32014],
        "swap_fees":       [29900,   47687,    59276],
        "topup_fees":      [6887,    12569,    14792],
        "issuance_fees":   [8625,    10214,    7994],
        "withdrawal_fees": [1695,    4393,     4125],
        "total_revenue":   [66146,   104490,   118200],
        "cashback_cost":   [-32868,  -54704,   -54013],
        "net_pnl":         [33277,   49786,    64187],
    },
    "countries": [
        # Tier 1 — Core Revenue Markets (>$400K spend) — refreshed 2026-03-11
        {"country": "ARE", "flag": "🇦🇪", "tier": 1, "card_users": 248, "card_spend": 3117294, "revenue": 43642, "spend_per_user": 12570, "conversion": 0.95},
        {"country": "PRT", "flag": "🇵🇹", "tier": 1, "card_users": 175, "card_spend": 948043,  "revenue": 13273, "spend_per_user": 5417,  "conversion": 0.99},
        {"country": "ESP", "flag": "🇪🇸", "tier": 1, "card_users": 107, "card_spend": 675193,  "revenue": 9453,  "spend_per_user": 6310,  "conversion": 0.96},
        {"country": "LVA", "flag": "🇱🇻", "tier": 1, "card_users": 92,  "card_spend": 659058,  "revenue": 9227,  "spend_per_user": 7164,  "conversion": 0.77},
        {"country": "POL", "flag": "🇵🇱", "tier": 1, "card_users": 125, "card_spend": 590026,  "revenue": 8260,  "spend_per_user": 4720,  "conversion": 0.93},
        {"country": "IDN", "flag": "🇮🇩", "tier": 1, "card_users": 287, "card_spend": 565947,  "revenue": 7923,  "spend_per_user": 1972,  "conversion": 0.99},
        {"country": "ITA", "flag": "🇮🇹", "tier": 1, "card_users": 121, "card_spend": 495723,  "revenue": 6940,  "spend_per_user": 4097,  "conversion": 0.83},
        {"country": "GBR", "flag": "🇬🇧", "tier": 1, "card_users": 69,  "card_spend": 468048,  "revenue": 6553,  "spend_per_user": 6783,  "conversion": 0.78},
        # Tier 2 — Growth Markets ($100K–$400K spend)
        {"country": "MNE", "flag": "🇲🇪", "tier": 2, "card_users": 135, "card_spend": 304421,  "revenue": 4262,  "spend_per_user": 2255,  "conversion": 0.99},
        {"country": "UZB", "flag": "🇺🇿", "tier": 2, "card_users": 202, "card_spend": 304245,  "revenue": 4259,  "spend_per_user": 1506,  "conversion": 0.99},
        {"country": "MDA", "flag": "🇲🇩", "tier": 2, "card_users": 99,  "card_spend": 293554,  "revenue": 4110,  "spend_per_user": 2965,  "conversion": 0.99},
        {"country": "BRA", "flag": "🇧🇷", "tier": 2, "card_users": 170, "card_spend": 292477,  "revenue": 4095,  "spend_per_user": 1720,  "conversion": 0.99},
        {"country": "THA", "flag": "🇹🇭", "tier": 2, "card_users": 92,  "card_spend": 264591,  "revenue": 3704,  "spend_per_user": 2876,  "conversion": 0.99},
        {"country": "SRB", "flag": "🇷🇸", "tier": 2, "card_users": 98,  "card_spend": 247175,  "revenue": 3460,  "spend_per_user": 2522,  "conversion": 0.99},
        {"country": "BGD", "flag": "🇧🇩", "tier": 2, "card_users": 192, "card_spend": 222547,  "revenue": 3116,  "spend_per_user": 1159,  "conversion": 0.63},
        {"country": "SWE", "flag": "🇸🇪", "tier": 2, "card_users": 9,   "card_spend": 221131,  "revenue": 3096,  "spend_per_user": 24570, "conversion": 0.69},
        {"country": "LTU", "flag": "🇱🇹", "tier": 2, "card_users": 71,  "card_spend": 209654,  "revenue": 2935,  "spend_per_user": 2952,  "conversion": 0.99},
        {"country": "CHE", "flag": "🇨🇭", "tier": 2, "card_users": 29,  "card_spend": 206387,  "revenue": 2889,  "spend_per_user": 7117,  "conversion": 0.99},
        {"country": "CYP", "flag": "🇨🇾", "tier": 2, "card_users": 60,  "card_spend": 205189,  "revenue": 2873,  "spend_per_user": 3420,  "conversion": 0.88},
        {"country": "BGR", "flag": "🇧🇬", "tier": 2, "card_users": 22,  "card_spend": 175980,  "revenue": 2464,  "spend_per_user": 7999,  "conversion": 0.92},
        {"country": "DEU", "flag": "🇩🇪", "tier": 2, "card_users": 61,  "card_spend": 176437,  "revenue": 2470,  "spend_per_user": 2892,  "conversion": 0.81},
        {"country": "CZE", "flag": "🇨🇿", "tier": 2, "card_users": 16,  "card_spend": 171042,  "revenue": 2395,  "spend_per_user": 10690, "conversion": 0.67},
        {"country": "ROU", "flag": "🇷🇴", "tier": 2, "card_users": 40,  "card_spend": 168468,  "revenue": 2359,  "spend_per_user": 4212,  "conversion": 0.82},
        {"country": "URY", "flag": "🇺🇾", "tier": 2, "card_users": 8,   "card_spend": 159854,  "revenue": 2238,  "spend_per_user": 19982, "conversion": 0.99},
        {"country": "GEO", "flag": "🇬🇪", "tier": 2, "card_users": 109, "card_spend": 154321,  "revenue": 2160,  "spend_per_user": 1416,  "conversion": 0.80},
        {"country": "ARM", "flag": "🇦🇲", "tier": 2, "card_users": 17,  "card_spend": 148569,  "revenue": 2080,  "spend_per_user": 8739,  "conversion": 0.99},
        {"country": "MCO", "flag": "🇲🇨", "tier": 2, "card_users": 2,   "card_spend": 148317,  "revenue": 2076,  "spend_per_user": 74159, "conversion": 0.99},
        {"country": "CAN", "flag": "🇨🇦", "tier": 2, "card_users": 61,  "card_spend": 143770,  "revenue": 2013,  "spend_per_user": 2357,  "conversion": 0.51},
        {"country": "KGZ", "flag": "🇰🇬", "tier": 2, "card_users": 18,  "card_spend": 140942,  "revenue": 1973,  "spend_per_user": 7830,  "conversion": 0.99},
        # Tier 3 — Emerging Markets ($30K–$100K spend)
        {"country": "ARG", "flag": "🇦🇷", "tier": 3, "card_users": 6,   "card_spend": 94152,   "revenue": 1318,  "spend_per_user": 15692, "conversion": 0.99},
        {"country": "MKD", "flag": "🇲🇰", "tier": 3, "card_users": 49,  "card_spend": 90608,   "revenue": 1268,  "spend_per_user": 1849,  "conversion": 0.92},
        {"country": "FRA", "flag": "🇫🇷", "tier": 3, "card_users": 66,  "card_spend": 83152,   "revenue": 1164,  "spend_per_user": 1260,  "conversion": 0.99},
        {"country": "EGY", "flag": "🇪🇬", "tier": 3, "card_users": 55,  "card_spend": 82037,   "revenue": 1148,  "spend_per_user": 1492,  "conversion": 0.99},
        # TUR excluded 2026-03-12 — removed from "Can Issue" list; 32 existing card users, $81K spend (historical)
        {"country": "PAK", "flag": "🇵🇰", "tier": 3, "card_users": 46,  "card_spend": 68406,   "revenue": 958,   "spend_per_user": 1487,  "conversion": 0.90},
    ],
    "languages": [
        # en/ru/uk from Hex lang_clusters (interface language); others derived from country totals — refreshed 2026-03-11
        {"lang": "English",    "code": "en", "card_users": 2178, "total_spend": 7551795, "spend_per_user": 3467},
        {"lang": "Russian",    "code": "ru", "card_users": 785,  "total_spend": 4663177, "spend_per_user": 5940},
        {"lang": "Ukrainian",  "code": "uk", "card_users": 26,   "total_spend": 162945,  "spend_per_user": 6267},
        {"lang": "Italian",    "code": "it", "card_users": 121,  "total_spend": 495723,  "spend_per_user": 4097},
        {"lang": "Spanish",    "code": "es", "card_users": 107,  "total_spend": 675193,  "spend_per_user": 6310},
        {"lang": "Indonesian", "code": "id", "card_users": 287,  "total_spend": 565947,  "spend_per_user": 1972},
        {"lang": "Polish",     "code": "pl", "card_users": 125,  "total_spend": 590026,  "spend_per_user": 4720},
        {"lang": "Portuguese", "code": "pt", "card_users": 170,  "total_spend": 292477,  "spend_per_user": 1720},
    ],
    "cashback_unit_economics": {
        "roi_pct": 18.2, "cac_cashback": 45, "cac_cpa": 12,
        "cac_seo_low": 18, "cac_seo_high": 55,
        "revenue_per_user": 53, "net_per_user": 8.19,
        "spend_multiplier": 65, "total_cashback_users": 3158,
    },
    "seo_forecast": {
        "conservative": {"revenue": 3848,  "cost": 2000, "roi": 1.9},
        "mid":          {"revenue": 7500,  "cost": 2000, "roi": 3.8},
        "optimistic":   {"revenue": 11810, "cost": 2000, "roi": 5.9},
    },
    # Card allowance lists — updated 2026-03-12 from Hex "Card Issuance & Spend Restrictions"
    "card_allowance": {
        "can_issue": {
            "europe": [
                "FRA", "DEU", "GBR", "NLD", "POL", "FIN", "SWE", "ESP", "ITA", "CHE",
                "CZE", "AUT", "ROU", "BGR", "NOR", "PRT", "LTU", "CYP", "LUX", "EST",
                "GRC", "HUN", "SRB", "SVK", "HRV", "SVN", "MLT", "ISL", "AND", "LIE",
                "MCO", "MDA",
            ],
            "asia_pacific": [
                "IDN", "SGP", "JPN", "KOR", "MYS", "THA", "HKG", "AUS", "NZL",
            ],
            "latam_caribbean": [
                "BRA", "ARG", "COL", "MEX", "PER", "CRI", "URY", "CHL",
            ],
            "central_asia_caucasus": [
                "GEO", "AZE", "UZB", "KGZ", "ARM",
            ],
            "middle_east": [
                "BHR", "ARE",
            ],
            "french_overseas": [
                "REU", "GLP", "MTQ", "GUF",
            ],
        },
        "cannot_issue": [
            "RUS", "BLR", "VEN", "CUB", "IRN", "SYR", "PRK", "UKR",
            "TUR", "ISR", "CHN", "IND", "VNM", "NPL", "IRQ", "KAZ",
        ],
        "cannot_spend": [
            "SYR", "IRN", "CUB", "PRK", "RUS", "UKR", "VEN",
        ],
        "note": "The US is NOT a supported market.",
        "updated": "2026-03-12",
    },
    "march_outlets": {
        # notion_score / notion_dims = from Notion Media Outlet Selection Guide + GEO ai_citability
        # notion_score: None = not evaluated; ai_citability: 0-3 (AI engine citation likelihood)
        # Scores now 0-18 (6 dimensions) — thresholds: 15-18=Buy, 11-14=Budget, 7-10=Consider, <7=Skip
        "en": [
            {"name": "businessabc.net",      "price": 100, "dr": 81, "traffic_share": None, "pillar": "English",
             "notion_score": 15, "notion_dims": {"search": 2, "dr": 3, "price_eff": 3, "category": 3, "traffic": 2, "ai_citability": 2},
             "ai_citability": 2},
            {"name": "businessage.com",      "price": 30,  "dr": 64, "traffic_share": 51,   "pillar": "English",
             "notion_score": 13, "notion_dims": {"search": 3, "dr": 2, "price_eff": 3, "category": 3, "traffic": 1, "ai_citability": 1},
             "ai_citability": 1},
            {"name": "thetradable.com",      "price": 100, "dr": 54, "traffic_share": None, "pillar": "English",
             "notion_score": 13, "notion_dims": {"search": 2, "dr": 2, "price_eff": 3, "category": 3, "traffic": 2, "ai_citability": 1},
             "ai_citability": 1},
            {"name": "newspioneer.co.uk",    "price": 65,  "dr": 54, "traffic_share": None, "pillar": "English",
             "notion_score": 11, "notion_dims": {"search": 1, "dr": 2, "price_eff": 3, "category": 3, "traffic": 1, "ai_citability": 1},
             "ai_citability": 1},
            # financial-news.co.uk: in March plan but NOT scored in Notion guide — treat as unconfirmed
            {"name": "financial-news.co.uk", "price": 125, "dr": 54, "traffic_share": None, "pillar": "English",
             "notion_score": None, "notion_dims": None, "notes": "Not in Notion guide — verify before buying",
             "ai_citability": 1},
        ],
        "it": [
            {"name": "viverepesaro.it",       "price": 100,   "dr": 40, "traffic_share": None, "pillar": "Italian",
             "notion_score": 11, "notion_dims": {"search": 2, "dr": 1, "price_eff": 2, "category": 2, "traffic": 3, "ai_citability": 1},
             "ai_citability": 1},
            {"name": "it.kompass.com",        "price": 135,   "dr": 77, "traffic_share": 81,   "pillar": "Italian",
             "notion_score": 15, "notion_dims": {"search": 3, "dr": 3, "price_eff": 3, "category": 1, "traffic": 3, "ai_citability": 2},
             "notes": "PICK — only Italian Finance/DR>65 outlet with >35% search on Collaborator; $35 over sub-budget",
             "ai_citability": 2},
            {"name": "comunicati-stampa.net", "price": 110,   "dr": 58, "traffic_share": 45,   "pillar": "Italian",
             "notion_score": 11, "notion_dims": {"search": 2, "dr": 2, "price_eff": 3, "category": 3, "traffic": 0, "ai_citability": 1},
             "notes": "Backup — Finance+Crypto DR58 but only 2.9k traffic",
             "ai_citability": 1},
        ],
        "es": [
            {"name": "crypto-economy.com",   "price": 130, "dr": None, "traffic_share": None, "pillar": "Spanish",
             "notion_score": 12, "notion_dims": {"search": 2, "dr": 2, "price_eff": 2, "category": 3, "traffic": 2, "ai_citability": 1},
             "ai_citability": 1},
            {"name": "sevillaBN",            "price": 133, "dr": None, "traffic_share": None, "pillar": "Spanish",
             "notion_score": None, "notion_dims": None, "notes": "Not in Notion guide — verify before buying",
             "ai_citability": 0},
        ],
        "pl": [
            {"name": "netbe.pl",             "price": 24,    "dr": 48, "traffic_share": 49,   "pillar": "Polish",
             "notion_score": 12, "notion_dims": {"search": 2, "dr": 1, "price_eff": 3, "category": 3, "traffic": 2, "ai_citability": 1},
             "notes": "In plan. Score updated with real DR48/search49% data from Collaborator",
             "ai_citability": 1},
            {"name": "nenws.com",            "price": 71.51, "dr": 44, "traffic_share": 45,   "pillar": "Polish",
             "notion_score": 11, "notion_dims": {"search": 2, "dr": 1, "price_eff": 3, "category": 3, "traffic": 1, "ai_citability": 1},
             "notes": "NEW PICK — Finance+Crypto, within $54-74 budget",
             "ai_citability": 1},
            {"name": "warsawski.eu",         "price": 67.93, "dr": 55, "traffic_share": 46,   "pillar": "Polish",
             "notion_score": 10, "notion_dims": {"search": 2, "dr": 2, "price_eff": 3, "category": 2, "traffic": 0, "ai_citability": 1},
             "notes": "Backup — DR55 but Media/News, low traffic 1.5k",
             "ai_citability": 1},
        ],
        "pt": [
            {"name": "adital.com.br",        "price": 100, "dr": None, "traffic_share": None, "pillar": "Portuguese",
             "notion_score": 12, "notion_dims": {"search": 2, "dr": 2, "price_eff": 3, "category": 3, "traffic": 1, "ai_citability": 1},
             "ai_citability": 1},
            {"name": "pt.egamersworld.com",  "price": None, "dr": None, "traffic_share": None, "pillar": "Portuguese",
             "notion_score": 15, "notion_dims": {"search": 3, "dr": 3, "price_eff": 2, "category": 2, "traffic": 3, "ai_citability": 2},
             "notes": "Added from Notion guide — price/DR TBD, gaming+crypto audience",
             "ai_citability": 2},
        ],
        "id": [
            {"name": "TBD Indonesian outlet 1", "price": 40, "dr": None, "traffic_share": None, "pillar": "Indonesian",
             "notion_score": None, "notion_dims": None,
             "notes": "ALERT: No qualifying ID crypto outlets on Collaborator (max DR=28). Source externally.",
             "ai_citability": 0},
            {"name": "TBD Indonesian outlet 2", "price": 40, "dr": None, "traffic_share": None, "pillar": "Indonesian",
             "notion_score": None, "notion_dims": None,
             "notes": "ALERT: No qualifying ID crypto outlets on Collaborator (max DR=28). Source externally.",
             "ai_citability": 0},
        ],
        "ru": [
            {"name": "moya-provinciya.com.ua", "price": 5.96,  "dr": 52, "traffic_share": 81, "pillar": "Russian",
             "notion_score": 13, "notion_dims": {"search": 3, "dr": 2, "price_eff": 3, "category": 2, "traffic": 2, "ai_citability": 1},
             "notes": "PICK DR>50 slot — 81% search, 47.5k traffic, exceptional $/DR.",
             "ai_citability": 1},
            {"name": "euroua.com",             "price": 30.00, "dr": 51, "traffic_share": 55, "pillar": "Russian",
             "notion_score": 13, "notion_dims": {"search": 3, "dr": 2, "price_eff": 3, "category": 3, "traffic": 1, "ai_citability": 1},
             "notes": "Alt DR>50 — Finance+Crypto, DR51, 55% search.",
             "ai_citability": 1},
            {"name": "track-package.com.ua",   "price": 3.93,  "dr": 54, "traffic_share": 76, "pillar": "Russian",
             "notion_score": 12, "notion_dims": {"search": 3, "dr": 2, "price_eff": 3, "category": 2, "traffic": 1, "ai_citability": 1},
             "notes": "PICK DR>40 slot — 76% search, 22.6k traffic.",
             "ai_citability": 1},
            {"name": "uaehelper.com",          "price": 50.00, "dr": 53, "traffic_share": 86, "pillar": "Russian",
             "notion_score": 11, "notion_dims": {"search": 3, "dr": 2, "price_eff": 3, "category": 1, "traffic": 1, "ai_citability": 1},
             "notes": "Dubai expat PICK — English-lang UAE site. DR53, 86% search.",
             "ai_citability": 1},
            {"name": "theemiratestimes.com",   "price": 99.00, "dr": 44, "traffic_share": 49, "pillar": "Russian",
             "notion_score": 8,  "notion_dims": {"search": 2, "dr": 1, "price_eff": 2, "category": 2, "traffic": 0, "ai_citability": 1},
             "notes": "Dubai backup — Business/Finance DR44, 49% search",
             "ai_citability": 1},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# NOTION PAGE IDs
# ─────────────────────────────────────────────────────────────────────────────

NOTION_PAGES = {
    # Only the Media Outlet Selection Guide is used — per user instruction 2026-03-10
    "outlet_guide": "31e255c3-552c-8001-9f11-fb11aae7c385",
}

# ─────────────────────────────────────────────────────────────────────────────
# HEX API CLIENT
# Status: POST /project/{id}/run returns 401 — catalog API execution not enabled.
# Workaround: read notebook via browser session (implemented in prior session).
# ─────────────────────────────────────────────────────────────────────────────

HEX_BASE       = "https://app.hex.tech/api/v1"
HEX_PROJECT_ID = "019bd11e-3c00-7004-a038-424c20e9281a"


def run_hex_project(token: str, timeout: int = 120) -> Optional[dict]:
    """Trigger a Hex project run and poll until COMPLETED. Returns run metadata or None."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(f"{HEX_BASE}/project/{HEX_PROJECT_ID}/run", headers=headers, json={})
    if resp.status_code != 200:
        return None  # 401 until catalog API execution is enabled
    run_id = resp.json().get("runId")
    import time
    for _ in range(timeout // 5):
        time.sleep(5)
        poll = requests.get(f"{HEX_BASE}/project/{HEX_PROJECT_ID}/run/{run_id}", headers=headers)
        if poll.json().get("status") == "COMPLETED":
            return poll.json()
    return None


# ─────────────────────────────────────────────────────────────────────────────
# COLLABORATOR.PRO API CLIENT
# Status: /api/public/creator/list requires manual support activation.
# Contact: support@collaborator.pro — "Enable catalog API for account etVxo-..."
# ─────────────────────────────────────────────────────────────────────────────

COLLAB_BASE = "https://collaborator.pro/api/public"


def fetch_collaborator_sites(token: str, category: str = "crypto", max_price: int = 500) -> list:
    """Fetch outlet catalog. Returns [] until API is activated by support."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"category": category, "_price_max": max_price, "sort": "price"}
    resp = requests.get(f"{COLLAB_BASE}/creator/list", headers=headers, params=params)
    if resp.status_code != 200:
        return []
    return resp.json().get("data", [])


def score_outlet_notion(
    search_pct: Optional[float],
    dr: Optional[float],
    price: float,
    category_fit: int,
    monthly_traffic: Optional[int],
    ai_citability: int = 0,
) -> int:
    """Score outlet 0–18 using 6-dimension system (SEO + GEO).

    Dimension 1 – Search traffic %:  >50%=3, 40-50%=2, 35-40%=1, <35%=0
    Dimension 2 – DR:                >65=3,  50-65=2,  40-50=1,  <40=0
    Dimension 3 – Price / DR point:  <$2=3,  $2-4=2,   $4-6=1,   >$6=0
    Dimension 4 – Category fit:      Crypto+Finance=3, Crypto+Other=2, Finance=1, Irrelevant=0
    Dimension 5 – Monthly traffic:   >100K=3, 30-100K=2, 5-30K=1, <5K=0
    Dimension 6 – AI Citability (GEO): Frequently cited=3, Occasionally=2, Rarely=1, Never=0

    Score thresholds: 15-18=Buy immediately, 11-14=Buy if budget, 7-10=Consider, <7=Skip
    Must-Have filters: search>35%, DR>40, Crypto/Finance/Business category, price<$5/DR
    Source: Notion Media Outlet Selection Guide + GEO extension
    """
    sp  = search_pct or 0
    d   = dr or 0
    p   = price or 0
    t   = monthly_traffic or 0
    pdr = (p / d) if d else 999

    s1 = 3 if sp > 50  else (2 if sp > 40 else (1 if sp >= 35 else 0))
    s2 = 3 if d > 65   else (2 if d >= 50 else (1 if d >= 40 else 0))
    s3 = 3 if pdr < 2  else (2 if pdr <= 4 else (1 if pdr <= 6 else 0))
    s4 = min(max(category_fit, 0), 3)
    s5 = 3 if t > 100000 else (2 if t >= 30000 else (1 if t >= 5000 else 0))
    s6 = min(max(ai_citability, 0), 3)

    return s1 + s2 + s3 + s4 + s5 + s6


def outlet_verdict(score: Optional[int]) -> str:
    """Map score (0-18) to buy/skip verdict."""
    if score is None: return "— Unscored"
    if score >= 15:   return "✅ Must buy"
    if score >= 11:   return "🟡 Buy if budget"
    if score >= 7:    return "🟠 Consider only"
    return "🔴 Skip"


def passes_must_haves(site: dict) -> bool:
    """Check Notion guide Must-Have criteria: search>35%, DR>40, price<$5/DR."""
    sp  = site.get("traffic_share") or 0
    d   = site.get("dr") or 0
    p   = site.get("price") or 0
    pdr = (p / d) if d else 999
    return sp >= 35 and d >= 40 and pdr < 5


def can_issue_card(country_code: str) -> bool:
    """Check if Kolo can issue cards to residents of a country (ISO 3166-1 alpha-3)."""
    allowance = DATA.get("card_allowance", {})
    cannot = set(allowance.get("cannot_issue", []))
    if country_code.upper() in cannot:
        return False
    # Check if in any "can_issue" region
    can = allowance.get("can_issue", {})
    all_allowed = set()
    for region_codes in can.values():
        all_allowed.update(region_codes)
    return country_code.upper() in all_allowed


def get_card_allowance_flat() -> list[str]:
    """Return flat list of all country codes where card issuance is allowed."""
    can = DATA.get("card_allowance", {}).get("can_issue", {})
    codes = []
    for region_codes in can.values():
        codes.extend(region_codes)
    return codes
