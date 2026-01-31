#!/usr/bin/env python3
"""
Generate Go (Golang) representation from the Effortless Rulebook.

This script runs from /language-candidates/golang/ and reads
the rulebook from ../../effortless-rulebook/effortless-rulebook.json
"""

import sys
from pathlib import Path

# Add orchestration directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent))

from shared import load_rulebook, write_readme, get_candidate_name_from_cwd


def main():
    candidate_name = get_candidate_name_from_cwd()
    print(f"Generating {candidate_name} language candidate...")

    # Load the rulebook (for future use)
    try:
        rulebook = load_rulebook()
        print(f"Loaded rulebook with {len(rulebook)} top-level keys")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        rulebook = None

    # Write placeholder README
    write_readme(
        candidate_name,
        "Go (Golang) code generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate Go structs, "
        "interfaces, and validation functions."
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
