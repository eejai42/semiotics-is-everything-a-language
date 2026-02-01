#!/bin/bash

# take-test.sh for python execution substrate
# Executes the Python substrate to compute calculated fields

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Copy blank test template to this folder as test-answers.json
cp "$SCRIPT_DIR/../../testing/blank-test.json" "$SCRIPT_DIR/test-answers.json"

# Step 3: Run Python substrate to compute calculated fields
python3 "$SCRIPT_DIR/take-test.py"

echo "python: test-answers.json computed and saved"
