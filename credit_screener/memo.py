"""
memo.py

Turns a ScorecardResult into an actual PDF -- the thing you'd attach to
an email or drop in a deal file, not just a printout of the console output.

Laid out the way I'd want a one-page opinion to read if I hadn't written
it myself: rating first, in a color you can't miss, before any of the
supporting detail. Nobody reading fifteen of these in a row wants to hunt
for the verdict on page two.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from credit_screener.scorecard import ScorecardResult

# Green-to-red down the rating scale, roughly the same visual language
# most people already read as "good to bad" -- no legend needed.
RATING_COLORS = {
    "Strong Investment Grade": colors.HexColor("#1a7a3c"),
    "Investment Grade": colors.HexColor("#4a8f3c"),
    "Watch": colors.HexColor("#c98a1a"),
    "High Risk": colors.HexColor("#c9541a"),
    "Decline": colors.HexColor("#a11f1f"),
}

PILLAR_LABELS = {
    "revenue_growth": "Revenue Growth (YoY)",
    "gross_margin": "Gross Margin",
    "runway": "Cash Runway",
    "burn_multiple": "Burn Multiple",
    "leverage": "Leverage / Debt Coverage",
    "governance": "Governance & Concentration",
}


def _styles():
    # Just the handful of text styles the memo actually uses, built once
    # per call. Nothing fancy -- I wanted this to look like a memo, not a
    # template gallery.
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="MemoTitle", fontSize=17, leading=21, spaceAfter=2,
        textColor=colors.HexColor("#14213d"), fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="MemoSubtitle", fontSize=10, leading=13,
        textColor=colors.HexColor("#555555"), spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=12, leading=15, spaceBefore=14, spaceAfter=6,
        textColor=colors.HexColor("#14213d"), fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="BLUF", fontSize=11, leading=15, spaceAfter=4, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=9.5, leading=13.5, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="Small", fontSize=8, leading=11, textColor=colors.HexColor("#777777")
    ))
    return styles


def generate_memo_pdf(result: ScorecardResult, output_path: str) -> str:
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    )
    story = []
    c = result.company

    cur = c.currency

    def fmt(x):
        # Small helper so every money field in the memo either shows the
        # number with its currency, or plainly says it isn't public --
        # never a blank cell that could be mistaken for zero.
        return f"{cur} {x:,.0f}" if x is not None else "Not publicly disclosed"

    # --- Header ---
    story.append(Paragraph(f"Private Credit Screening Memo — {c.name}", styles["MemoTitle"]))
    ask_line = f"Illustrative facility size: {fmt(c.funding_ask)}" if c.funding_ask else "Retrospective screen of public financials (no live facility)"
    story.append(Paragraph(
        f"Sector: {result.benchmark.sector} &nbsp;|&nbsp; {ask_line} "
        f"&nbsp;|&nbsp; Prepared by: {c.analyst or 'Analyst'}",
        styles["MemoSubtitle"]
    ))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#dddddd"), thickness=0.8))
    story.append(Spacer(1, 8))

    # --- BLUF / Recommendation block ---
    # This is the whole point of putting the rating in a big colored bar at
    # the top instead of at the bottom of a table: whoever's skimming
    # fifteen of these should get the answer without reading a word of body
    # text.
    rating_color = RATING_COLORS.get(result.rating, colors.black)
    bluf_table = Table(
        [[
            Paragraph(f"<b>{result.rating}</b>", ParagraphStyle(
                "RatingBig", fontSize=15, textColor=colors.white, fontName="Helvetica-Bold"
            )),
            Paragraph(
                f"Composite score: <b>{result.composite_score:.2f} / 5.00</b><br/>{result.recommendation}",
                ParagraphStyle("RecText", fontSize=10, textColor=colors.white, leading=14)
            ),
        ]],
        colWidths=[55 * mm, None]
    )
    bluf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rating_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(bluf_table)
    story.append(Spacer(1, 10))

    # --- Scorecard table ---
    story.append(Paragraph("Six-Pillar Scorecard", styles["SectionHeading"]))
    if result.weight_coverage < 0.999:
        # Only show the coverage warning when something's actually missing --
        # no point cluttering a fully-scored memo with a banner that says
        # "100% coverage" nobody needed to be told.
        story.append(Paragraph(
            f"<b>Data coverage: {result.weight_coverage:.0%} of pillar weight.</b> "
            f"{'Pillars without public data: ' + ', '.join(PILLAR_LABELS.get(n, n) for n in result.unscored_pillars) + '.' if result.unscored_pillars else ''} "
            "The composite score below is calculated only from scored pillars, reweighted to sum to 100%; "
            "it is not padded with assumptions for missing fields.",
            ParagraphStyle("DataWarning", fontSize=8.5, leading=12, textColor=colors.HexColor("#a15a1a"), spaceAfter=6)
        ))
    table_data = [["Pillar", "Weight", "Value", "Score", "Commentary"]]
    for p in result.pillars:
        score_display = str(p.score) if p.score is not None else "N/A"
        table_data.append([
            Paragraph(PILLAR_LABELS.get(p.name, p.name), styles["Body"]),
            f"{p.weight:.0%}",
            Paragraph(p.raw_value, styles["Body"]),
            score_display,
            Paragraph(p.commentary, styles["Body"]),
        ])
    # Value and commentary are wrapped in Paragraph() rather than passed as
    # plain strings -- ReportLab won't wrap plain text inside a table cell,
    # it just overflows into the next column. Learned that one the hard way
    # on the first draft of this table.
    score_tbl = Table(table_data, colWidths=[30 * mm, 13 * mm, 42 * mm, 15 * mm, None], repeatRows=1)
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14213d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f6f6")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 4))
    contributions = ", ".join(
        f"{PILLAR_LABELS.get(k, k)} {v:.2f}" for k, v in result.weighted_contribution.items() if v is not None
    )
    story.append(Paragraph(
        "Scores are benchmarked against sector medians and top-quartile figures "
        "(see benchmarks.py and SOURCES.md); governance is analyst-assigned. Weighted contribution "
        f"of each scored pillar to the composite: {contributions}.",
        styles["Small"]
    ))

    # --- Financial snapshot ---
    story.append(Paragraph("Financial Snapshot", styles["SectionHeading"]))
    snap_data = [
        ["Current Revenue/ARR", fmt(c.arr_current)],
        ["Prior Period Revenue/ARR", fmt(c.arr_prior_year)],
        ["Gross Margin", f"{c.gross_margin:.1%}" if c.gross_margin is not None else "Not publicly disclosed"],
        ["Monthly Net Burn", fmt(c.monthly_net_burn)],
        ["Cash on Hand", fmt(c.cash_on_hand)],
        ["Net New Revenue/ARR (TTM)", fmt(c.net_new_arr_ttm)],
        ["Existing Debt", fmt(c.existing_debt) if c.existing_debt else "None identified"],
    ]
    snap_tbl = Table(snap_data, colWidths=[55 * mm, 55 * mm])
    snap_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e5e5")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(snap_tbl)

    # --- Key risks / notes ---
    # These three fields (notes, governance_notes, data_notes) are where
    # all the actual judgment calls live -- the scorecard above is the
    # what, this section is the why. I'd rather a reader skip the table
    # and just read this part than the other way around.
    story.append(Paragraph("Key Risks & Notes", styles["SectionHeading"]))
    risk_text = c.notes or "No additional risk flags beyond those captured in the scorecard above."
    story.append(Paragraph(risk_text, styles["Body"]))
    if c.governance_notes:
        story.append(Paragraph(f"<b>Governance:</b> {c.governance_notes}", styles["Body"]))
    if c.data_notes:
        story.append(Paragraph(f"<b>Data notes:</b> {c.data_notes}", styles["Body"]))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#dddddd"), thickness=0.6))
    story.append(Paragraph(
        "This memo is a decision-support output of a rules-based screening model. "
        "It is not a substitute for full due diligence, legal review, or committee judgement.",
        styles["Small"]
    ))

    doc.build(story)
    return output_path
