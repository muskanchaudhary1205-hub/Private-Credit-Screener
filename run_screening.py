#!/usr/bin/env python3
"""
run_screening.py

The entry point -- point this at a JSON file of companies and it scores
each one, prints a one-line summary per company to the console, and drops
a full PDF memo for each into the output folder.

Usage:
    python run_screening.py                          # scores the three sample companies
    python run_screening.py --input data/mine.json    # or your own
    python run_screening.py --output-dir memos        # change where the PDFs land
"""

import argparse
import json
import os
import sys

from credit_screener.scorecard import CompanyFinancials, score_company
from credit_screener.memo import generate_memo_pdf


def load_companies(path: str):
    with open(path, "r") as f:
        raw = json.load(f)
    # json.load() turns JSON null into Python None automatically, which is
    # exactly what CompanyFinancials expects for an undisclosed field --
    # so no extra handling needed here, just unpack each dict straight in.
    return [CompanyFinancials(**entry) for entry in raw]


def main():
    parser = argparse.ArgumentParser(description="Score companies and generate credit memos.")
    parser.add_argument("--input", default="data/sample_companies.json", help="Path to input JSON file")
    parser.add_argument("--output-dir", default="sample_output", help="Directory to write PDF memos to")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    companies = load_companies(args.input)

    print(f"{'Company':<20}{'Sector':<18}{'Score':<8}{'Rating':<26}{'Recommendation'}")
    print("-" * 100)

    for company in companies:
        result = score_company(company)
        print(f"{company.name:<20}{result.benchmark.sector:<18}{result.composite_score:<8}{result.rating:<26}{result.recommendation}")

        # Filenames from company names -- lowercase, spaces to underscores.
        # Good enough for a handful of companies; if this ever needs to run
        # against hundreds, swap in a proper slugify function.
        safe_name = company.name.lower().replace(" ", "_")
        out_path = os.path.join(args.output_dir, f"{safe_name}_credit_memo.pdf")
        generate_memo_pdf(result, out_path)

    print(f"\nPDF memos written to: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
