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
        # Tier 1 — Core Revenue Markets (>$400K spend) — refreshed 2026-03-24 from HEX BigQuery (180-day window)
        {"country": "ARE", "flag": "🇦🇪", "tier": 1, "card_users": 265, "card_spend": 3664945, "revenue": 51309, "spend_per_user": 13830, "conversion": 0.92},
        {"country": "PRT", "flag": "🇵🇹", "tier": 1, "card_users": 182, "card_spend": 1131138, "revenue": 15836, "spend_per_user": 6215,  "conversion": 0.94},
        {"country": "ESP", "flag": "🇪🇸", "tier": 1, "card_users": 122, "card_spend": 869183,  "revenue": 12169, "spend_per_user": 7124,  "conversion": 0.89},
        {"country": "LVA", "flag": "🇱🇻", "tier": 1, "card_users": 95,  "card_spend": 757571,  "revenue": 10606, "spend_per_user": 7975,  "conversion": 0.77},
        {"country": "POL", "flag": "🇵🇱", "tier": 1, "card_users": 135, "card_spend": 726400,  "revenue": 10170, "spend_per_user": 5381,  "conversion": 0.92},
        {"country": "IDN", "flag": "🇮🇩", "tier": 1, "card_users": 313, "card_spend": 665980,  "revenue": 9324,  "spend_per_user": 2128,  "conversion": 0.97},
        {"country": "GBR", "flag": "🇬🇧", "tier": 1, "card_users": 72,  "card_spend": 589731,  "revenue": 8256,  "spend_per_user": 8191,  "conversion": 0.74},
        {"country": "ITA", "flag": "🇮🇹", "tier": 1, "card_users": 125, "card_spend": 506249,  "revenue": 7088,  "spend_per_user": 4050,  "conversion": 0.81},
        # Tier 2 — Growth Markets ($100K–$400K spend)
        {"country": "MNE", "flag": "🇲🇪", "tier": 2, "card_users": 146, "card_spend": 381874,  "revenue": 5346,  "spend_per_user": 2616,  "conversion": 0.99},
        {"country": "THA", "flag": "🇹🇭", "tier": 2, "card_users": 130, "card_spend": 351805,  "revenue": 4925,  "spend_per_user": 2706,  "conversion": 0.99},
        {"country": "UZB", "flag": "🇺🇿", "tier": 2, "card_users": 223, "card_spend": 349200,  "revenue": 4889,  "spend_per_user": 1566,  "conversion": 0.70},
        {"country": "MDA", "flag": "🇲🇩", "tier": 2, "card_users": 113, "card_spend": 346118,  "revenue": 4846,  "spend_per_user": 3063,  "conversion": 0.65},
        {"country": "BRA", "flag": "🇧🇷", "tier": 2, "card_users": 183, "card_spend": 325863,  "revenue": 4562,  "spend_per_user": 1781,  "conversion": 0.99},
        {"country": "SRB", "flag": "🇷🇸", "tier": 2, "card_users": 108, "card_spend": 297368,  "revenue": 4163,  "spend_per_user": 2753,  "conversion": 0.99},
        {"country": "POL", "flag": "🇵🇱", "tier": 2, "card_users": 59,  "card_spend": 298532,  "revenue": 4179,  "spend_per_user": 5060,  "conversion": 0.94},  # ru-speaking POL users
        {"country": "SWE", "flag": "🇸🇪", "tier": 2, "card_users": 10,  "card_spend": 242689,  "revenue": 3398,  "spend_per_user": 24269, "conversion": 0.71},
        {"country": "BGD", "flag": "🇧🇩", "tier": 2, "card_users": 201, "card_spend": 241699,  "revenue": 3384,  "spend_per_user": 1202,  "conversion": 0.64},
        {"country": "LTU", "flag": "🇱🇹", "tier": 2, "card_users": 77,  "card_spend": 241170,  "revenue": 3376,  "spend_per_user": 3132,  "conversion": 0.99},
        {"country": "CYP", "flag": "🇨🇾", "tier": 2, "card_users": 63,  "card_spend": 259320,  "revenue": 3630,  "spend_per_user": 4116,  "conversion": 0.85},
        {"country": "CHE", "flag": "🇨🇭", "tier": 2, "card_users": 31,  "card_spend": 224124,  "revenue": 3138,  "spend_per_user": 7230,  "conversion": 0.99},
        {"country": "DEU", "flag": "🇩🇪", "tier": 2, "card_users": 66,  "card_spend": 215119,  "revenue": 3012,  "spend_per_user": 3259,  "conversion": 0.79},
        {"country": "ROU", "flag": "🇷🇴", "tier": 2, "card_users": 43,  "card_spend": 208566,  "revenue": 2920,  "spend_per_user": 4850,  "conversion": 0.66},
        {"country": "BGR", "flag": "🇧🇬", "tier": 2, "card_users": 24,  "card_spend": 207751,  "revenue": 2909,  "spend_per_user": 8656,  "conversion": 0.92},
        {"country": "CZE", "flag": "🇨🇿", "tier": 2, "card_users": 18,  "card_spend": 184789,  "revenue": 2587,  "spend_per_user": 10266, "conversion": 0.67},
        {"country": "URY", "flag": "🇺🇾", "tier": 2, "card_users": 8,   "card_spend": 178403,  "revenue": 2498,  "spend_per_user": 22300, "conversion": 0.99},
        {"country": "GEO", "flag": "🇬🇪", "tier": 2, "card_users": 115, "card_spend": 169074,  "revenue": 2367,  "spend_per_user": 1470,  "conversion": 0.80},
        {"country": "ARM", "flag": "🇦🇲", "tier": 2, "card_users": 17,  "card_spend": 163658,  "revenue": 2291,  "spend_per_user": 9627,  "conversion": 0.99},
        {"country": "MCO", "flag": "🇲🇨", "tier": 2, "card_users": 3,   "card_spend": 161968,  "revenue": 2268,  "spend_per_user": 53989, "conversion": 0.99},
        {"country": "CAN", "flag": "🇨🇦", "tier": 2, "card_users": 67,  "card_spend": 159830,  "revenue": 2238,  "spend_per_user": 2386,  "conversion": 0.46},
        {"country": "KGZ", "flag": "🇰🇬", "tier": 2, "card_users": 20,  "card_spend": 148281,  "revenue": 2076,  "spend_per_user": 7414,  "conversion": 0.99},
        # Tier 3 — Emerging Markets ($30K–$100K spend)
        {"country": "ARG", "flag": "🇦🇷", "tier": 3, "card_users": 6,   "card_spend": 100332,  "revenue": 1405,  "spend_per_user": 16722, "conversion": 0.99},
        {"country": "MKD", "flag": "🇲🇰", "tier": 3, "card_users": 53,  "card_spend": 103395,  "revenue": 1448,  "spend_per_user": 1951,  "conversion": 0.93},
        {"country": "FRA", "flag": "🇫🇷", "tier": 3, "card_users": 70,  "card_spend": 95522,   "revenue": 1337,  "spend_per_user": 1365,  "conversion": 0.99},
        {"country": "EGY", "flag": "🇪🇬", "tier": 3, "card_users": 59,  "card_spend": 82248,   "revenue": 1151,  "spend_per_user": 1394,  "conversion": 0.99},
        # TUR excluded 2026-03-12 — removed from "Can Issue" list
        {"country": "ESP", "flag": "🇪🇸", "tier": 3, "card_users": 13,  "card_spend": 76256,   "revenue": 1068,  "spend_per_user": 5866,  "conversion": 0.99},  # uk-speaking ESP users
        {"country": "THA", "flag": "🇹🇭", "tier": 3, "card_users": 27,  "card_spend": 73530,   "revenue": 1029,  "spend_per_user": 2723,  "conversion": 0.99},  # ru-speaking THA users
    ],
    "languages": [
        # en/ru/uk from HEX lang_clusters — refreshed 2026-03-24
        {"lang": "English",    "code": "en", "card_users": 2254, "total_spend": 8546859, "spend_per_user": 3792},
        {"lang": "Russian",    "code": "ru", "card_users": 872,  "total_spend": 5543327, "spend_per_user": 6357},
        {"lang": "Ukrainian",  "code": "uk", "card_users": 37,   "total_spend": 261177,  "spend_per_user": 7059},
        {"lang": "Italian",    "code": "it", "card_users": 125,  "total_spend": 506249,  "spend_per_user": 4050},
        {"lang": "Spanish",    "code": "es", "card_users": 122,  "total_spend": 869183,  "spend_per_user": 7124},
        {"lang": "Indonesian", "code": "id", "card_users": 313,  "total_spend": 665980,  "spend_per_user": 2128},
        {"lang": "Polish",     "code": "pl", "card_users": 135,  "total_spend": 726400,  "spend_per_user": 5381},
        {"lang": "Portuguese", "code": "pt", "card_users": 183,  "total_spend": 325863,  "spend_per_user": 1781},
    ],
    # Acquisition funnel by market — refreshed 2026-03-24 from HEX "Acquisition Funnel by Market"
    # Shows: registered → onboarded → card_requested → card_active → has_spent (top 20 markets)
    "acquisition_funnel": [
        {"country": "IDN", "lang": "en",   "registered": 474, "onboarded": 436, "card_requested": 355, "card_active": 192, "has_spent": 172},
        {"country": "UZB", "lang": "ru",   "registered": 394, "onboarded": 392, "card_requested": 381, "card_active": 158, "has_spent": 148},
        {"country": "BRA", "lang": "en",   "registered": 383, "onboarded": 369, "card_requested": 357, "card_active": 233, "has_spent": 212},
        {"country": "BGD", "lang": "en",   "registered": 346, "onboarded": 338, "card_requested": 317, "card_active": 125, "has_spent": 146},
        {"country": "ARE", "lang": "en",   "registered": 314, "onboarded": 307, "card_requested": 302, "card_active": 192, "has_spent": 168},
        {"country": "UZB", "lang": "en",   "registered": 262, "onboarded": 258, "card_requested": 257, "card_active": 95,  "has_spent": 85},
        {"country": "MDA", "lang": "ru",   "registered": 240, "onboarded": 234, "card_requested": 226, "card_active": 133, "has_spent": 108},
        {"country": "CAN", "lang": "en",   "registered": 217, "onboarded": 210, "card_requested": 200, "card_active": 70,  "has_spent": 57},
        {"country": "PRT", "lang": "en",   "registered": 207, "onboarded": 202, "card_requested": 199, "card_active": 108, "has_spent": 104},
        {"country": "ITA", "lang": "en",   "registered": 181, "onboarded": 181, "card_requested": 176, "card_active": 130, "has_spent": 124},
        {"country": "THA", "lang": "en",   "registered": 174, "onboarded": 166, "card_requested": 162, "card_active": 110, "has_spent": 103},
        {"country": "GEO", "lang": "en",   "registered": 167, "onboarded": 166, "card_requested": 164, "card_active": 123, "has_spent": 110},
        {"country": "POL", "lang": "en",   "registered": 133, "onboarded": 130, "card_requested": 121, "card_active": 64,  "has_spent": 60},
        {"country": "GBR", "lang": "en",   "registered": 130, "onboarded": 123, "card_requested": 117, "card_active": 64,  "has_spent": 57},
        {"country": "DEU", "lang": "en",   "registered": 128, "onboarded": 122, "card_requested": 112, "card_active": 68,  "has_spent": 60},
    ],
    # Content locale mapping — refreshed 2026-03-24 from HEX "Content Locale Mapping"
    # Shows language mismatches: e.g. Russian speakers in Portugal, Spanish speakers in Spain
    # card_adoption_pct = % of registered users who got a card
    "content_locale_map": [
        {"country": "NGA", "lang": "en",  "users": 2500, "card_users": 4,   "card_adoption_pct": 0.2},
        {"country": "IDN", "lang": "en",  "users": 1793, "card_users": 262, "card_adoption_pct": 14.6},
        {"country": "BGD", "lang": "en",  "users": 916,  "card_users": 144, "card_adoption_pct": 15.7},
        {"country": "BRA", "lang": "en",  "users": 599,  "card_users": 257, "card_adoption_pct": 42.9},
        {"country": "DZA", "lang": "en",  "users": 528,  "card_users": 70,  "card_adoption_pct": 13.3},
        {"country": "UZB", "lang": "ru",  "users": 510,  "card_users": 173, "card_adoption_pct": 33.9},
        {"country": "ARE", "lang": "en",  "users": 408,  "card_users": 206, "card_adoption_pct": 50.5},
        {"country": "PAK", "lang": "en",  "users": 402,  "card_users": 57,  "card_adoption_pct": 14.2},
        {"country": "GHA", "lang": "en",  "users": 366,  "card_users": 53,  "card_adoption_pct": 14.5},
        {"country": "KEN", "lang": "en",  "users": 343,  "card_users": 35,  "card_adoption_pct": 10.2},
        {"country": "UZB", "lang": "en",  "users": 310,  "card_users": 101, "card_adoption_pct": 32.6},
        {"country": "ESP", "lang": "es",  "users": 490,  "card_users": None, "card_adoption_pct": None, "note": "Native Spanish speakers — produce ES content"},
    ],
    # Product feature popularity — refreshed 2026-03-24 from HEX (top 20 by active_cards)
    "product_features": [
        {"country": "IDN", "lang": "en", "active_cards": 4848, "deposit_volume": 818194},
        {"country": "BRA", "lang": "en", "active_cards": 4192, "deposit_volume": 502526},
        {"country": "ARE", "lang": "en", "active_cards": 3600, "deposit_volume": 4979451},
        {"country": "THA", "lang": "en", "active_cards": 2700, "deposit_volume": 307709},
        {"country": "BGD", "lang": "en", "active_cards": 2625, "deposit_volume": 227779},
        {"country": "MDA", "lang": "ru", "active_cards": 2544, "deposit_volume": 790103},
        {"country": "GEO", "lang": "en", "active_cards": 2412, "deposit_volume": 205467},
        {"country": "UZB", "lang": "ru", "active_cards": 2366, "deposit_volume": 466452},
        {"country": "PRT", "lang": "en", "active_cards": 2295, "deposit_volume": 1469318},
        {"country": "ITA", "lang": "en", "active_cards": 2250, "deposit_volume": 520373},
        {"country": "MNE", "lang": "ru", "active_cards": 1802, "deposit_volume": 367943},
        {"country": "UZB", "lang": "en", "active_cards": 1665, "deposit_volume": 587471},
        {"country": "POL", "lang": "en", "active_cards": 1552, "deposit_volume": 828325},
        {"country": "FRA", "lang": "en", "active_cards": 1536, "deposit_volume": None},
        {"country": "CAN", "lang": "en", "active_cards": 1494, "deposit_volume": None},
        {"country": "DEU", "lang": "en", "active_cards": 1445, "deposit_volume": None},
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
