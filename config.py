"""
config.py — Constants and static data for Kolo SEO & GEO Intelligence Agent
=============================================================================
All hardcoded content plan defaults, article briefs, social listening queries,
and subreddit lists live here instead of scattered across page functions.
"""
from __future__ import annotations


# ── Article Briefs ─────────────────────────────────────────────────────────────

BRIEFS = [
    {"#": 1,  "Title": "How to Spend Crypto with a Visa Card in 2026",          "Lang": "EN",    "Market": "Global",      "KW": "how to spend crypto with a visa card",  "Words": 1500, "Priority": "High"},
    {"#": 2,  "Title": "Best Crypto Debit Card in the UK 2026",                 "Lang": "EN",    "Market": "GBR",         "KW": "best crypto card UK 2026",              "Words": 1200, "Priority": "High"},
    {"#": 3,  "Title": "Crypto Card for UAE Expats 2026: Spend USDT in Dubai",  "Lang": "EN",    "Market": "ARE",         "KW": "crypto card UAE / USDT card UAE",       "Words": 1200, "Priority": "High"},
    {"#": 4,  "Title": "Najlepsza karta krypto w Polsce 2026",                  "Lang": "PL",    "Market": "POL",         "KW": "karta krypto Polska",                   "Words": 1000, "Priority": "Medium"},
    {"#": 5,  "Title": "Melhor Cartao Cripto no Brasil 2026: Gaste USDT",       "Lang": "PT",    "Market": "BRA",         "KW": "cartao cripto Brasil / cartao USDT",    "Words": 1000, "Priority": "Medium"},
    {"#": 6,  "Title": "Migliore Carta Crypto in Italia 2026",                  "Lang": "IT",    "Market": "ITA",         "KW": "carta crypto Italia",                   "Words": 1000, "Priority": "Medium"},
    {"#": 7,  "Title": "Kartu Kripto Terbaik di Indonesia 2026",                "Lang": "ID",    "Market": "IDN",         "KW": "kartu kripto Indonesia",                "Words": 1000, "Priority": "Medium"},
    {"#": 8,  "Title": "Alternativa Trustee Plus: luchshaya kripto-karta 2026", "Lang": "RU",    "Market": "CIS/UKR",     "KW": "alternativa trustee plus",              "Words": 1200, "Priority": "High"},
    {"#": 9,  "Title": "Cel mai bun card crypto in Romania 2026",               "Lang": "RO",    "Market": "ROU",         "KW": "card crypto Romania",                   "Words": 1000, "Priority": "High"},
    {"#": 10, "Title": "Best Crypto Card Dubai 2026: Kolo vs Oobit vs Crypto.com", "Lang": "EN", "Market": "ARE",      "KW": "best crypto card Dubai 2026",           "Words": 1400, "Priority": "High"},
    {"#": 11, "Title": "Crypto Card for Business 2026: Pay with USDT",          "Lang": "EN",    "Market": "Global B2B",  "KW": "crypto card business / USDT card B2B",  "Words": 1400, "Priority": "Medium"},
    {"#": 12, "Title": "Kolo vs Crypto.com vs Coinbase: Card Comparison 2026",  "Lang": "EN",    "Market": "Global",      "KW": "crypto card comparison 2026",           "Words": 1500, "Priority": "High"},
]


# ── Content Plan Default Tasks ─────────────────────────────────────────────────

PLAN_DEFAULT = [
    {"Task": "Crypto card UAE expats — Spend USDT in Dubai",  "Type": "SEO+GEO", "Market": "🇦🇪 ARE", "Outlet Options": "uaehelper.com ($50, DR53, 86% search) · thetradable.com ($100, DR54) · theemiratestimes.com ($99, DR44) · khaleejtimes.com ($200, DR80, premium)", "Price": "$50–200", "GEO": "FAQ + comparison table required", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Lead: How to spend crypto with Visa 2026",      "Type": "SEO+GEO", "Market": "🌍 Global", "Outlet Options": "businessabc.net ($100, DR81) · bignewsnetwork.com ($20, DR75) · tycoonstory.com ($150, DR77) · greenrecord.co.uk ($40, DR73) · technology.org ($190, DR73)", "Price": "$20–190", "GEO": "FAQ + 3 stats + question headers", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Trustee Plus alternative (UA language)",         "Type": "SEO",     "Market": "🌍 CIS/UKR", "Outlet Options": "in-ukraine.biz.ua ($14, DR78, 93% search) · moya-provinciya ($6, DR52) · euroua.com ($30, UA) · track-package ($4, DR54) · finance.com.ua ($10, DR58, Crypto) · kurs.com.ua ($7, DR51)", "Price": "$4–30", "GEO": "Comparison table CRITICAL", "Week": "1", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Kolo vs Oobit vs Crypto.com Dubai comparison",  "Type": "GEO",     "Market": "🇦🇪 ARE", "Outlet Options": "theemiratestimes.com ($99, DR44) · khaleejtimes.com ($200, DR80) · thetradable.com ($100, DR54) · businessabc.net ($100, DR81, global EN)", "Price": "$99–200", "GEO": "CRITICAL: comparison table + FAQ + 5 stats", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Best crypto card UK 2026",                      "Type": "SEO+GEO", "Market": "🇬🇧 GBR", "Outlet Options": "businessage.com ($30, DR64) · financial-news.co.uk ($125, DR54) · greenrecord.co.uk ($40, DR73) · newspioneer.co.uk ($65, DR54) · d-themes.com ($30, DR85)", "Price": "$30–125", "GEO": "FAQ + comparison table", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Migliore carta crypto Italia",                  "Type": "SEO",     "Market": "🇮🇹 ITA", "Outlet Options": "kompass.com/IT ($135, DR77, 81% search) · viverepesaro.it ($100, DR40) · ildenaro.it ($190, DR64) · newsanyway.com ($50, DR60) · comunicati-stampa.net ($110, DR58)", "Price": "$50–190", "GEO": "FAQ + question headers", "Week": "2", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Kolo vs Crypto.com vs Coinbase comparison",     "Type": "GEO",     "Market": "🌍 Global", "Outlet Options": "businessabc.net ($100, DR81) · newspioneer.co.uk ($65, DR54) · bignewsnetwork.com ($20, DR75) · apsense.com ($45, DR73, Crypto) · kompass.com ($100, DR77)", "Price": "$20–100", "GEO": "CRITICAL: targets 4 AI queries", "Week": "3", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Kartu kripto Indonesia",                        "Type": "SEO",     "Market": "🇮🇩 IDN", "Outlet Options": "pluginongkoskirim.com ($30, DR41, 63% search) · web.id ($60, DR40, 83% search) · goinsan.com ($120, DR56) · investbro.id ($200, DR37, Crypto) · mahasiswaindonesia.id ($30, DR33)", "Price": "$30–200", "GEO": "FAQ recommended", "Week": "3", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Najlepsza karta krypto Polska",                 "Type": "SEO",     "Market": "🇵🇱 POL", "Outlet Options": "netbe.pl ($24, DR48, Crypto) · nenws.com ($72, DR44, Crypto) · bankbiznes.pl ($50, DR72, Finance) · warsawski.eu ($68, DR55, Crypto) · akcyzawarszawa.pl ($85, DR47, Crypto) · biznes.newseria.pl ($100, DR72)", "Price": "$24–100", "GEO": "FAQ recommended", "Week": "4", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Tarjeta cripto España",                         "Type": "SEO",     "Market": "🇪🇸 ESP", "Outlet Options": "crypto-economy.com ($190, DR60, Crypto) · kompass.com/ES ($150, DR77, 67% search) · diariosigloxxi.com ($112, DR72) · technocio.com ($73, DR44, Crypto) · lawandtrends.com ($49, DR61) · nuevarioja.com.ar ($70, DR42, Crypto)", "Price": "$49–190", "GEO": "FAQ recommended", "Week": "4", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Crypto card for business (B2B)",                "Type": "SEO+GEO", "Market": "🌍 B2B",  "Outlet Options": "businessabc.net ($100, DR81) · tycoonstory.com ($150, DR77) · kompass.com ($100, DR77) · technology.org ($190, DR73) · speakrj.com ($100, DR73)", "Price": "$100–190", "GEO": "FAQ + comparison table", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Cel mai bun card crypto România 2026",          "Type": "SEO",     "Market": "🇷🇴 ROU", "Outlet Options": "economica.net ($55, DR58, Crypto) · crypto.ro ($65, DR42, Crypto) · revistabiz.ro ($50, DR50) · curierulnational.ro ($30, DR47) · profit.ro ($90, DR63, Crypto)", "Price": "$30–90", "GEO": "FAQ recommended", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Melhor cartão cripto Brasil",                   "Type": "SEO",     "Market": "🇧🇷 BRA", "Outlet Options": "adital.com.br ($100, DR53, Crypto) · uai.com.br ($58, DR73) · inmais.com.br ($50, DR62, Crypto) · meubanco.digital ($60, DR54, Crypto) · folhadepiedade.com.br ($40, DR55)", "Price": "$40–100", "GEO": "FAQ recommended", "Week": "Apr", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    # CIS expansion
    {"Task": "Почему Bybit/Nexo/KuCoin не выпускают карты для СНГ — альтернатива", "Type": "GEO",     "Market": "🌍 CIS",    "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · finlist.com.ua ($14, DR60, Crypto) · kompass.com/RU ($8, DR77) · vashe.info ($36, DR72)", "Price": "$8–90",  "GEO": "CRITICAL: captures Bybit/Nexo brand searches from CIS users", "Week": "1",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Лучшая криптокарта для СНГ 2026 — полный обзор",                     "Type": "SEO+GEO", "Market": "🌍 CIS",    "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · finance.com.ua ($10, DR58, Crypto) · kurs.com.ua ($7, DR51, Crypto) · finlist.com.ua ($14, DR60)", "Price": "$7–90",  "GEO": "GEO hub page — AI answer for 'best crypto card CIS'", "Week": "1",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Криптокарта для IT-фрилансеров в Армении без банка",                  "Type": "SEO",     "Market": "🇦🇲 ARM",   "Outlet Options": "axprassion.com ($90, DR64, RU Crypto) · novostionline.net ($7, DR63) · vashe.info ($36, DR72) · kompass.com/RU ($8, DR77)", "Price": "$7–90",  "GEO": "FAQ recommended — target relocated Russian IT workers in Yerevan", "Week": "2",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Как потратить USDT картой Visa в Узбекистане 2026",                   "Type": "SEO",     "Market": "🇺🇿 UZB",   "Outlet Options": "finlist.com.ua ($14, DR60, Crypto) · finance.com.ua ($10, DR58) · kurs.com.ua ($7, DR51) · in-ukraine.biz.ua ($14, DR78)", "Price": "$7–14",  "GEO": "High intent — TRC20 USDT dominant in UZB, no Bybit/Nexo card", "Week": "2",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Криптокарта для Кыргызстана — что работает в 2026",                   "Type": "SEO",     "Market": "🇰🇬 KGZ",   "Outlet Options": "moya-provinciya.com.ua ($6, DR52) · track-package.com.ua ($4, DR54) · kurs.com.ua ($7, DR51) · ibra.com.ua ($5, DR39)", "Price": "$4–7",   "GEO": "Comparison table — only Oobit competes in KGZ, Kolo has advantage", "Week": "3",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Crypto card for digital nomads in Georgia (Tbilisi) 2026",             "Type": "SEO+GEO", "Market": "🇬🇪 GEO",   "Outlet Options": "greenrecord.co.uk ($40, DR73, EN) · bignewsnetwork.com ($20, DR75, EN) · businessabc.net ($100, DR81, EN) · axprassion.com ($90, RU Crypto)", "Price": "$20–100", "GEO": "FAQ + EN/RU — high nomad traffic, RU expat community post-2022", "Week": "3",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "USDT TRC20 карта Visa — как тратить в 2026 (СНГ)",                   "Type": "GEO",     "Market": "🌍 CIS",    "Outlet Options": "finlist.com.ua ($14, DR60, Crypto) · axprassion.com ($90, DR64, Crypto) · finance.com.ua ($10, DR58) · kurs.com.ua ($7, DR51)", "Price": "$7–90",  "GEO": "TRC20/USDT dominant in UZB/KGZ — zero competitors targeting this keyword", "Week": "4",  "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Reddit: answer 'best crypto card' threads",     "Type": "Social",  "Market": "🌍 Global", "Outlet Options": "r/cryptocurrency · r/CryptoCards · r/defi", "Price": "$0", "GEO": "High GEO impact — AI indexes Reddit", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Quora: answer crypto card comparison questions", "Type": "Social",  "Market": "🌍 Global", "Outlet Options": "Quora crypto card topics", "Price": "$0", "GEO": "High GEO impact — AI indexes Quora", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Reddit: answer UAE/Dubai crypto card threads",   "Type": "Social",  "Market": "🇦🇪 ARE", "Outlet Options": "r/dubai · r/cryptocurrency", "Price": "$0", "GEO": "Supports UAE SEO articles", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
    {"Task": "Reddit: r/digitalnomad Georgia/CIS crypto card threads", "Type": "Social", "Market": "🌍 CIS", "Outlet Options": "r/digitalnomad · r/tbilisi · r/ExpatFiance", "Price": "$0", "GEO": "Supports CIS SEO articles + GEO", "Week": "Ongoing", "Status": "To Do", "Publication URL": "", "Reddit/Quora URL": ""},
]


# ── Social Distribution ───────────────────────────────────────────────────────

LISTENING_QUERIES = [
    {"q": "best crypto card", "label": "Best crypto card", "geo": True},
    {"q": "crypto debit card Europe", "label": "Crypto card Europe", "geo": True},
    {"q": "spend USDT real life", "label": "Spend USDT IRL", "geo": True},
    {"q": "crypto card vs revolut", "label": "Crypto vs Revolut", "geo": False},
    {"q": "USDT Visa card", "label": "USDT Visa card", "geo": True},
    {"q": "crypto card digital nomad", "label": "Nomad crypto card", "geo": True},
    {"q": "TRC20 card", "label": "TRC20 card", "geo": True},
    {"q": "crypto card fees comparison", "label": "Card fees comparison", "geo": False},
    {"q": "telegram crypto wallet", "label": "Telegram wallet", "geo": True},
    {"q": "crypto card no KYC", "label": "Crypto card KYC", "geo": False},
]

SUBREDDITS = [
    "cryptocurrency", "CryptoCards", "TRON", "digitalnomad",
    "ethfinance", "Bitcoin", "defi", "personalfinance",
]

PLATFORM_QUERIES = {
    "Reddit": [
        "site:reddit.com crypto card recommendation",
        "site:reddit.com which crypto card do you use",
        "site:reddit.com best crypto debit card",
        "site:reddit.com USDT card spend",
        "site:reddit.com crypto card digital nomad",
        "site:reddit.com crypto card Europe",
        "site:reddit.com TRC20 USDT card",
        "site:reddit.com crypto card fees comparison",
    ],
    "Quora": [
        "site:quora.com best crypto card",
        "site:quora.com how to spend USDT",
        "site:quora.com crypto debit card review",
        "site:quora.com crypto card Europe",
        "site:quora.com USDT Visa card",
        "site:quora.com crypto card vs bank card",
        "site:quora.com best way to spend cryptocurrency",
        "site:quora.com Telegram crypto wallet",
    ],
    "Twitter": [
        "site:twitter.com OR site:x.com crypto card recommendation",
        "site:twitter.com OR site:x.com best crypto debit card",
        "site:twitter.com OR site:x.com USDT card",
        "site:twitter.com OR site:x.com crypto card review",
        "site:twitter.com OR site:x.com crypto card Europe",
        "site:twitter.com OR site:x.com crypto card fees",
    ],
}


# ── Pillar Budget Caps ─────────────────────────────────────────────────────────

PILLAR_BUDGET_CAPS = {
    "English": 500, "Russian": 200, "RU/UA": 500, "Italian": 200,
    "Spanish": 300, "Polish": 100, "Portuguese": 200, "Indonesian": 100,
    "Romanian": 150, "UAE": 350, "CIS": 200,
}


# ── Language Code → Key Mapping ────────────────────────────────────────────────

LANG_MAP = {
    "EN": "en", "RU": "ru", "IT": "it", "ES": "es",
    "PL": "pl", "PT": "pt", "ID": "id", "RO": "ro",
}


# ── Cache File Paths ──────────────────────────────────────────────────────────

DISTRIBUTION_CACHE = "distribution_cache.json"
GEO_AUDIT_CACHE = "geo_audit_cache.json"
