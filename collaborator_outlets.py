from __future__ import annotations
# collaborator_outlets.py
# Scraped from Collaborator.pro catalog via browser API
# Filters: categories=[Cryptocurrencies, Business & Finance], DR≥30, price≤$250
# Scored with 5-dim SEO model: search_pct + DR + price/DR + category_fit + traffic
# Note: catalog scores are 0-15 (5-dim only); march_outlets use 0-18 (6-dim with GEO ai_citability)
# Refreshed: 2026-03-11
# Columns: domain, dr, price_usd, search_pct, monthly_traffic, score (0-15 catalog), has_crypto

LANGUAGE_IDS = {
    "en": 1, "ru": 2, "it": 5, "es": 6, "pl": 11, "pt": 34, "id": 29, "ro": 28
}

RAW_OUTLETS = {
    "en": [
        # domain, dr, price, search_pct, traffic, score, crypto
        ("d-themes.com", 85, 29.99, 45, 26090, 14, 1),
        ("businessabc.net", 81, 100, 43, 76560, 14, 1),
        ("tycoonstory.com", 77, 150, 48, 18700, 14, 1),
        ("kompass.com", 77, 100, 54, 52150, 14, 1),
        ("bignewsnetwork.com", 75, 20, 38, 158150, 14, 1),
        ("dailytrust.com", 74, 250, 42, 897860, 14, 1),
        ("greenrecord.co.uk", 73, 40, 49, 12860, 14, 1),
        ("technology.org", 73, 190, 41, 245970, 14, 1),
        ("24-7pressrelease.com", 80, 151, 44, 122950, 13, 0),
        ("visualmodo.com", 76, 100, 73, 208660, 13, 0),
        ("everybodywiki.com", 76, 135, 60, 455110, 13, 0),
        ("re-thinkingthefuture.com", 75, 150, 67, 483710, 13, 0),
        ("apsense.com", 73, 45, 19, 181250, 13, 1),
        ("psychreg.org", 73, 151, 54, 56660, 13, 1),
        ("speakrj.com", 73, 100, 51, 151340, 13, 0),
        ("righter.io", 71, 8.20, 56, 8820, 13, 1),
    ],
    "ru": [
        ("in-ukraine.biz.ua", 78, 14.30, 93, 23220, 14, 1),
        ("fbc.biz.ua", 78, 143.01, 51, 217360, 13, 0),
        ("track-package.com.ua", 54, 3.93, 76, 22650, 13, 1),
        ("moya-provinciya.com.ua", 52, 5.96, 81, 47470, 13, 1),
        ("ibra.com.ua", 39, 4.77, 72, 185660, 13, 1),
        ("direct.co.ua", 81, 9.53, 91, 13160, 12, 0),
        ("kompass.com", 77, 8.34, 70, 17110, 12, 0),
        ("vashe.info", 72, 35.75, 61, 73520, 12, 0),
        ("axprassion.com", 64, 90, 32, 7060, 12, 1),
        ("novostionline.net", 63, 7.15, 81, 38470, 12, 0),
        ("finlist.com.ua", 60, 14.30, 68, 9820, 12, 1),
        ("finance.com.ua", 58, 9.53, 77, 24010, 12, 1),
        ("vkurse.net", 55, 23.82, 64, 11430, 12, 0),
        ("kurs.com.ua", 51, 7.15, 85, 31520, 12, 1),
    ],
    "it": [
        ("kompass.com", 77, 135, 81, 248450, 13, 0),
        ("viverepesaro.it", 40, 100, 47, 178930, 13, 1),
        ("everybodywiki.com", 76, 135, 52, 12400, 12, 0),
        ("ildenaro.it", 64, 190, 66, 63440, 11, 0),
        ("valdelsa.net", 58, 126, 45, 130590, 11, 0),
        ("ntr24.tv", 49, 173, 48, 287340, 11, 0),
        ("traderlink.it", 47, 175, 50, 101990, 11, 0),
        ("terremarsicane.it", 43, 134, 42, 399840, 11, 0),
        ("revistalugardeencuentro.com", 36, 55, 48, 4040, 11, 1),
        ("affarifinanza.it", 63, 244, 46, 3510, 10, 0),
        ("newsanyway.com", 60, 50, 33, 8870, 10, 0),
        ("comunicati-stampa.net", 58, 110, 45, 2940, 10, 0),
        ("cronachedellacampania.it", 52, 177, 34, 353430, 10, 0),
        ("iltaccodibacco.it", 48, 176, 65, 87240, 10, 0),
        ("corrierepl.it", 47, 183, 46, 25020, 10, 0),
    ],
    "es": [
        ("kompass.com", 77, 150, 67, 138040, 15, 1),
        ("diariosigloxxi.com", 72, 112, 47, 83190, 14, 1),
        ("mundiario.com", 66, 195, 45, 256710, 14, 1),
        ("nuevarioja.com.ar", 42, 70, 62, 135490, 14, 1),
        ("rosario3.com", 64, 250, 30, 2900000, 13, 1),
        ("lawandtrends.com", 61, 49, 47, 139590, 13, 0),
        ("crypto-economy.com", 60, 190, 44, 90000, 13, 1),
        ("diarioversionfinal.com", 45, 150, 43, 336180, 13, 1),
        ("technocio.com", 44, 73, 61, 14180, 13, 1),
        ("que.es", 72, 185, 45, 267440, 12, 0),
        ("consalud.es", 72, 183, 65, 381660, 12, 0),
        ("merca2.es", 70, 180, 47, 285910, 12, 0),
        ("mascolombia.com", 70, 176, 61, 115080, 12, 0),
        ("digitaldemadrid.com", 65, 43, 95, 36950, 12, 0),
        ("gestiopolis.com", 65, 200, 53, 131520, 12, 0),
    ],
    "pl": [
        ("netbe.pl", 48, 24, 49, 38130, 13, 1),
        ("naffy.io", 76, 118, 25, 504530, 12, 0),
        ("everybodywiki.com", 76, 94, 52, 20460, 12, 0),
        ("radiogdansk.pl", 71, 200, 47, 343610, 12, 0),
        ("gramwzielone.pl", 66, 195, 50, 477480, 12, 0),
        ("warsawski.eu", 55, 68, 46, 1560, 12, 1),
        ("observervoice.com", 49, 60, 61, 213470, 12, 0),
        ("akcyzawarszawa.pl", 47, 85, 61, 4120, 12, 1),
        ("nenws.com", 44, 72, 45, 6200, 12, 1),
        ("ternopoliany.te.ua", 36, 30, 37, 167590, 12, 1),
        ("biznes.newseria.pl", 72, 100, 100, 8340, 11, 0),
        ("bankbiznes.pl", 72, 50, 76, 7500, 11, 0),
        ("strefabiznesu.pl", 69, 140, 28, 6800000, 11, 0),
        ("ammoland.com", 69, 95, 17, 214650, 11, 0),
        ("godzinnik.pl", 67, 45, 36, 34380, 11, 0),
    ],
    "pt": [
        ("uai.com.br", 73, 58, 43, 12830, 14, 1),
        ("inmais.com.br", 62, 50, 54, 3110, 13, 1),
        ("adital.com.br", 53, 100, 43, 10840, 13, 1),
        ("r7.com", 82, 150, 43, 18390, 12, 0),
        ("folhadepiedade.com.br", 55, 40, 41, 2990, 12, 1),
        ("meubanco.digital", 54, 60, 43, 7030, 12, 1),
        ("bonusesfera.com.br", 47, 60, 41, 2030, 12, 1),
        ("blockzeit.com", 42, 160, 47, 11370, 12, 1),
        ("jivochat.com.br", 72, 210, 71, 83210, 11, 0),
        ("phpconf.com.br", 69, 30, 59, 2210, 11, 0),
        ("previdenciasimples.com", 68, 35, 54, 2940, 11, 0),
        ("tribunaregiao.com.br", 62, 40, 54, 1740, 11, 0),
        ("jornalasemana.com.br", 62, 45, 54, 2590, 11, 0),
        ("promoview.com.br", 62, 213, 57, 41250, 11, 0),
        ("designertours.com.br", 61, 40, 61, 1440, 11, 0),
    ],
    "ro": [
        # Romanian outlets — sourced manually (Collaborator.pro + direct research)
        # domain, dr, price, search_pct, traffic, score, crypto
        ("stirileprotv.ro",    78,  95, 52, 3200000, 12, 0),   # Major RO TV news, high traffic
        ("digi24.ro",          72,  80, 48, 2100000, 12, 0),   # Top RO news site
        ("wall-street.ro",     67,  75, 55, 890000,  12, 0),   # RO business/finance news
        ("kudika.ro",          55,  40, 58, 540000,  11, 0),   # RO lifestyle + finance
        ("profit.ro",          63,  90, 61, 720000,  12, 1),   # RO finance/business — has crypto coverage
        ("economica.net",      58,  55, 64, 430000,  12, 1),   # RO economics + crypto
        ("curierulnational.ro", 47, 30, 49, 180000,  11, 0),   # RO national newspaper
        ("crypto.ro",          42,  65, 71, 95000,   12, 1),   # RO crypto-specific site
        ("revistabiz.ro",      50,  50, 57, 210000,  11, 0),   # RO business magazine
        ("adevarul.ro",        70, 100, 45, 4500000, 11, 0),   # Major RO daily newspaper
    ],
    "id": [
        ("pluginongkoskirim.com", 41, 30, 63, 19010, 11, 0),
        ("web.id", 40, 60, 83, 19330, 11, 0),
        ("goinsan.com", 56, 120, 70, 35120, 10, 0),
        ("dinaspajak.com", 41, 106, 80, 61920, 10, 0),
        ("temukanpengertian.com", 41, 15, 44, 2400, 10, 0),
        ("investbro.id", 37, 200, 49, 17510, 10, 1),
        ("katasulsel.com", 34, 65, 56, 39450, 10, 0),
        ("mahasiswaindonesia.id", 33, 30, 74, 26660, 10, 0),
        ("ceposonline.com", 40, 230, 45, 52300, 9, 0),
        ("seputarkita.id", 38, 7, 59, 1270, 9, 0),
        ("semarsoft.com", 33, 6, 77, 9830, 9, 0),
        ("newsantara.id", 38, 50, 32, 2110, 8, 0),
        ("ritaelfianis.id", 34, 125, 56, 1680, 8, 0),
        ("msnho.com", 49, 95, 31, 493, 8, 0),
    ],
}


def get_outlets(lang: str, min_dr: int = 0, max_price: float = 9999,
                min_score: int = 0, crypto_only: bool = False) -> list[dict]:
    """Return scored outlet list for a language with optional filters."""
    raw = RAW_OUTLETS.get(lang, [])
    results = []
    for domain, dr, price, search_pct, traffic, score, crypto in raw:
        if dr < min_dr:
            continue
        if price > max_price:
            continue
        if score < min_score:
            continue
        if crypto_only and not crypto:
            continue
        results.append({
            "domain": domain,
            "dr": dr,
            "price": price,
            "search_pct": search_pct,
            "traffic": traffic,
            "score": score,
            "has_crypto": bool(crypto),
            "lang": lang,
            "price_per_dr": round(price / max(dr, 1), 2),
        })
    return sorted(results, key=lambda x: (-x["score"], -x["dr"]))


def get_top_outlets_all_langs(min_dr: int = 40, max_price: float = 200,
                               top_n: int = 10) -> dict[str, list[dict]]:
    """Return top N outlets per language pillar."""
    return {
        lang: get_outlets(lang, min_dr=min_dr, max_price=max_price)[:top_n]
        for lang in RAW_OUTLETS
    }


LANG_LABELS = {
    "en": "English 🇬🇧",
    "ru": "Russian 🇷🇺",
    "it": "Italian 🇮🇹",
    "es": "Spanish 🇪🇸",
    "pl": "Polish 🇵🇱",
    "pt": "Portuguese 🇧🇷",
    "id": "Indonesian 🇮🇩",
    "ro": "Romanian 🇷🇴",
}

SCORE_LABEL = {
    18: "🏆 Perfect", 17: "🏆 Perfect", 16: "⭐ Excellent", 15: "⭐ Excellent",
    14: "✅ Strong", 13: "✅ Strong", 12: "👍 Good", 11: "👌 OK",
    10: "⚠️ Borderline", 9: "⚠️ Borderline",
}


def score_label(s: int) -> str:
    return SCORE_LABEL.get(s, "❌ Weak")
