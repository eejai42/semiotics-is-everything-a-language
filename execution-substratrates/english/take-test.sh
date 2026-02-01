#!/bin/bash

# take-test.sh for english execution substrate
# This script runs the english substrate to produce test answers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the english substrate solution to populate answers
# The python script handles checking for existing results and prompting
# It will copy blank-test.json only after user confirms (or with --regenerate)
python3 "$SCRIPT_DIR/take-test.py" "$@"
