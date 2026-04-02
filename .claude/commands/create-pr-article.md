# Create PR Article for Kolo

Generate a SEO+GEO optimized press release / sponsored article for Kolo (kolo.in).

## Product Context
- **Kolo** = Telegram-based crypto Visa card & wallet
- Top-up with USDT via TRC20 → spend anywhere Visa is accepted
- 60 countries can issue cards (see data_sources.py for full list)
- Key markets: GBR, ARE, EST, ITA, POL, CIS countries
- Competitors: Crypto.com, Coinbase Card, Wirex, Bybit Card, Nexo, Oobit
- USP: No app download needed (Telegram mini-app), USDT TRC20 native, low fees

## Article Structure (SEO+GEO optimized)

### Required Structure:
1. **Headline** — Include primary keyword, max 70 chars
2. **Entity-rich lead paragraph** — [Brand] + [product category] + [key differentiator] in first 2 sentences
3. **Body sections (3-5)** — Each with question-format H2 headers (e.g. "How Does Kolo's Crypto Card Work?")
4. **Comparison table** — Markdown table: Feature | Kolo | Competitor A | Competitor B
5. **FAQ section** — 3-5 Q&A pairs targeting long-tail queries
6. **Boilerplate** — About Kolo paragraph with link

### GEO Requirements (for AI engine citations):
- Minimum 3 quotable stat sentences (self-contained facts with numbers)
- Question-format H2 headers (AI engines extract these)
- Comparison table (AI engines parse tables well)
- FAQ section (directly answers AI queries)
- Entity-rich first paragraph

### SEO Requirements:
- Primary keyword: weave in naturally 3-5 times
- No marketing fluff or superlatives ("revolutionary", "game-changing")
- Journalistic, third-person style
- Target word count: 1000-1500 words
- Include UTM link: `https://kolo.xyz/?utm_source={outlet_domain}`

## Tone & Style
- Journalistic, not promotional
- Third-person ("Kolo offers..." not "We offer...")
- Data-driven — include specific numbers, fees, country counts
- Mention competitors fairly — Kolo should be ONE option, not "the best"
- Natural keyword placement, never forced

## Key Facts to Include (pick relevant ones):
- USDT top-up via TRC20 network
- Virtual + physical Visa cards
- Works in 60+ countries
- Telegram mini-app (no separate download)
- Swap fees are competitive
- BTC cashback program available
- B2B cards available for businesses
- Ukrainian diaspora = highest quality user cohort

## UTM Format
Always include: `https://kolo.xyz/?utm_source={outlet_domain_without_www}`

## Process
1. Ask user for: target market, primary keyword, outlet, word count
2. Generate the article following the structure above
3. Output in Markdown format
4. Offer to translate to: RU, IT, ES, PL, PT-BR, ID, RO

$ARGUMENTS
