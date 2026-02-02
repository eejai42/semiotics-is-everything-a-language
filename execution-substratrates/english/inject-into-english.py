#!/usr/bin/env python3
"""
Generate English documentation from the Effortless Rulebook.

ARCHITECTURE: Deterministic Structure + Stochastic Content
==========================================================
- DETERMINISTIC: Document skeleton, sections, headings, formatting
- STOCHASTIC: LLM generates prose in ONE BIG GULP per document

This mirrors how other substrates work - the structure is fixed,
but the content is generated/injected. Using larger context windows
with full documents produces better results than chunked generation.
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, get_candidate_name_from_cwd, handle_clean_arg

# =============================================================================
# MODEL TIER CONFIGURATION
# =============================================================================
# Control the "intelligence" of the LLM to see how it affects reliability.
# Deterministic substrates always score 100%; LLM substrates vary by model.

MODEL_TIERS = {
    "smart": {
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
        "description": "Most capable models - highest accuracy, slowest, most expensive"
    },
    "medium": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "description": "Balanced models - good accuracy, moderate speed/cost"
    },
    "cheap": {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-haiku-20240307",
        "description": "Budget models - faster/cheaper but less reliable"
    },
}

# Default tier (can be overridden by --tier flag or LLM_TIER env var)
DEFAULT_TIER = os.environ.get("LLM_TIER", "medium")  # gpt-4o-mini - balanced accuracy with some variability
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")


def get_model_for_tier(tier: str, provider: str) -> str:
    """Get the model name for a given tier and provider."""
    if tier not in MODEL_TIERS:
        print(f"Warning: Unknown tier '{tier}', using 'medium'")
        tier = "medium"
    return MODEL_TIERS[tier].get(provider, MODEL_TIERS[tier]["openai"])


def get_llm_response(prompt: str, provider: str = None, tier: str = None) -> str:
    """Get a response from the LLM with configurable model tier."""
    provider = provider or DEFAULT_PROVIDER
    tier = tier or DEFAULT_TIER
    model = get_model_for_tier(tier, provider)

    # Log first 2 lines of prompt
    prompt_lines = prompt.split('\n')
    print("=" * 60)
    print(f"CALLING {provider.upper()} ({model})...")
    print("PROMPT (first 2 lines):")
    for line in prompt_lines[:2]:
        print(f"  {line[:100]}")
    print(f"  ... ({len(prompt_lines)} total lines, {len(prompt)} chars)")
    print("=" * 60)
    sys.stdout.flush()

    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Higher temp for more variability
                max_tokens=8192,  # Adequate output budget
            )
            response_text = response.choices[0].message.content
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=8192,  # Adequate output budget
                temperature=0.7,  # Higher temp for more variability
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Log first 2 lines of response
        response_lines = response_text.split('\n')
        print("=" * 60)
        print("RESPONSE (first 2 lines):")
        for line in response_lines[:2]:
            print(f"  {line[:100]}")
        print(f"  ... ({len(response_lines)} total lines, {len(response_text)} chars)")
        print("=" * 60)
        sys.stdout.flush()

        return response_text
    except Exception as e:
        print(f"Warning: LLM call failed: {e}")
        return f"[LLM generation failed: {e}]"


def preview_response(response: str, context: str = "", max_chars: int = 120) -> None:
    """Print a preview of the LLM response (first 1-2 lines) for progress tracking."""
    # Get first meaningful line(s)
    lines = [l.strip() for l in response.split('\n') if l.strip()]
    preview = ""
    for line in lines[:2]:
        if len(preview) + len(line) < max_chars:
            preview += (" " if preview else "") + line
        else:
            preview += (" " if preview else "") + line[:max_chars - len(preview) - 3] + "..."
            break

    if context:
        print(f"    [{context}] {preview}")
    else:
        print(f"    → {preview}")


# =============================================================================
# LLM CONTENT GENERATORS (One Big Gulp per Document)
# =============================================================================
# Instead of making many small LLM calls, we generate entire documents in one call.
# Larger context windows produce more coherent and accurate results.

def generate_glossary_content(schema: list, provider: str = None, tier: str = None) -> dict:
    """Generate all glossary definitions in ONE LLM call."""
    raw_fields = [f for f in schema if f.get("type") == "raw"]
    calc_fields = [f for f in schema if f.get("type") == "calculated"]

    # Build the schema description for the prompt
    schema_json = json.dumps({
        "raw_fields": [{"name": f.get("name"), "datatype": f.get("datatype")} for f in raw_fields],
        "calculated_fields": [{"name": f.get("name"), "datatype": f.get("datatype"), "formula": f.get("formula")} for f in calc_fields]
    }, indent=2)

    prompt = f"""You are writing glossary entries for a technical rulebook about language classification.

Here is the complete schema of predicates:

{schema_json}

For EACH predicate (both raw and calculated), write a clear, concise definition (2-3 sentences) explaining:
1. What this predicate measures or represents
2. How it's used in determining if something is a "language"

Use plain English that a non-technical reader can understand.

Return your response as a JSON object where keys are predicate names and values are the definitions.
Example format:
{{
  "HasSyntax": "This predicate indicates whether...",
  "DistanceFromConcept": "This numeric value measures..."
}}

IMPORTANT: Include ALL predicates from both raw_fields and calculated_fields.
Return ONLY valid JSON, no markdown code blocks.
"""
    response = get_llm_response(prompt, provider, tier)
    preview_response(response, "Glossary definitions")

    # Parse the JSON response
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print(f"    Warning: Could not parse glossary JSON: {e}")
    return {}


def generate_overview_content(rulebook: dict, provider: str = None, tier: str = None) -> str:
    """Generate an overview/summary explaining the goal and structure of the model."""
    # Extract key information from the rulebook
    neial_data = rulebook.get("IsEverythingALanguage", {}).get("data", [])
    schema = rulebook.get("LanguageCandidates", {}).get("schema", [])
    candidates = rulebook.get("LanguageCandidates", {}).get("data", [])

    # Build a summary of the argument structure
    argument_steps = []
    for step in neial_data:
        argument_steps.append({
            "name": step.get("Name"),
            "type": step.get("StepType"),
            "statement": step.get("Statement"),
            "formalization": step.get("Formalization")
        })

    # Build schema summary
    raw_fields = [f.get("name") for f in schema if f.get("type") == "raw" and f.get("name") not in ["LanguageCandidateId", "Name", "Category", "SortOrder"]]
    calc_fields = [{"name": f.get("name"), "formula": f.get("formula")} for f in schema if f.get("type") == "calculated"]

    # Count statistics
    language_count = sum(1 for c in candidates if c.get("TopFamilyFeudAnswer", False))
    non_language_count = len(candidates) - language_count

    prompt = f"""You are writing an executive overview for a formal rulebook system.

The system formalizes the definition of "language" to answer: "Is everything a language?"

Here is the argument structure from the rulebook:
{json.dumps(argument_steps, indent=2)}

Here are the raw predicates (input properties):
{json.dumps(raw_fields, indent=2)}

Here are the calculated fields (derived properties):
{json.dumps(calc_fields, indent=2)}

Statistics:
- Total candidates evaluated: {len(candidates)}
- Classified as languages: {language_count}
- Classified as NOT languages: {non_language_count}

Write a clear, comprehensive overview (3-4 paragraphs) that explains:
1. The GOAL/OBJECTIVE: Why this system exists (to avoid "everything is a language" while still formalizing what a language IS)
2. The CORE THESIS: What the operational definition of language is
3. The MODEL STRUCTURE: How the predicates work together (raw inputs → calculated outputs → classification)
4. The KEY INSIGHT: Why this matters (distinguishing language systems from sign vehicles and semiotic processes)

Use plain English. Be concise but thorough. Do NOT use bullet points or lists - write flowing prose.
Return ONLY the overview text, no headers or formatting.
"""
    response = get_llm_response(prompt, provider, tier)
    preview_response(response, "Overview summary")
    return response


def generate_specification_content(calc_fields: list, provider: str = None, tier: str = None) -> dict:
    """Generate all formula explanations in ONE LLM call."""
    formulas_json = json.dumps([
        {"name": f.get("name"), "formula": f.get("formula")}
        for f in calc_fields
    ], indent=2)

    prompt = f"""You are writing documentation that explains formulas in plain English.

Here are ALL the calculated fields with their formulas:

{formulas_json}

For EACH calculated field, write step-by-step instructions (as a numbered list) explaining exactly how to compute the value.
Be precise and unambiguous - someone should be able to follow these instructions manually.
Do NOT use code or technical notation. Use plain English only.
Keep each explanation under 100 words.

Return your response as a JSON object where keys are field names and values are the step-by-step instructions.
Example format:
{{
  "FieldName1": "1. First, check if...\\n2. Then, calculate...",
  "FieldName2": "1. Look at the value of...\\n2. If it equals..."
}}

Return ONLY valid JSON, no markdown code blocks.
"""
    response = get_llm_response(prompt, provider, tier)
    preview_response(response, "Formula explanations")

    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print(f"    Warning: Could not parse specification JSON: {e}")
    return {}


def generate_profiles_content(candidates: list, provider: str = None, tier: str = None) -> dict:
    """Generate all candidate profiles in ONE LLM call."""
    # Build a summary of each candidate
    candidates_summary = []
    for c in candidates:
        summary = {
            "name": c.get("Name"),
            "category": c.get("Category"),
            "is_language": c.get("TopFamilyFeudAnswer", False),
            "properties": {k: v for k, v in c.items()
                          if k not in ["LanguageCandidateId", "Name", "Category", "SortOrder",
                                       "FamilyFuedQuestion", "TopFamilyFeudAnswer", "FamilyFeudMismatch",
                                       "HasGrammar", "RelationshipToConcept"]}
        }
        candidates_summary.append(summary)

    candidates_json = json.dumps(candidates_summary, indent=2)

    prompt = f"""You are writing brief profiles explaining why items do or don't qualify as "languages" under a formal definition.

The formal definition of Language requires ALL of:
- HasSyntax = true
- RequiresParsing = true
- Meaning_Is_Serialized = true
- IsOngologyDescriptor = true
- CanBeHeld = false
- HasIdentity = false
- DistanceFromConcept = 2

Here are ALL the candidates to evaluate:

{candidates_json}

For EACH candidate, write a 2-3 sentence explanation of WHY they do or don't qualify as a language.
Focus on the key predicates that determine the outcome.
Use plain English. Do NOT use bullet points or formatting within each profile.

Return your response as a JSON object where keys are candidate names and values are the profile explanations.
Example format:
{{
  "Python": "Python qualifies as a language because it has syntax, requires parsing...",
  "A Rock": "A rock does not qualify as a language because it cannot be parsed..."
}}

Return ONLY valid JSON, no markdown code blocks.
"""
    response = get_llm_response(prompt, provider, tier)
    preview_response(response, "Candidate profiles")

    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print(f"    Warning: Could not parse profiles JSON: {e}")
    return {}


# =============================================================================
# DOCUMENT GENERATORS (Deterministic Structure + Stochastic Content)
# =============================================================================
# Each document is generated with ONE LLM call for all content.
# The structure is deterministic; the LLM fills in the prose.

def generate_glossary(rulebook: dict, provider: str = None, tier: str = None) -> str:
    """Generate glossary.md with LLM-generated definitions (one big gulp)."""
    schema = rulebook.get("LanguageCandidates", {}).get("schema", [])
    raw_fields = [f for f in schema if f.get("type") == "raw"]
    calc_fields = [f for f in schema if f.get("type") == "calculated"]

    print("  Generating all definitions in one call...")
    definitions = generate_glossary_content(schema, provider, tier)

    lines = [
        "# ERB Glossary - Predicate Definitions",
        "",
        "Human-readable definitions for all predicates in the Effortless Rulebook.",
        "",
        "---",
        "",
        "## Raw Predicates (Input Fields)",
        "",
    ]

    for field in raw_fields:
        name = field.get("name", "Unknown")
        datatype = field.get("datatype", "unknown")
        definition = definitions.get(name, f"[Definition for {name} not generated]")

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"**Type:** {datatype}")
        lines.append("")
        lines.append(definition)
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Calculated Predicates (Computed Fields)")
    lines.append("")

    for field in calc_fields:
        name = field.get("name", "Unknown")
        datatype = field.get("datatype", "unknown")
        formula = field.get("formula", "")
        definition = definitions.get(name, f"[Definition for {name} not generated]")

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"**Type:** {datatype}")
        lines.append(f"**Formula:** `{formula}`")
        lines.append("")
        lines.append(definition)
        lines.append("")
        lines.append("---")
        lines.append("")

    print(f"    Generated {len(definitions)} definitions")
    return "\n".join(lines)


def generate_specification(rulebook: dict, provider: str = None, tier: str = None) -> str:
    """Generate specification.md with LLM-generated formula explanations (one big gulp)."""
    schema = rulebook.get("LanguageCandidates", {}).get("schema", [])
    calc_fields = [f for f in schema if f.get("type") == "calculated"]
    raw_fields = [f for f in schema if f.get("type") == "raw"]

    # Generate overview first
    print("  Generating overview summary...")
    overview = generate_overview_content(rulebook, provider, tier)

    print("  Generating all formula explanations in one call...")
    explanations = generate_specification_content(calc_fields, provider, tier)

    # Build raw predicates list for display
    raw_predicate_names = [f.get("name") for f in raw_fields
                          if f.get("name") not in ["LanguageCandidateId", "Name", "Category", "SortOrder"]]

    lines = [
        "# ERB Specification - Language Classification Rulebook",
        "",
        "---",
        "",
        "## Overview",
        "",
        overview,
        "",
        "---",
        "",
        "## Model Structure",
        "",
        "The model operates on a set of raw predicates (input properties) that are evaluated for each candidate,",
        "which then feed into calculated fields that derive the final classification.",
        "",
        "### Raw Predicates (Inputs)",
        "",
        "These are the fundamental properties evaluated for each candidate:",
        "",
    ]

    # Add raw predicates as a bullet list
    for name in raw_predicate_names:
        field = next((f for f in raw_fields if f.get("name") == name), {})
        datatype = field.get("datatype", "unknown")
        lines.append(f"- **{name}** ({datatype})")

    lines.extend([
        "",
        "### Calculated Fields (Derived)",
        "",
        "These fields are computed from the raw predicates:",
        "",
    ])

    # Add calculated fields as a bullet list
    for field in calc_fields:
        name = field.get("name", "Unknown")
        lines.append(f"- **{name}**")

    lines.extend([
        "",
        "---",
        "",
        "## Core Language Definition",
        "",
        "An item qualifies as a **Language** if and only if ALL of these are true:",
        "",
        "1. HasSyntax = true",
        "2. RequiresParsing = true",
        "3. HasLinearDecodingPressure = true",
        "4. StableOntologyReference = true",
        "5. CanBeHeld = false",
        "6. HasIdentity = false",
        "7. DistanceFromConcept = 2",
        "",
        "---",
        "",
        "## Calculated Field Instructions",
        "",
    ])

    for field in calc_fields:
        name = field.get("name", "Unknown")
        formula = field.get("formula", "")
        explanation = explanations.get(name, f"[Explanation for {name} not generated]")

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"**Formula:** `{formula}`")
        lines.append("")
        lines.append("**How to compute:**")
        lines.append("")
        lines.append(explanation)
        lines.append("")
        lines.append("---")
        lines.append("")

    print(f"    Generated {len(explanations)} explanations")
    return "\n".join(lines)


def generate_candidate_profiles(rulebook: dict, provider: str = None, tier: str = None) -> str:
    """Generate candidate-profiles.md with LLM-generated explanations (one big gulp)."""
    candidates = rulebook.get("LanguageCandidates", {}).get("data", [])
    sorted_candidates = sorted(candidates, key=lambda x: x.get("SortOrder", 999))

    # Calculate statistics
    language_count = sum(1 for c in candidates if c.get("TopFamilyFeudAnswer", False))
    non_language_count = len(candidates) - language_count

    # Group by category for summary
    categories = {}
    for c in candidates:
        cat = c.get("Category", "Unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "languages": 0}
        categories[cat]["total"] += 1
        if c.get("TopFamilyFeudAnswer", False):
            categories[cat]["languages"] += 1

    print("  Generating all candidate profiles in one call...")
    profiles = generate_profiles_content(sorted_candidates, provider, tier)

    lines = [
        "# Language Candidate Profiles",
        "",
        "This document evaluates various candidates against the formal definition of 'language' established in the ERB (Effortless Rulebook) specification.",
        "",
        "## Summary",
        "",
        f"**Total candidates evaluated:** {len(candidates)}",
        f"**Classified as languages:** {language_count}",
        f"**Classified as NOT languages:** {non_language_count}",
        "",
        "### By Category",
        "",
    ]

    # Add category breakdown
    for cat, stats in sorted(categories.items()):
        lines.append(f"- **{cat}**: {stats['languages']}/{stats['total']} qualify as languages")

    lines.extend([
        "",
        "---",
        "",
        "## Classification Criteria",
        "",
        "To qualify as a **language**, a candidate must satisfy ALL of the following:",
        "",
        "- HasSyntax = true",
        "- RequiresParsing = true",
        "- HasLinearDecodingPressure = true",
        "- StableOntologyReference = true",
        "- CanBeHeld = false",
        "- HasIdentity = false",
        "- DistanceFromConcept = 2",
        "",
        "---",
        "",
        "## Individual Profiles",
        "",
    ])

    for candidate in sorted_candidates:
        name = candidate.get("Name", "Unknown")
        category = candidate.get("Category", "Unknown")
        is_language = candidate.get("TopFamilyFeudAnswer", False)
        profile = profiles.get(name, f"[Profile for {name} not generated]")

        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"**Category:** {category}")
        lines.append(f"**Classification:** {'✓ Language' if is_language else '✗ Not a Language'}")
        lines.append("")
        lines.append(profile)
        lines.append("")
        lines.append("---")
        lines.append("")

    print(f"    Generated {len(profiles)} profiles")
    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def print_tier_info(tier: str, provider: str):
    """Print information about the selected model tier."""
    model = get_model_for_tier(tier, provider)
    tier_info = MODEL_TIERS.get(tier, {})
    print(f"\n{'='*60}")
    print(f"LLM Configuration")
    print(f"{'='*60}")
    print(f"  Provider: {provider}")
    print(f"  Tier:     {tier} ({tier_info.get('description', '')})")
    print(f"  Model:    {model}")
    print(f"{'='*60}\n")


def main():
    # Define generated files for this substrate
    # NOTE: LLM-generated files (markdown docs, test-answers.json) are NOT cleaned
    # because they take significant time to regenerate. Only test-results.md is cleaned
    # (it's quick to regenerate from the existing test-answers.json).
    GENERATED_FILES = [
        'test-results.md',  # Quick to regenerate - just grading existing answers
    ]

    # Handle --clean argument (check before argparse to avoid conflicts)
    if '--clean' in sys.argv:
        if handle_clean_arg(GENERATED_FILES, "English substrate: Preserves LLM-generated files (they take time to rebuild). Only removes test-results.md."):
            return

    parser = argparse.ArgumentParser(
        description="Generate English documentation from the Effortless Rulebook",
        epilog="""
Model Tiers:
  smart   - Most capable (gpt-4o, claude-sonnet) - highest accuracy
  medium  - Balanced (gpt-4o-mini, claude-haiku) - good accuracy [default]
  cheap   - Budget (gpt-3.5-turbo) - faster but less reliable

Environment Variables:
  LLM_TIER     - Default tier (smart/medium/cheap)
  LLM_PROVIDER - Default provider (openai/anthropic)
        """
    )
    parser.add_argument(
        "--tier", "-t",
        choices=["smart", "medium", "cheap"],
        default=DEFAULT_TIER,
        help=f"Model intelligence tier (default: {DEFAULT_TIER})"
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "anthropic"],
        default=DEFAULT_PROVIDER,
        help=f"LLM provider (default: {DEFAULT_PROVIDER})"
    )
    parser.add_argument(
        "--list-tiers",
        action="store_true",
        help="List available model tiers and exit"
    )
    parser.add_argument(
        "--regenerate", "-r",
        action="store_true",
        help="Force regeneration of all LLM content without prompting"
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip interactive prompts (use with --regenerate to auto-run, or alone to skip LLM calls)"
    )

    args = parser.parse_args()

    if args.list_tiers:
        print("\nAvailable Model Tiers:")
        print("=" * 60)
        for tier_name, tier_info in MODEL_TIERS.items():
            print(f"\n  {tier_name}:")
            print(f"    {tier_info.get('description', '')}")
            print(f"    OpenAI:    {tier_info.get('openai', 'N/A')}")
            print(f"    Anthropic: {tier_info.get('anthropic', 'N/A')}")
        print()
        return 0

    candidate_name = get_candidate_name_from_cwd()

    # Check if output files already exist
    output_files = ["glossary.md", "specification.md", "candidate-profiles.md"]
    existing_files = [f for f in output_files if Path(f).exists()]

    if existing_files and not args.regenerate:
        print(f"\nExisting output files found: {', '.join(existing_files)}")
        if args.no_prompt:
            print("Skipping LLM regeneration (use --regenerate to force).")
            return 2  # Exit code 2 = skipped by user choice (not an error)

        # Check if stdin is a terminal for interactive prompts
        if not sys.stdin.isatty():
            print("Non-interactive mode detected. Skipping LLM regeneration (use --regenerate to force).")
            return 2  # Exit code 2 = skipped (not an error)

        sys.stdout.flush()
        response = input("Re-run all LLM prompts? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print("Skipping LLM regeneration. Use --regenerate to force.")
            return 2  # Exit code 2 = skipped by user choice (not an error)

    print(f"Generating {candidate_name} substrate (LLM-assisted)...")

    # Show configuration
    print_tier_info(args.tier, args.provider)

    # Load the rulebook
    try:
        rulebook = load_rulebook()
        print(f"Loaded rulebook with {len(rulebook)} top-level keys")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Generate glossary (ONE LLM call for all definitions)
    print("\n=== Generating Glossary ===")
    glossary_content = generate_glossary(rulebook, args.provider, args.tier)
    with open("glossary.md", 'w', encoding='utf-8') as f:
        f.write(glossary_content)
    print("  Created glossary.md")

    # Generate specification (ONE LLM call for all formula explanations)
    print("\n=== Generating Specification ===")
    spec_content = generate_specification(rulebook, args.provider, args.tier)
    with open("specification.md", 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("  Created specification.md")

    # Generate candidate profiles (ONE LLM call for all profiles)
    print("\n=== Generating Candidate Profiles ===")
    profiles_content = generate_candidate_profiles(rulebook, args.provider, args.tier)
    with open("candidate-profiles.md", 'w', encoding='utf-8') as f:
        f.write(profiles_content)
    print("  Created candidate-profiles.md")

    print(f"\n{'='*60}")
    print(f"Done generating {candidate_name} substrate.")
    print(f"  Tier: {args.tier} | Provider: {args.provider}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
