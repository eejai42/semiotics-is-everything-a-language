#!/usr/bin/env python3
"""
GraphQL Substrate Test Runner

This script reads blank-test.json and computes all calculated fields
using the shared erb_calc.py library (same as Python and YAML substrates),
producing test-answers.json.

The resolvers.js file contains the same logic for GraphQL runtime,
but for testing we use the shared Python library to ensure consistency.
"""

import json
import os
import sys
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent

# Add Python substrate directory to path for shared library
python_substrate_dir = script_dir / ".." / "python"
sys.path.insert(0, str(python_substrate_dir))

from erb_calc import compute_all_calculated_fields


def main():
    blank_test_path = script_dir / '..' / '..' / 'testing' / 'blank-test.json'
    answers_path = script_dir / 'test-answers.json'

    # Load blank test data
    with open(blank_test_path, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    print(f"GraphQL substrate: Processing {len(candidates)} candidates...")

    # Compute answers for each candidate using shared library
    computed = []
    for candidate in candidates:
        computed.append(compute_all_calculated_fields(candidate))

    # Save test answers
    with open(answers_path, 'w', encoding='utf-8') as f:
        json.dump(computed, f, indent=2)

    print(f"GraphQL substrate: Saved results to {answers_path}")


if __name__ == "__main__":
    main()
