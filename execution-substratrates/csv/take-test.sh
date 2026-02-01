#!/bin/bash

# take-test.sh for csv execution substrate
# This script reads the CSV file and produces test-answers.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Copy blank test template to this folder as test-answers.json
cp "$SCRIPT_DIR/../../testing/blank-test.json" "$SCRIPT_DIR/test-answers.json"

# Step 2: Run the Python script to read from language_candidates.csv and populate test-answers.json
python3 take-test.py
