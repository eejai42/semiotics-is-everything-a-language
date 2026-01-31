# Python SDK - Language Candidates Rulebook

Python implementation of the ERB calculation functions.

## Technology

**Python** is a dynamically-typed, interpreted language known for readability and extensive libraries. Its class system with `@property` decorators and dataclasses makes it natural for implementing ERB's entity/calculation pattern.

Key characteristics:
- **Classes with methods**: Python classes group data and behavior; `self` provides instance access
- **Dynamic typing**: No compile-time type checking, but type hints available for documentation
- **JSON support**: Built-in `json` module for loading/dumping rulebook data
- **Dataclasses**: `@dataclass` decorator auto-generates `__init__`, `__repr__`, etc.

The Python SDK mirrors the PostgreSQL calc functions as class methods, enabling the same DAG of calculations to run in-memory without a database. Useful for data analysis, scripting, and rapid prototyping.

## Files

- `erb_sdk.py` - Entity classes with calc functions mirroring PostgreSQL

## Usage

```python
from erb_sdk import LanguageCandidate, load_from_rulebook, is_language

# Load from rulebook
candidates, arguments = load_from_rulebook("../../effortless-rulebook/effortless-rulebook.json")

# Use calculated fields (DAG-aware)
for c in candidates:
    view = c.to_view()  # All raw + calculated fields
    print(f"{view['name']}: is_language={view['is_a_family_feud_top_answer']}")

# Or use individual calc methods
candidate = candidates[0]
print(candidate.calc_category_contains_language())
print(candidate.calc_is_a_family_feud_top_answer())
print(candidate.calc_family_feud_mismatch())
```

## DAG Execution Order

```
Level 0: Raw fields (from rulebook)
Level 1: category_contains_language, has_grammar, relationship_to_concept, family_fued_question
Level 2: is_a_family_feud_top_answer (depends on category_contains_language)
Level 3: family_feud_mismatch (depends on is_a_family_feud_top_answer)
```

## Source

Mirrors: `postgres/02-create-functions.sql`
Generated from: `effortless-rulebook/effortless-rulebook.json`
