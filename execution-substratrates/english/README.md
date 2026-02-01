# English Language Candidate

English prose documentation generated from the Effortless Rulebook using LLM-assisted Natural Language Generation.

## Architecture: Deterministic Structure + Stochastic Content

This substrate follows the same pattern as all other ERB substrates:

```
┌─────────────────────────────────────────────────────────────┐
│                    inject-into-english.py                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. Load rulebook JSON (structured data)                   │
│                          ↓                                  │
│   2. DETERMINISTIC: Create document skeleton                │
│      - Fixed sections: Glossary, Specification, Profiles    │
│      - Fixed headings, tables, formatting                   │
│                          ↓                                  │
│   3. STOCHASTIC (LLM): For EACH piece of content:          │
│      - Call LLM to generate prose for ONE predicate         │
│      - Call LLM to generate prose for ONE candidate         │
│      - Call LLM to generate prose for ONE formula           │
│                          ↓                                  │
│   4. Assemble: Insert LLM outputs into deterministic slots  │
│                          ↓                                  │
│   5. Output: specification.md, glossary.md, profiles.md     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Principle: LLM as Content Generator, Not Structure Generator

**WRONG approach (what we must NOT do):**
```python
# DON'T: Write static prose directly
content = """
HasSyntax means the item has grammar rules.
RequiresParsing means it needs parsing.
"""
```

**CORRECT approach (what we MUST do):**
```python
# DO: Call LLM for each piece of content
for predicate in predicates:
    prompt = f"""
    Given this predicate from the ERB rulebook:
    Name: {predicate['name']}
    Formula: {predicate['formula']}

    Write a 2-3 sentence human-readable explanation of what this predicate means.
    """
    explanation = get_llm_response(prompt)
    glossary[predicate['name']] = explanation
```

## Document Generation Process

### 1. Glossary Generation

For each predicate in the schema:
```
┌────────────────────────────────────────┐
│ Input: predicate name, formula, type   │
│              ↓                         │
│ LLM Prompt: "Explain this predicate    │
│             in plain English..."       │
│              ↓                         │
│ Output: Human-readable definition      │
└────────────────────────────────────────┘
```

### 2. Candidate Profile Generation

For each language candidate:
```
┌────────────────────────────────────────┐
│ Input: candidate data (all fields)     │
│              ↓                         │
│ LLM Prompt: "Given these properties,   │
│             explain why this item      │
│             does/doesn't qualify..."   │
│              ↓                         │
│ Output: Prose explanation paragraph    │
└────────────────────────────────────────┘
```

### 3. Formula Explanation Generation

For each calculated field:
```
┌────────────────────────────────────────┐
│ Input: formula, dependencies           │
│              ↓                         │
│ LLM Prompt: "Explain this formula      │
│             as step-by-step English    │
│             instructions..."           │
│              ↓                         │
│ Output: Algorithm in plain English     │
└────────────────────────────────────────┘
```

## Testing: Round-Trip Verification

The test proves the English is accurate by having an LLM read it back:

```
┌─────────────────────────────────────────────────────────────┐
│                       take-test.py                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. Load the generated English documents                   │
│                          ↓                                  │
│   2. For each candidate in blank-test.json:                │
│      - Feed English spec + candidate data to LLM            │
│      - Ask LLM to compute values based on English rules     │
│                          ↓                                  │
│   3. Write inferred values to test-answers.json            │
│                          ↓                                  │
│   4. Orchestrator compares to answer-key.json              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

If the generated English is clear and accurate, the LLM reader should be able to reproduce the correct computed values.

## Files Generated

| File | Structure | Content Source |
|------|-----------|----------------|
| `specification.md` | Deterministic sections | LLM-generated formula explanations |
| `glossary.md` | Deterministic format | LLM-generated predicate definitions |
| `candidate-profiles.md` | One section per candidate | LLM-generated reasoning for each |

## Why This Matters

This approach ensures:

1. **Reproducibility** - Same rulebook always produces same document structure
2. **Testability** - We can verify the English accurately describes the logic
3. **Traceability** - Each piece of English maps to a specific rulebook element
4. **Consistency** - LLM generates each piece following the same pattern

The English substrate proves that natural language can be a valid "execution substrate" when the prose is generated systematically from structured data.

## Status

Implementation pending - requires LLM integration in inject-into-english.py

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
