#!/bin/bash

# take-test.sh for golang execution substrate
# Runs the Go SDK to compute test answers from blank-test.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Run the Go test runner to compute answers
go run erb_sdk.go main.go take-test
