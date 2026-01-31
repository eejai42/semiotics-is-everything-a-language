#!/usr/bin/env python3
"""
Generate UML diagrams from the Effortless Rulebook.

This script runs from /language-candidates/uml/ and reads
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
        "UML diagram generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate PlantUML or Mermaid "
        "class diagrams, entity-relationship diagrams, and sequence diagrams.",
        technology="""**UML (Unified Modeling Language)** is the ISO/IEC 19501 standard for software modeling diagrams. For code generation, text-based UML tools like PlantUML and Mermaid allow diagrams to be version-controlled, diffed, and generated programmatically.

Key characteristics:
- **Text-to-diagram**: PlantUML and Mermaid convert plain text to rendered diagrams
- **Multiple diagram types**: Class, entity-relationship, sequence, state, activity diagrams
- **Embeddable**: Markdown, wikis, and documentation systems render these inline
- **Diff-friendly**: Text representations enable meaningful version control

ERB UML exports (PlantUML class diagram):
```plantuml
@startuml
class LanguageCandidate {
  +id: string
  +name: string
  +hasSyntax: boolean
  +requiresParsing: boolean
  +meaningIsSerialized: boolean
  +isOntologyDescriptor: boolean
  --
  +calcTopFamilyFeudAnswer(): boolean
  +calcFamilyFeudMismatch(): string
}

class ArgumentStep {
  +id: string
  +argumentName: string
  +statement: string
  +formalization: string
}

ArgumentStep --> LanguageCandidate : relatedCandidate
@enduml
```"""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
