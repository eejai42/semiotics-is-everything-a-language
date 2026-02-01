#!/bin/bash
set -e

# take-test.sh for RDF execution substrate
# This script runs the SPARQL-based computation to produce test answers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Delete previous test-answers.json to prevent stale results
rm -f "$SCRIPT_DIR/test-answers.json"

# Step 2: Run the RDF substrate solution to populate answers
# This loads RDF data, executes SPARQL CONSTRUCT queries, and extracts results
python3 "$SCRIPT_DIR/take-test.py"

echo "rdf: test-answers.json populated with SPARQL-computed values"
