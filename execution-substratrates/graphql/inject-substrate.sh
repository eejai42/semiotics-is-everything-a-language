#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Regenerate Python's erb_calc.py from rulebook (shared by GraphQL tests)
echo "=== Regenerating shared erb_calc.py from rulebook ==="
python3 "$SCRIPT_DIR/../python/inject-into-python.py"

# Inject data into the graphql substrate (generates schema.graphql and resolvers.js)
echo "=== Generating GraphQL schema and resolvers ==="
python3 "$SCRIPT_DIR/inject-into-graphql.py"

# Run the test for this substrate
"$SCRIPT_DIR/take-test.sh"
