#!/usr/bin/env python3
"""
Generate GraphQL schema from the Effortless Rulebook.

This script runs from /language-candidates/graphql/ and reads
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
        "GraphQL schema generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate GraphQL types, "
        "queries, mutations, and resolvers.",
        technology="""**GraphQL** is a query language and runtime for APIs developed by Facebook (2012, open-sourced 2015). Unlike REST's fixed endpoints, GraphQL lets clients request exactly the fields they need in a single query, with strong typing enforced by a schema.

Key characteristics:
- **Schema-first**: Types, queries, and mutations are defined in SDL (Schema Definition Language)
- **Hierarchical queries**: Clients can traverse relationships in a single request
- **Strong typing**: Every field has a type; the schema serves as a contract and documentation
- **Introspection**: Clients can query the schema itself to discover available types and fields

ERB GraphQL exports would generate:
```graphql
type LanguageCandidate {
  id: ID!
  name: String
  hasSyntax: Boolean
  requiresParsing: Boolean
  meaningIsSerialized: Boolean
  isOngologyDescriptor: Boolean
  topFamilyFeudAnswer: Boolean  # Calculated
  category: String
}

type Query {
  languageCandidates: [LanguageCandidate!]!
  languageCandidate(id: ID!): LanguageCandidate
  argumentSteps: [ArgumentStep!]!
}
```"""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
