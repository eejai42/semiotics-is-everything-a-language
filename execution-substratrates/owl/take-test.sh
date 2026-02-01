#!/bin/bash

# take-test.sh for owl execution substrate
# This script runs the SHACL reasoner to compute derived values

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
echo "Deleting previous test-answers.json..."
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Install dependencies if needed (auto-handled by take-test.py)
# pip install rdflib pyshacl --quiet

# Step 3: Run the OWL/SHACL substrate solution to populate answers
echo "Running OWL substrate test (SHACL reasoner)..."
python3 "$SCRIPT_DIR/take-test.py"

echo "owl: test-answers.json populated with computed values"
