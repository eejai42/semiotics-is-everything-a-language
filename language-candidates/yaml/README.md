# YAML Schema - Language Candidates Rulebook

Clean, tight schema representation for LLM consumption. No data, just structure.

## Technology

**YAML (YAML Ain't Markup Language)** is a human-readable data serialization format that uses indentation for structure. It's widely used for configuration files, CI/CD pipelines, and as a more readable alternative to JSON.

Key characteristics:
- **Indentation-based**: Structure defined by whitespace, no braces or brackets required
- **Superset of JSON**: Any valid JSON is valid YAML
- **Comments**: Supports `#` comments, unlike JSON
- **Anchors & aliases**: Can reference and reuse values within a document

The YAML schema serves as a bridge between the JSON rulebook and code generation. LLMs can consume this compact schema representation to generate SDKs in any target language without needing the full data payload.

## Files

- `schema.yaml` - Entity definitions, field types, and calculation DAG

## Purpose

This YAML schema serves as:
1. Human-readable documentation of the data model
2. LLM-friendly schema for code generation
3. Reference for implementing SDKs in other languages

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
