#!/bin/bash

# take-test.sh for binary execution substrate
# This script runs the binary substrate to produce test answers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
echo "Deleting previous test-answers.json..."
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Copy blank test template to this folder as test-answers.json
echo "Copying blank test template..."
cp "$SCRIPT_DIR/../../testing/blank-test.json" "$SCRIPT_DIR/test-answers.json"

# Step 3: Run the binary substrate solution to populate answers
echo "Running binary substrate test..."
python3 "$SCRIPT_DIR/take-test.py"

echo "binary: test-answers.json populated with computed values"
