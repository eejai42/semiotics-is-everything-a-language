#!/usr/bin/env python3
"""
Generate Binary representation from the Effortless Rulebook.

This script runs from /language-candidates/binary/ and reads
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
        "Binary format generation from the Effortless Rulebook.\n\n"
        "Future implementation will generate compact binary "
        "serialization formats (e.g., Protocol Buffers, MessagePack).",
        technology="""**Binary serialization** represents data as compact byte sequences rather than human-readable text. Unlike JSON or XML, binary formats encode type information and values directly as bytes, eliminating parsing overhead and reducing payload size by 2-10x.

Key characteristics:
- **Schema-driven**: Formats like Protocol Buffers and Thrift require schema definitions (`.proto`, `.thrift` files) that compile to code
- **Self-describing vs. Schema-required**: MessagePack and CBOR include type markers inline; Protobuf requires the schema to decode
- **Backward compatibility**: Well-designed schemas support field addition/removal without breaking existing readers

Common formats for ERB export:
- **Protocol Buffers** - Google's format, excellent tooling, strict schemas
- **MessagePack** - "JSON in binary", schema-optional, widely supported
- **CBOR** - IETF standard (RFC 8949), optimized for constrained environments"""
    )

    print(f"Done generating {candidate_name} candidate.")


if __name__ == "__main__":
    main()
