#!/bin/bash
set -e

# take-test.sh for UML execution substrate
# This script runs the OCL-based computation to produce test answers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Run the UML substrate solution to populate answers
# This loads the model, evaluates OCL expressions, and extracts results
python3 "$SCRIPT_DIR/take-test.py"

echo "uml: test-answers.json populated with OCL-computed values"
