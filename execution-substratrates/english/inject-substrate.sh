#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
SKIP_INJECT=false
for arg in "$@"; do
    case $arg in
        --skip-inject)
            SKIP_INJECT=true
            shift
            ;;
    esac
done

# Inject data into the english substrate (unless --skip-inject)
INJECT_EXIT_CODE=0
if [ "$SKIP_INJECT" = false ]; then
    python3 "$SCRIPT_DIR/inject-into-english.py"
    INJECT_EXIT_CODE=$?
fi

# Run the test for this substrate
# Only pass --regenerate if user chose to regenerate (exit code 0)
# Exit code 2 means user skipped LLM regeneration - skip test too
if [ "$INJECT_EXIT_CODE" = "0" ]; then
    "$SCRIPT_DIR/take-test.sh" --regenerate
elif [ "$INJECT_EXIT_CODE" = "2" ]; then
    echo "Skipping LLM test (user chose not to regenerate)."
else
    echo "Error during injection (exit code $INJECT_EXIT_CODE)"
    exit $INJECT_EXIT_CODE
fi
