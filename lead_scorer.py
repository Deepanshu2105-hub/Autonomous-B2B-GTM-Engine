#!/usr/bin/env python3
"""Score and prioritize ICP leads from a CSV file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

import pandas as pd
from pandas import DataFrame

# =============================================================================
# EDITABLE ICP SCORING CONFIGURATION
# Keywords are matched case-insensitively against Persona and Scraped Context.
# Each keyword contributes its points at most once per lead.
# =============================================================================
SCORING_WEIGHTS: Final[dict[str, dict[str, int]]] = {
    "high_intent": {
        "founder": 40,
        "ceo": 40,
        "hiring": 35,
        "scaling": 35,
        "raised funding": 50,
    },
    "medium_intent": {
        "marketing manager": 15,
        "growing": 15,
    },
    "negative_intent": {
        "student": -50,
        "looking for a job": -50,
        "freelance": -50,
    },
}

REQUIRED_COLUMNS: Final[tuple[str,...]] = (
    "Company",
    "Website",
    "Persona",
    "Persona Email",
    "Scraped Context",
)

class LeadScorer:
    """Ingest, score, tier, sort, and export leads from a CSV file."""

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        weights: dict[str, dict[str, int]] | None = None,
    ) -> None:
        """Set file paths and scoring weights; reject invalid configurations."""
        self.input_path = input_path
        self.output_path = output_path
        self.weights = weights if weights is not None else SCORING_WEIGHTS

        if not self.weights or any(
            not isinstance(score, int)
            for group in self.weights.values()
            for score in group.values()
        ):
            raise ValueError(
                "Scoring weights must contain keyword groups with integer scores."
            )

    def load(self) -> DataFrame:
        """Read the input CSV and verify that required columns are present."""
        if not self.input_path.is_file():
            raise FileNotFoundError(f"Input CSV does not exist: {self.input_path}")

        frame = pd.read_csv(self.input_path)
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]

        if missing:
            raise ValueError(
                f"Input CSV is missing required column(s): {', '.join(missing)}"
            )
        if frame.empty:
            raise ValueError("Input CSV contains no lead rows.")

        return frame

    def _score_text(self, persona: object, context: object) -> int:
        """Return additive points for matching keywords in a lead's text fields."""
        persona_text = "" if pd.isna(persona) else str(persona)
        context_text = "" if pd.isna(context) else str(context)
        text = f"{persona_text} {context_text}".casefold()

        return sum(
            points
            for terms in self.weights.values()
            for keyword, points in terms.items()
            if keyword.casefold() in text
        )

    @staticmethod
    def _tier(score: int) -> str:
        """Assign a tier based on a lead's score."""
        if score >= 60:
            return "Tier 1 (Hot)"
        if score >= 25:
            return "Tier 2 (Warm)"
        return "Tier 3 (Cold)"

    def score(self, frame: DataFrame) -> DataFrame:
        """Return a copy of the input with scores and tiers, sorted by score."""
        result = frame.copy()
        result["Lead Score"] = [
            self._score_text(persona, context)
            for persona, context in zip(result["Persona"], result["Scraped Context"])
        ]
        result["Lead Tier"] = result["Lead Score"].map(self._tier)

        # Preserve input order when two leads have the same score.
        result["_original_order"] = range(len(result))
        result = result.sort_values(
            ["Lead Score", "_original_order"],
            ascending=[False, True],
            kind="stable",
        )
        return result.drop(columns="_original_order").reset_index(drop=True)

    def export(self, frame: DataFrame) -> None:
        """Write the prioritized leads to CSV, creating the output directory."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(self.output_path, index=False, encoding="utf-8")

    @staticmethod
    def print_summary(frame: DataFrame, output_path: Path) -> None:
        """Print tier totals and a preview of the three highest-scoring leads."""
        tier_counts = frame["Lead Tier"].value_counts()

        print("\n=== ICP Lead Scoring Report ===")
        print(f"Total leads scored: {len(frame):,}")
        print("Tier breakdown:")
        for tier in ("Tier 1 (Hot)", "Tier 2 (Warm)", "Tier 3 (Cold)"):
            print(f"  {tier}: {int(tier_counts.get(tier, 0)):,}")

        preview_columns = ["Company", "Persona", "Lead Score", "Lead Tier"]
        print("\nTop 3 hottest leads:")
        print(frame[preview_columns].head(3).to_string(index=False))
        print(f"\nExported prioritized leads to: {output_path.resolve()}")

    def run(self) -> DataFrame:
        """Run the complete load, score, export, and reporting workflow."""
        scored = self.score(self.load())
        self.export(scored)
        self.print_summary(scored, self.output_path)
        return scored

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Score and prioritize ICP leads from a CSV file."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path("v2_ready_leads.csv"),
        help="Input CSV (default: v2_ready_leads.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("v2_prioritized_leads.csv"),
        help="Output CSV (default: v2_prioritized_leads.csv)",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """Run the command-line application and report expected errors cleanly."""
    args = parse_args(argv)

    try:
        LeadScorer(args.input, args.output).run()
    except (OSError, pd.errors.ParserError, UnicodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
