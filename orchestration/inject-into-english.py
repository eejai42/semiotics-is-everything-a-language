#!/usr/bin/env python3
"""
Generate English documentation from the Effortless Rulebook.

This script runs from /language-candidates/english/ and reads
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
        "English prose documentation from the Effortless Rulebook.\n\n"
        "Future implementation will generate human-readable "
        "specifications, glossaries, and documentation.",
        technology="""**Natural Language Generation (NLG)** transforms structured data into human-readable prose. Unlike templated text, NLG aims to produce fluent, contextually appropriate sentences that read as if written by a human author.

Key characteristics:
- **Template-based**: Simple variable substitution ("The candidate {name} has HasSyntax={value}")
- **Rule-based**: Grammar rules and sentence patterns combined programmatically
- **LLM-assisted**: Modern approaches use language models to produce natural phrasing from structured inputs

ERB English exports would generate:
- **Argument narratives**: "To demonstrate that not everything is a language, consider the following: A Coffee Mug lacks syntax, does not require parsing, and does not serialize meaning..."
- **Candidate profiles**: Prose descriptions of each language candidate explaining why it does or doesn't qualify
- **Glossary entries**: Definitions of predicates like HasSyntax, RequiresParsing, MeaningIsSerialized
- **Executive summaries**: High-level overview of the thesis and supporting evidence

The goal is documentation that non-technical stakeholders can read without understanding formal logic notation."""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
