# Private Credit Screening Tool

A rules-based credit scoring engine that takes a company's financials and outputs a six-pillar scorecard, a funding viability rating, and a one-page PDF memo — the kind of first-pass output an analyst would put together in Excel and Word before a deal goes to committee.

I built this to replicate the screening workflow I actually ran at **GetVantage** (200+ companies underwritten) and **FinnUp** (80+ startups, EUR 11-22M pipeline). The bottleneck there was never the analysis itself. It was doing it the same way twice — consistently, fast enough to keep up with deal flow, and in a format someone could sign off on without re-deriving my logic from scratch.

**Scored against real, publicly disclosed financials, not made-up companies.** Three examples are in the sample data, each sourced from a different kind of document:

- **Pennylane** (French fintech) — scored from the company's own filed statutory accounts for FY2022, pulled from the Greffe du Tribunal de Commerce. Comes out Investment Grade, with a specific and slightly unglamorous reason why: strong growth on a strong balance sheet, in a year the company was clearly still spending heavily to build the product rather than running efficiently.
- **Younited Financial** (licensed consumer credit institution, France/Luxembourg) — scored from KPMG-audited consolidated IFRS statements. Most of the tool's pillars are marked "not applicable" here on purpose, because the model this tool uses (burn rate, cash runway) is built for equity-funded startups, and Younited is funded by customer deposits. Forcing those pillars through the formula anyway would have produced a number that looked precise and meant the wrong thing.
- **Made.com** (UK D2C furniture retailer) — screened as of its own August 2022 trading update. Comes out High Risk. The company actually went into administration three months later, which wasn't something I knew when I built the scoring logic — it's a genuinely useful sense check that the framework reacts the way it should to a real, fast-moving deterioration.

Every number in the sample data is cited in [`SOURCES.md`](./SOURCES.md), including the fields I couldn't verify and left blank on purpose, and the pillars I judged inapplicable rather than forced.

**Sample memos:**
[Pennylane](sample_output/pennylane_credit_memo.pdf) · [Younited Financial](sample_output/younited_financial_credit_memo.pdf) · [Made.com](sample_output/made.com_credit_memo.pdf)

---

## The problem this is actually solving

Early-stage credit and venture debt teams see more deal flow than they can diligence deeply, so the first pass — "is this even worth a full data room review?" — usually gets done fast, informally, and without much of a paper trail. Two things go wrong because of that:

1. **Inconsistency.** Two analysts screening the same company on the same day, with the same information, can land in different places, because there's no shared framework forcing the comparison to be apples-to-apples.
2. **No audit trail.** When someone on the committee asks "why did we pass on this," the honest answer often lives in someone's head rather than in the deal file.

This tool doesn't try to replace the analyst's judgment — the governance pillar is explicitly left as a manual 1-5 input for exactly that reason. What it does is force every company through the same six checks, benchmark them against sector norms instead of gut feel, and write the reasoning down automatically so it survives past the conversation where it happened.

---

## How the scoring actually works

Six pillars, each scored 1-5, combined into a weighted composite:

| Pillar | Weight | What it's actually checking |
|---|---|---|
| Revenue Growth (YoY) | 20% | Is the business working, full stop |
| Gross Margin | 15% | Unit economics, benchmarked by sector |
| Cash Runway | 20% | The metric that actually kills companies |
| Burn Multiple | 20% | Growth bought cheaply vs. growth bought expensively |
| Leverage / Debt Coverage | 15% | Room to service more debt |
| Governance & Concentration | 10% | The part a spreadsheet genuinely can't tell you |

Composite score maps to a rating:

| Score | Rating | What I'd actually do with it |
|---|---|---|
| 4.3 – 5.0 | Strong Investment Grade | Take it to committee |
| 3.5 – 4.2 | Investment Grade | Take it to committee, with conditions |
| 2.7 – 3.4 | Watch | Needs more diligence or a structured facility |
| 1.9 – 2.6 | High Risk | Decline, or heavy structuring only |
| 1.0 – 1.8 | Decline | Pass |

Sector benchmarks (fintech, SaaS, consumer, beauty & apparel, healthcare) live in `credit_screener/benchmarks.py` and are directional medians assembled from public sources — not a live data feed. Swapping in a real vendor (PitchBook, Carta, etc.) is the obvious next step if this were going into production rather than a portfolio.

### Missing data doesn't get papered over

Real companies don't disclose everything, and some metrics genuinely don't apply to some business models. Rather than fill a gap with a sector-average guess, the tool draws a line between two different situations:

- **Undisclosed** — the number just isn't public. That pillar is left out of the composite, and the remaining pillars are re-weighted to fill the gap. Coverage below 70% triggers a visible "LOW DATA CONFIDENCE" flag on the memo.
- **Not applicable** — the pillar doesn't mean what it's supposed to mean for this company (Younited's cash runway is the example above). The analyst states why, and that reason shows up in the memo instead of a number.

Both are visible on every memo, along with a data-coverage percentage, so nobody reading it mistakes an 85%-coverage rating for the same thing as a 30%-coverage one.

---

## Project structure

```
private-credit-screener/
├── credit_screener/
│   ├── scorecard.py      # the actual scoring logic
│   ├── benchmarks.py     # sector reference data
│   └── memo.py           # PDF memo layout (ReportLab)
├── data/
│   └── sample_companies.json   # Pennylane, Younited Financial, Made.com
├── sample_output/         # generated PDF memos land here
├── run_screening.py       # run this
├── SOURCES.md              # exactly where every number in the sample data came from
└── requirements.txt
```

## Running it

```bash
pip install -r requirements.txt
python run_screening.py
```

Console output:

```
Company             Sector            Score   Rating                    Recommendation
----------------------------------------------------------------------------------------------------
Pennylane           Fintech           3.94    Investment Grade          Proceed with conditions
Younited Financial  Fintech           1.67    Decline                   Do not proceed -- LOW DATA CONFIDENCE...
Made.com            Consumer          2.2     High Risk                 Decline or heavily structured terms only
```

Each company also gets a full PDF memo in `sample_output/` — rating up top, then the scorecard, then a financial snapshot, then the notes that actually explain the number.

To score your own companies, point `--input` at a different JSON file shaped like `data/sample_companies.json`. The fields map directly onto `credit_screener.scorecard.CompanyFinancials` — set anything you don't have to `null`, and use `excluded_pillars` for anything that structurally doesn't apply to the company you're screening.

```bash
python run_screening.py --input data/my_companies.json --output-dir memos
```

---

## What I'd do next if I kept building this

- Wire in a real data vendor instead of the static benchmark table
- A stress-test view: how does the rating move if burn goes up 20%, or a funding round slips six months
- Batch mode with a portfolio-level summary, so this becomes a monitoring tool for an existing book, not just a new-deal screen
- A proper scoring pathway for regulated lenders instead of just excluding most of the pillars, the way Younited's entry does here
