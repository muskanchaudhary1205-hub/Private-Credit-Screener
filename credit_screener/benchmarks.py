"""
benchmarks.py

Sector reference points -- what "good" looks like for a company in a
given sector, so a raw number (like "83% revenue growth") means something
instead of floating in space. Without this, the scorecard can't tell the
difference between 83% growth being exceptional (in consumer, it would be)
or middling (in SaaS, where it's closer to par).

Full honesty on where these numbers come from: they're directional medians
I put together from public benchmark reports (Bessemer and OpenView publish
SaaS metrics annually, KPMG has venture debt market reports, and general VC
sector reporting covers consumer and healthtech reasonably well). They are
NOT pulled from a live data feed and I wouldn't present them to a credit
committee as audited numbers -- they're a reasonable starting point for a
portfolio project, and the obvious next step for anyone taking this
further is wiring in a real data vendor (Carta, PitchBook, etc.) instead.

Each sector gets four numbers: a median and a top-quartile figure for
revenue growth, gross margin, and burn multiple (lower is better on burn
multiple, everything else higher is better). Runway isn't sector-specific
-- 12 months of cash left is 12 months of cash left, whatever you sell.
"""

from dataclasses import dataclass


@dataclass
class SectorBenchmark:
    sector: str
    revenue_growth_yoy_median: float
    revenue_growth_yoy_top_quartile: float
    gross_margin_median: float
    gross_margin_top_quartile: float
    burn_multiple_median: float
    burn_multiple_top_quartile: float
    runway_months_median: float
    runway_months_top_quartile: float


SECTOR_BENCHMARKS = {
    "fintech": SectorBenchmark(
        sector="Fintech",
        revenue_growth_yoy_median=0.55,
        revenue_growth_yoy_top_quartile=1.00,
        gross_margin_median=0.55,
        gross_margin_top_quartile=0.72,
        burn_multiple_median=1.6,
        burn_multiple_top_quartile=0.9,
        runway_months_median=15,
        runway_months_top_quartile=24,
    ),
    "saas": SectorBenchmark(
        sector="SaaS",
        revenue_growth_yoy_median=0.60,
        revenue_growth_yoy_top_quartile=1.20,
        gross_margin_median=0.72,
        gross_margin_top_quartile=0.85,
        burn_multiple_median=1.3,
        burn_multiple_top_quartile=0.7,
        runway_months_median=18,
        runway_months_top_quartile=26,
    ),
    "consumer": SectorBenchmark(
        sector="Consumer",
        revenue_growth_yoy_median=0.40,
        revenue_growth_yoy_top_quartile=0.80,
        gross_margin_median=0.40,
        gross_margin_top_quartile=0.58,
        burn_multiple_median=1.8,
        burn_multiple_top_quartile=1.0,
        runway_months_median=14,
        runway_months_top_quartile=22,
    ),
    "beauty_apparel": SectorBenchmark(
        # Split out from generic "consumer" because return rates and margin
        # structure in beauty/apparel D2C are different enough from, say,
        # a hardware or homeware brand that lumping them together would
        # have blurred the benchmark more than it helped.
        sector="Beauty & Apparel",
        revenue_growth_yoy_median=0.35,
        revenue_growth_yoy_top_quartile=0.70,
        gross_margin_median=0.45,
        gross_margin_top_quartile=0.62,
        burn_multiple_median=1.7,
        burn_multiple_top_quartile=0.95,
        runway_months_median=13,
        runway_months_top_quartile=20,
    ),
    "healthcare": SectorBenchmark(
        sector="Healthcare",
        revenue_growth_yoy_median=0.45,
        revenue_growth_yoy_top_quartile=0.85,
        gross_margin_median=0.50,
        gross_margin_top_quartile=0.68,
        burn_multiple_median=1.9,
        burn_multiple_top_quartile=1.1,
        runway_months_median=16,
        runway_months_top_quartile=24,
    ),
}


def get_benchmark(sector: str) -> SectorBenchmark:
    # Loose matching on the sector string so "Beauty & Apparel", "beauty_apparel"
    # and "beauty & apparel " all land on the same key -- one less thing to
    # get wrong when typing up a new company.
    key = sector.strip().lower().replace(" ", "_").replace("&", "").replace("__", "_")
    if key not in SECTOR_BENCHMARKS:
        valid = ", ".join(SECTOR_BENCHMARKS.keys())
        raise ValueError(f"Unknown sector '{sector}'. Valid sectors: {valid}")
    return SECTOR_BENCHMARKS[key]
