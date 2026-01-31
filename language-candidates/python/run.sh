#!/bin/bash
set -e
cd "$(dirname "$0")"

# Run the SDK demo
echo "=== Python ERB SDK ==="
python3 erb_sdk.py
