#!/bin/bash
set -e
cd "$(dirname "$0")"

# Run the SDK demo
echo "=== Go ERB SDK ==="
go run erb_sdk.go main.go
