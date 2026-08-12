"""
scorecard.py

This is the actual scoring logic. Everything else in the project (memo.py,
run_screening.py) is just plumbing around what happens in here.

Why six pillars and why these six: this is roughly how I actually read a
deal when I was underwriting at GetVantage and FinnUp. Growth tells you
if the business is working. Margin and burn multiple tell you how
efficiently it's working. Runway and leverage tell you whether it
survives long enough to matter (next round, or loan maturity, whichever
comes first). Governance is the one thing a spreadsheet can't tell you,
so I didn't try to make it pretend to — it's analyst input, on purpose.

    Pillar                      Weight   Why this weight
    --------------------------------------------------------------
    Revenue Growth (YoY)          20%    the single best "is this working" signal
    Gross Margin                  15%    matters, but less than growth at this stage
    Cash Runway                   20%    this is the one that actually kills companies
    Burn Multiple                 20%    growth bought cheaply vs. growth bought expensively
    Leverage / Debt Coverage      15%    can they actually service more debt
    Governance & Concentration    10%    the qualitative stuff, kept deliberately small

Composite score (weighted average, 1-5) maps to a rating:

    4.3 - 5.0   Strong Investment Grade  -> proceed to committee
    3.5 - 4.2   Investment Grade         -> proceed with conditions
    2.7 - 3.4   Watch                    -> more DD / structured terms
    1.9 - 2.6   High Risk                -> decline or heavy structuring
    1.0 - 1.8   Decline                  -> pass

One thing I want to be clear about, because it's easy to overstate what a
tool like this does: this is a first-pass screen, not a credit decision.
It's meant to make the reasoning explicit and repeatable enough that you
could hand the memo to a committee and defend every line of it. It is
not meant to replace the committee.
"""

from dataclasses import dataclass, field
from typing import Optional

from credit_screener.benchmarks import get_benchmark, SectorBenchmark

PILLAR_WEIGHTS = {
    "revenue_growth": 0.20,
    "gross_margin": 0.15,
    "runway": 0.20,
    "burn_multiple": 0.20,
    "leverage": 0.15,
    "governance": 0.10,
}

RATING_BANDS = [
    (4.3, 5.01, "Strong Investment Grade", "Proceed to committee"),
    (3.5, 4.3, "Investment Grade", "Proceed with conditions"),
    (2.7, 3.5, "Watch", "Further due diligence / structured terms required"),
    (1.9, 2.7, "High Risk", "Decline or heavily structured terms only"),
    (1.0, 1.9, "Decline", "Do not proceed"),
]


@dataclass
class CompanyFinancials:
    """
    The inputs, basically what you'd pull off a data room or a management
    pack -- or, for the sample companies in this repo, off actual filed
    accounts and annual reports.

    A lot of the fields below are Optional, and that's deliberate, not
    lazy typing. Real companies don't disclose everything. Private
    companies don't publish burn rate. Even audited public companies
    don't always break out gross margin in a way that's comparable across
    businesses. My first instinct when a field is missing is NOT to
    plug in a sector-average guess -- that just launders a guess into
    something that looks like data. Leave it None, and let score_company()
    below score around it honestly.
    """
    name: str
    sector: str  # has to match a key in benchmarks.SECTOR_BENCHMARKS, see that file
    currency: str = "EUR"  # whatever currency the source filing uses -- keep every field consistent
    arr_current: float = 0.0  # current revenue (or ARR, if it's genuinely recurring)
    arr_prior_year: float = 0.0  # same metric, one period back

    # everything below this line is allowed to be missing
    gross_margin: Optional[float] = None  # decimal, e.g. 0.46 not 46
    monthly_net_burn: Optional[float] = None
    cash_on_hand: Optional[float] = None
    net_new_arr_ttm: Optional[float] = None  # net new revenue added, trailing twelve months
    existing_debt: float = 0.0  # 0.0 means "found no evidence of debt", not "confirmed debt-free"
    ebitda: Optional[float] = None
    governance_score: int = 3  # 1-5, this is the one field that's always me, not the filing
    governance_notes: str = ""
    funding_ask: float = 0.0  # only meaningful for a live deal -- 0 for a retrospective screen
    analyst: str = ""
    notes: str = ""
    data_notes: str = ""  # what's real, what's derived, what's missing -- see SOURCES.md for the long version

    # Some companies just don't fit the model. A licensed lender funded by
    # customer deposits doesn't have "cash runway" the way a startup does --
    # forcing that pillar through the formula would spit out a confident-
    # looking number that means the wrong thing. This lets me say "not
    # applicable, and here's why" instead, which is a different (and more
    # honest) statement than "unknown."
    excluded_pillars: dict = field(default_factory=dict)  # {pillar_name: reason}


@dataclass
class PillarResult:
    name: str
    raw_value: str
    score: int  # 1-5, or None if unscored
    weight: float
    commentary: str


@dataclass
class ScorecardResult:
    company: CompanyFinancials
    benchmark: SectorBenchmark
    pillars: list = field(default_factory=list)
    composite_score: float = 0.0
    rating: str = ""
    recommendation: str = ""
    weight_coverage: float = 1.0  # what fraction of the six pillars actually got scored
    unscored_pillars: list = field(default_factory=list)

    @property
    def weighted_contribution(self):
        return {p.name: (round(p.score * p.weight, 2) if p.score is not None else None) for p in self.pillars}


def _score_against_benchmark(value: float, median: float, top_quartile: float,
                              higher_is_better: bool = True) -> int:
    """
    Turns a raw number into a 1-5 score by checking where it sits between
    the sector median and top quartile. I split the gap between median and
    top-quartile in half to get the 3/4 boundary, and mirror that below
    the median for the 2/1 boundary -- it's a simple linear banding, not
    trying to be a statistical model. For burn multiple, "lower is better"
    so the comparison just flips.
    """
    gap = top_quartile - median
    half = gap / 2

    if higher_is_better:
        if value >= top_quartile:
            return 5
        elif value >= median + half:
            return 4
        elif value >= median:
            return 3
        elif value >= median - half:
            return 2
        else:
            return 1
    else:
        if value <= top_quartile:
            return 5
        elif value <= median - half:
            return 4
        elif value <= median:
            return 3
        elif value <= median + half:
            return 2
        else:
            return 1


def _score_runway(months: float) -> int:
    # These bands aren't sector-benchmarked like the others -- runway is
    # runway regardless of industry. 24 months+ is comfortably past the
    # next fundraise cycle; under 6 is the danger zone regardless of what
    # else looks good on the scorecard.
    if months >= 24:
        return 5
    elif months >= 18:
        return 4
    elif months >= 12:
        return 3
    elif months >= 6:
        return 2
    else:
        return 1


def _score_leverage(company: CompanyFinancials) -> int:
    """
    Ideally this is a debt service coverage ratio (EBITDA / debt), which is
    the real underwriting metric. Problem is, pre-profitability companies
    don't have positive EBITDA to divide by, and that's most of who
    venture debt actually lends to. So when EBITDA isn't usable, I fall
    back to debt-to-revenue instead -- cruder, but it's the metric lenders
    actually use for exactly this reason.
    """
    if company.existing_debt <= 0:
        return 5  # no debt found -- see the caveat on existing_debt above
    if company.ebitda and company.ebitda > 0:
        dscr = company.ebitda / company.existing_debt
        if dscr >= 3:
            return 5
        elif dscr >= 2:
            return 4
        elif dscr >= 1.2:
            return 3
        elif dscr >= 0.8:
            return 2
        else:
            return 1
    else:
        debt_to_arr = company.existing_debt / company.arr_current if company.arr_current else 99
        if debt_to_arr <= 0.15:
            return 5
        elif debt_to_arr <= 0.30:
            return 4
        elif debt_to_arr <= 0.50:
            return 3
        elif debt_to_arr <= 0.75:
            return 2
        else:
            return 1


def score_company(company: CompanyFinancials) -> ScorecardResult:
    benchmark = get_benchmark(company.sector)
    pillars = []

    # --- Pillar 1: Revenue growth ---
    # This one's always scoreable -- it only needs the two revenue fields,
    # which is the bare minimum you'd need to screen anything at all.
    growth = (company.arr_current - company.arr_prior_year) / company.arr_prior_year if company.arr_prior_year else 0
    growth_score = _score_against_benchmark(
        growth, benchmark.revenue_growth_yoy_median, benchmark.revenue_growth_yoy_top_quartile, True
    )
    pillars.append(PillarResult(
        "revenue_growth", f"{growth:+.1%} YoY (sector median {benchmark.revenue_growth_yoy_median:.0%})",
        growth_score, PILLAR_WEIGHTS["revenue_growth"],
        f"Revenue moved from {company.arr_prior_year:,.0f} to {company.arr_current:,.0f} (same currency/unit as entered)."
    ))

    # --- Pillar 2: Gross margin ---
    # Watch the order of checks here: excluded_pillars gets checked first,
    # because "not applicable" and "not disclosed" are different findings
    # and I want the commentary to say the right one.
    if "gross_margin" in company.excluded_pillars:
        pillars.append(PillarResult(
            "gross_margin", "Not applicable", None, PILLAR_WEIGHTS["gross_margin"],
            company.excluded_pillars["gross_margin"]
        ))
    elif company.gross_margin is not None:
        margin_score = _score_against_benchmark(
            company.gross_margin, benchmark.gross_margin_median, benchmark.gross_margin_top_quartile, True
        )
        pillars.append(PillarResult(
            "gross_margin", f"{company.gross_margin:.1%} (sector median {benchmark.gross_margin_median:.0%})",
            margin_score, PILLAR_WEIGHTS["gross_margin"],
            "Unit economics " + ("above" if company.gross_margin >= benchmark.gross_margin_median else "below") + " sector median."
        ))
    else:
        pillars.append(PillarResult(
            "gross_margin", "Not publicly disclosed", None, PILLAR_WEIGHTS["gross_margin"],
            "No gross margin figure could be sourced publicly for this company; excluded from the composite rather than estimated."
        ))

    # --- Pillar 3: Cash runway ---
    # Needs both cash and burn to mean anything -- half the inputs gets
    # you nowhere here, so I don't try to salvage a partial calculation.
    if "runway" in company.excluded_pillars:
        pillars.append(PillarResult(
            "runway", "Not applicable", None, PILLAR_WEIGHTS["runway"],
            company.excluded_pillars["runway"]
        ))
    elif company.cash_on_hand is not None and company.monthly_net_burn is not None:
        if company.monthly_net_burn > 0:
            runway_months = company.cash_on_hand / company.monthly_net_burn
            runway_score = _score_runway(runway_months)
            desc = f"{runway_months:.1f} months at current burn"
        else:
            # burn is zero or negative -- i.e. cash flow positive. Give it top marks
            # rather than dividing by zero and blowing up.
            runway_score = 5
            desc = "Cash flow positive / no net burn"
        pillars.append(PillarResult(
            "runway", desc, runway_score, PILLAR_WEIGHTS["runway"],
            f"Cash on hand of {company.cash_on_hand:,.0f} against monthly net burn of {company.monthly_net_burn:,.0f}."
        ))
    else:
        pillars.append(PillarResult(
            "runway", "Not publicly disclosed", None, PILLAR_WEIGHTS["runway"],
            "Cash position and/or burn rate not available from public sources; excluded from the composite rather than estimated."
        ))

    # --- Pillar 4: Burn multiple (net burn / net new revenue) ---
    # The one edge case worth flagging: a company can be burning cash
    # while revenue is actually *shrinking*. Dividing by a negative net-new
    # number gives you a negative "multiple" that looks better than a
    # normal one, which is backwards -- a shrinking, cash-burning business
    # is worse than any growth-stage company with a bad-but-positive burn
    # multiple. So that case gets pinned to the floor score explicitly,
    # rather than letting the arithmetic quietly produce a flattering number.
    if "burn_multiple" in company.excluded_pillars:
        pillars.append(PillarResult(
            "burn_multiple", "Not applicable", None, PILLAR_WEIGHTS["burn_multiple"],
            company.excluded_pillars["burn_multiple"]
        ))
    elif company.monthly_net_burn is not None and company.net_new_arr_ttm is not None:
        if company.net_new_arr_ttm > 0:
            burn_multiple = (company.monthly_net_burn * 12) / company.net_new_arr_ttm
            burn_score = _score_against_benchmark(
                burn_multiple, benchmark.burn_multiple_median, benchmark.burn_multiple_top_quartile, False
            )
            desc = f"{burn_multiple:.2f}x (sector median {benchmark.burn_multiple_median:.2f}x)"
            comment = "Capital efficiency " + ("stronger than" if burn_multiple <= benchmark.burn_multiple_median else "weaker than") + " sector median."
        else:
            burn_score = 1
            desc = "Undefined -- revenue contracting while still burning cash"
            comment = ("Net new revenue is negative: the business is shrinking and still spending "
                       "cash to do it. Scored at the floor rather than as a ratio -- a negative "
                       "denominator isn't comparable to a positive-growth burn multiple.")
        pillars.append(PillarResult("burn_multiple", desc, burn_score, PILLAR_WEIGHTS["burn_multiple"], comment))
    else:
        pillars.append(PillarResult(
            "burn_multiple", "Not publicly disclosed", None, PILLAR_WEIGHTS["burn_multiple"],
            "Burn rate and/or net new revenue not available from public sources; excluded from the composite rather than estimated."
        ))

    # --- Pillar 5: Leverage / debt coverage ---
    # existing_debt defaults to 0.0, and that default is doing a lot of
    # quiet work -- it means "I didn't find evidence of debt," which is
    # not the same claim as "this company has no debt." Worth remembering
    # if you're extending this to a company where debt just wasn't in the
    # sources you had.
    if "leverage" in company.excluded_pillars:
        pillars.append(PillarResult(
            "leverage", "Not applicable", None, PILLAR_WEIGHTS["leverage"],
            company.excluded_pillars["leverage"]
        ))
    else:
        leverage_score = _score_leverage(company)
        leverage_desc = "No debt identified in public sources." if company.existing_debt <= 0 else f"{company.existing_debt:,.0f} existing debt outstanding."
        pillars.append(PillarResult(
            "leverage", leverage_desc, leverage_score, PILLAR_WEIGHTS["leverage"],
            "Existing leverage assessed against EBITDA or revenue coverage."
        ))

    # --- Pillar 6: Governance & concentration ---
    # No excluded_pillars check here on purpose -- this one is always the
    # analyst's call, so it's always present. It's the one pillar I didn't
    # try to systematize, because founder quality and key-person risk
    # genuinely aren't things a formula should be pretending to assess.
    pillars.append(PillarResult(
        "governance", f"{company.governance_score}/5 (analyst input)",
        company.governance_score, PILLAR_WEIGHTS["governance"],
        company.governance_notes or "No specific governance flags noted."
    ))

    # --- Roll it up ---
    # Composite is a weighted average over only the pillars that actually
    # scored, re-normalised so the weights still sum to 100% among
    # themselves. This is the bit that keeps the tool honest: a company
    # with three unscored pillars doesn't get a free pass, but it also
    # doesn't get punished for missing data the way it would if I just
    # zeroed out the missing pillars.
    scored = [p for p in pillars if p.score is not None]
    unscored = [p.name for p in pillars if p.score is None]
    total_weight_scored = sum(p.weight for p in scored)
    weight_coverage = round(total_weight_scored, 4)

    if total_weight_scored > 0:
        composite = sum(p.score * p.weight for p in scored) / total_weight_scored
    else:
        composite = 0.0

    rating, recommendation = "Unrated", "Insufficient data to rate"
    for low, high, label, rec in RATING_BANDS:
        if low <= composite < high:
            rating, recommendation = label, rec
            break

    # Below 70% coverage, I don't trust the rating enough to present it
    # without a flag -- two or fewer of the six pillars driving the whole
    # score is a genuinely different situation from five out of six.
    if weight_coverage < 0.7:
        recommendation += " -- LOW DATA CONFIDENCE: rating is based on partial information, treat as directional only."

    return ScorecardResult(
        company=company, benchmark=benchmark, pillars=pillars,
        composite_score=round(composite, 2), rating=rating, recommendation=recommendation,
        weight_coverage=weight_coverage, unscored_pillars=unscored
    )
