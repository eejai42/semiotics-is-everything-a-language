#!/usr/bin/env python3
"""
Generate DOCX documents from the Effortless Rulebook.

This script runs from /language-candidates/docx/ and reads
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
        "DOCX document generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate Microsoft Word documents "
        "with formatted specifications and documentation.",
        technology="""**DOCX (Office Open XML)** is Microsoft Word's native format since 2007, standardized as ECMA-376 and ISO/IEC 29500. A `.docx` file is actually a ZIP archive containing XML files for content, styles, relationships, and embedded media.

Key characteristics:
- **Rich formatting**: Headings, tables, lists, fonts, colors, images, and page layout
- **Structured content**: XML-based, enabling programmatic generation via libraries like python-docx, docx4j, or pandoc
- **Track changes & comments**: Supports collaborative review workflows
- **Cross-platform**: Opens in Word, Google Docs, LibreOffice, and most document editors

ERB DOCX exports would generate:
- Formatted specification documents with the logical argument structure
- Tables showing language candidates with their predicate evaluations
- Glossary sections explaining the operational definition of "language"
- Visual highlighting of witnesses, counterexamples, and fuzzy boundary cases"""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
