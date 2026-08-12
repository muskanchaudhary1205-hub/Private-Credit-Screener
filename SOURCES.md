# Source Log

Every figure in `data/sample_companies.json` is either sourced below, derived from a sourced figure (with the derivation shown), or left blank because it isn't available or doesn't meaningfully apply to the company. Nothing here is estimated to fill a gap. Where I'm not confident in a number, that's stated rather than smoothed over.

Last verified: 12 August 2026.

---

## Pennylane (fintech, France) — FY2022, from filed statutory accounts

Source: **PENNYLANE — Comptes sociaux 2022**, filed with the Greffe du Tribunal de Commerce de Cherbourg on 28/10/2024, audited by SEFAC (unqualified opinion, 19 May 2023).

| Field | Value used | Where it's from |
|---|---|---|
| Revenue (chiffre d'affaires), FY2022 | EUR 3,918,048 | Compte de résultat, "Montant net du chiffre d'affaires" |
| Revenue, FY2021 | EUR 1,529,789 | Same table, prior-year column |
| Cash on hand (disponibilités) | EUR 48,291,281 | Bilan actif, "Disponibilités" |
| Existing debt | EUR 200,000 | Bilan passif, "Emprunts et dettes auprès des établissements de crédit" — unchanged between FY2021 and FY2022, which reads like a single ongoing facility rather than active borrowing |
| Operating result (used to derive burn) | EUR (21,519,130) | Compte de résultat, "Résultat d'exploitation" |
| Net loss for the year | EUR (20,409,232) | Compte de résultat, "Résultat de l'exercice" — cross-checked against the AGM minutes (PV du 31 mai 2023), which record the same figure |
| Founder voting control, share lock-up to 2032 | — | Statuts, articles 8.3.1 and 9 ("Inaliénabilité") |
| Audit opinion | Unqualified, no going-concern flag | Rapport du commissaire aux comptes (SEFAC), 19 May 2023 |

**Derived, not directly disclosed:**
- Monthly net burn (EUR 1,793,261) = operating result ÷ 12. There's no cash flow statement in this filing, so this is a proxy off the income statement rather than a literal cash-burn number.
- Net new revenue (EUR 2,388,259) = FY2022 revenue minus FY2021 revenue, both of which are directly disclosed.

**Left blank:** gross margin. This set of accounts, prepared under French GAAP, doesn't separate a cost-of-revenue line from operating expenses — "Autres achats et charges externes" (EUR 14.4m) bundles R&D subcontracting, marketing, and general overhead into one figure, so there's no defensible way to isolate a COGS number and compute a margin from it. That's a feature of this accounting presentation, not something I could close by digging harder.

**Worth flagging on timing:** this filing is roughly two years before the EUR 60m (2024) / EUR 115m (2025) ARR figures reported in the press (Sifted, Maddyness). Those two data points sit on different bases entirely and aren't combined anywhere in this scorecard — FY2022 is scored as its own snapshot, which happens to land in a heavy-investment, pre-profitability phase of the company's life. The later, more mature trajectory is mentioned in the `notes` field for context, not used in the score.

---

## Younited Financial (licensed consumer credit institution, France/Luxembourg) — FY2024, from audited consolidated statements

Source: **Younited Financial S.A. — Consolidated Financial Statements 2024**, audited by KPMG Luxembourg (unqualified opinion), approved by the Board 3 April 2025.

| Field | Value used | Where it's from |
|---|---|---|
| Revenue, FY2024 | EUR 94,671,000 | Consolidated statement of profit or loss, "Revenue" |
| Revenue, FY2023 | EUR 101,755,000 | Same table, prior-year column |
| Net loss, FY2024 | EUR (83,439,000) | Same table, "Loss for the year" |
| Net loss, FY2023 | EUR (49,679,000) | Same table |
| Listing expense (one-off, part of the FY2024 loss) | EUR 29,934,000 | Note 11, "Other operating expenses" |
| Share-based payment expense, mostly accelerated by the SPAC closing | EUR 31,706,000 | Consolidated statement of cash flows |
| Total equity, FY2024 vs FY2023 | EUR 238,474,000 vs EUR 143,383,000 | Consolidated statement of financial position |
| Customer deposits, FY2024 | EUR 832,722,000 | Same statement, "Deposits from deposit holders" |
| Loans/deposits from financial institutions, FY2024 | EUR 60,611,000 | Same statement |
| Cash and cash equivalents at year end | EUR 276,846,000 | Consolidated statement of cash flows |
| Audit opinion | Unqualified, no going-concern flag | Report of the réviseur d'entreprises agréé, KPMG Audit S.à r.l. |

A note on how I got here: before I had the primary source, two Yahoo Finance data feeds (for two tickers of the same company) showed inconsistent FY2024 revenue — one said the equivalent of GBP 73.8m, the other GBP 94.7m. The audited figure above (EUR 94.67m, a 7.0% YoY decline) resolves that, and it's a meaningfully smaller decline than the higher aggregator figure would have implied. Going back to the primary source caught a real discrepancy rather than just adding a second opinion to the pile.

**Why four of the six pillars are marked "not applicable" rather than scored:** Younited is a licensed, deposit-and-wholesale-funded lender, not an equity-funded startup. Gross margin, cash runway, burn multiple, and leverage as this tool defines them assume a company burning down an equity war chest — none of that maps cleanly onto a regulated lender whose deposits and institutional borrowing *are* the funding model, not incremental risk sitting on top of one. Scoring "leverage" as 5/5 (the tool's default for "no debt found") would have been actively wrong here, not just approximate — Younited obviously carries very large liabilities, they're just not the kind this particular pillar is built to read. I judged it more honest to mark these four pillars "not applicable," with the reason stated, than to compute a number that looks precise and means the wrong thing.

**Net effect:** only revenue growth (20% weight) and governance (10% weight) get scored — 30% coverage, which is why the memo's low-confidence flag fires. The resulting "Decline" rating is really a statement that "on the two dimensions this tool can actually assess for a business like this, FY2024 wasn't strong" — not a real committee-grade opinion on the company. H1 2025 results (outside this filing, so not scored) showed revenue up 48% YoY, which suggests the FY2024 dip didn't turn into a trend.

---

## Made.com (D2C furniture retailer, UK — entered administration Nov 2022)

Sourced from public reporting rather than a filing I was handed directly — Made.com never published FY2022 accounts, because it collapsed before the year closed.

| Field | Value used | Source | Note |
|---|---|---|---|
| FY2020 revenue | GBP 247m | [Tracxn](https://tracxn.com/d/companies/made.com/) | Used to sanity-check the FY2021 growth figure below |
| FY2021 revenue | GBP 371m | [Wikipedia](https://en.wikipedia.org/wiki/Made.com), citing company results | Cross-checked against EUR 448.1m reported by [ecommercenews.eu](https://ecommercenews.eu/made-com-loss-of-e37-8-million-in-2021/) — the ~50% YoY growth rate matches in both currencies |
| FY2021 gross margin | 46.3% (down from 53.2% in FY2020) | [ecommercenews.eu, Jul 2022](https://ecommercenews.eu/made-com-loss-of-e37-8-million-in-2021/) | Company's own full-year results |
| H1 2022 net cash | GBP 31.5m (unaudited) | [Investing.com, 18 Aug 2022](https://uk.investing.com/news/stock-market-news/madecom-shares-fall-sharply-as-group-confirms-potential-capital-raise-2725548) | Company's own trading update |
| FY2022 EBITDA loss guidance | GBP 50m–70m | Same trading update (the third profit warning of the year) | April guidance for the same year had been *positive* EBITDA of GBP 6–18m |
| FY2022 gross sales guidance | Down 15%–30% vs FY2021 | Same trading update | Midpoint (-22.5%) applied to FY2021 revenue for the "current revenue" figure. Actuals were never published — administration came on 9 Nov 2022 |
| CEO departure | Philippe Chainieux stepped down Feb 2022 | [Wikipedia](https://en.wikipedia.org/wiki/Made.com) | Feeds the governance score |
| Governance post-mortem | Board's clean going-concern sign-off questioned, ~9 months before administration | [flinder.co, Aug 2023](https://www.flinder.co/insights/made-com-what-went-wrong) | Independent retrospective, not a company source |

**Derived:** monthly net burn (~GBP 5m) = midpoint of the guided FY2022 EBITDA loss ÷ 12. That's a proxy off the company's own guidance, not a disclosed cash-burn figure, and it likely understates the real number for an inventory-heavy retailer — working capital drags cash down further than EBITDA loss alone captures, which is exactly why net cash fell from GBP 31.5m at H1 close toward a guided GBP 5-30m by year end. Existing debt is left at zero because I found no evidence of it either way in the sources reviewed — that's "not found," not "confirmed none."

---

## One company I looked at and didn't include

**Deezer** (music streaming, Euronext Paris) has excellent, fully-reconciled public numbers — FY2024 revenue growth of 12.7%, adjusted gross margin up to 24.7% from 22.7%, adjusted EBITDA improved to EUR (4.0)m from EUR (28.8)m, EUR 62m cash at year end, first year of positive free cash flow. I left it out because it doesn't fit any of the five sector benchmarks in `benchmarks.py`. Scoring it against the "consumer" median (40% gross margin) would unfairly penalize a business where royalty payments to labels are a structural cost of the model, not weak unit economics — and I wasn't willing to invent a "media streaming" benchmark without real median/top-quartile data behind it.
