#!/usr/bin/env python3
"""
Python Substrate Test Runner
=============================
Loads blank-test.json, computes all calculated fields using erb_calc.py,
and saves the results to test-answers.json.

This script uses the shared erb_calc.py library which is also used by
the YAML substrate to ensure identical calculation logic.
"""

import json
import os
import sys

# Add current directory to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from erb_calc import compute_all_calculated_fields


def main():
    # Input: test-answers.json (already copied from blank-test.json by take-test.sh)
    input_path = os.path.join(script_dir, "test-answers.json")
    output_path = os.path.join(script_dir, "test-answers.json")

    # Load test data
    with open(input_path, 'r') as f:
        records = json.load(f)

    print(f"Python substrate: Processing {len(records)} records...")

    # Compute all calculated fields for each record
    computed_records = []
    for record in records:
        computed = compute_all_calculated_fields(record)
        computed_records.append(computed)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(computed_records, f, indent=2)

    print(f"Python substrate: Saved results to {output_path}")


if __name__ == "__main__":
    main()
