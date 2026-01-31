#!/usr/bin/env python3
"""
Generate CSV representation from the Effortless Rulebook.

This script runs from /language-candidates/csv/ and reads
the rulebook from ../../effortless-rulebook/effortless-rulebook.json
"""

import sys
from pathlib import Path

# Add orchestration directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent))

from shared import load_rulebook, write_readme, get_candidate_name_from_cwd


def main():
    candidate_name = get_candidate_name_from_cwd()
    print(f"Generating {candidate_name} language candidate...")

    # Load the rulebook (for future use)
    try:
        rulebook = load_rulebook()
        print(f"Loaded rulebook with {len(rulebook)} top-level keys")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        rulebook = None

    # Write placeholder README
    write_readme(
        candidate_name,
        "CSV file generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate tabular CSV exports "
        "of entities, relationships, and metadata.",
        technology="""**CSV (Comma-Separated Values)** is a plain-text tabular format defined by RFC 4180. Each line represents a record, with fields separated by commas. Despite its simplicity, CSV remains the universal interchange format for spreadsheets, databases, and data analysis tools.

Key characteristics:
- **Universal compatibility**: Excel, Google Sheets, pandas, R, SQL imports all support CSV natively
- **Human-readable**: Can be opened in any text editor for inspection
- **Flat structure**: Best for denormalized, single-table exports; relationships require multiple files or embedded IDs
- **No type information**: All values are strings; consumers must infer or specify types

ERB CSV exports would produce:
- `language_candidates.csv` - One row per candidate with all predicate columns
- `is_everything_a_language.csv` - One row per argument step with formalization and evidence"""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
