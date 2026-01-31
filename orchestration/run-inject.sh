#!/bin/bash
# Wrapper script to run inject-into-*.py scripts
# Usage: ./run-inject.sh <target>
# Example: ./run-inject.sh python

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <target>"
    echo "Example: $0 python"
    exit 1
fi

SCRIPT="${SCRIPT_DIR}/inject-into-${TARGET}.py"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: Script not found: $SCRIPT"
    exit 1
fi

python3 "$SCRIPT"
