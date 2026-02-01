#!/bin/bash

# take-test.sh for graphql execution substrate
# This script runs the GraphQL resolver logic to compute test answers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Run the Python script to compute answers using resolver functions
python3 take-test.py
