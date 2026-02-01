#!/bin/bash

# take-test.sh for yaml execution substrate
# Executes the YAML schema deterministically using Python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Copy blank test template to this folder as test-answers.json
cp "$SCRIPT_DIR/../../testing/blank-test.json" "$SCRIPT_DIR/test-answers.json"

# Step 3: Run YAML substrate to compute calculated fields
python3 "$SCRIPT_DIR/take-test.py"

echo "yaml: test-answers.json computed and saved"
