# ERB Specification - English Prose Implementation

*Mirrors the PostgreSQL functions from postgres/02-create-functions.sql*
*Source: effortless-rulebook/effortless-rulebook.json*

## Overview

This specification defines how to evaluate whether a candidate item qualifies as a **language** according to the Effortless Rulebook.

## Core Language Definition

A candidate **x** is classified as a **Language** if and only if it satisfies all of the following predicates:

1. **HasSyntax(x)** - The item has explicit grammar rules
2. **RequiresParsing(x)** - The item needs parsing to be interpreted
3. **Meaning_Is_Serialized(x)** - The item's meaning can be represented in serialized form
4. **IsOngologyDescriptor(x)** - The item functions as an ontology/descriptor system

**Formal Definition:**
```
Language(x) := HasSyntax(x) ∧ RequiresParsing(x) ∧ Meaning_Is_Serialized(x) ∧ IsOngologyDescriptor(x)
```

## Entities

### 1. Language Candidate

A **Language Candidate** is any item being evaluated for language classification.

#### Raw Fields (Level 0)

| Field | Type | Description |
|-------|------|-------------|
| `language_candidate_id` | string | Primary key identifier |
| `name` | string | Display name of the candidate |
| `category` | string | Classification category (Natural Language, Formal Language, Physical Object, Running Software) |
| `can_be_held` | boolean | Can this be physically held? (Tangibility predicate) |
| `meaning_is_serialized` | boolean | Can meaning be represented in serialized form? |
| `requires_parsing` | boolean | Does it need parsing to be interpreted? |
| `is_ongology_descriptor` | boolean | Does it function as an ontology/descriptor system? |
| `has_syntax` | boolean | Does it have explicit grammar rules? |
| `chosen_language_candidate` | boolean | Manually marked as a "true" language candidate |
| `sort_order` | integer | Display ordering |
| `has_identity` | boolean | Does it have persistent identity? |
| `distance_from_concept` | integer | 1=Mirror (is the thing), 2=Description (describes the thing) |

#### Calculated Fields

Calculated fields follow a **DAG (Directed Acyclic Graph)** execution order to ensure dependencies are resolved.

---

**Level 1: Simple Calculations**

These calculations depend only on raw fields.

##### Category Contains Language

*Mirrors: `calc_language_candidates_category_contains_language()`*

**Question:** Does the category string contain the word "language"?

**Formula:** `FIND("language", LOWER(category)) > 0`

**Algorithm:**
1. Take the `category` field value
2. Convert to lowercase
3. Search for the substring "language"
4. Return `true` if found, `false` otherwise

---

##### Has Grammar

*Mirrors: `calc_language_candidates_has_grammar()`*

**Question:** What is the string representation of the syntax status?

**Formula:** `CAST(has_syntax AS TEXT)`

**Algorithm:**
1. Take the `has_syntax` field value
2. If `true`, return the string "true"
3. If `false` or `null`, return an empty string ""

---

##### Relationship To Concept

*Mirrors: `calc_language_candidates_relationship_to_concept()`*

**Question:** What is the semantic relationship to the language concept?

**Formula:** `IF(distance_from_concept = 1, "IsMirrorOf", "IsDescriptionOf")`

**Algorithm:**
1. Take the `distance_from_concept` field value
2. If equal to 1, return "IsMirrorOf" (the item IS the thing)
3. Otherwise, return "IsDescriptionOf" (the item DESCRIBES the thing)

---

##### Family Feud Question

*Mirrors: `calc_language_candidates_family_fued_question()`*

**Question:** What is the Family Feud style question for this candidate?

**Formula:** `"Is " & name & " a language?"`

**Algorithm:**
1. Take the `name` field value
2. Concatenate: "Is " + name + " a language?"
3. Return the resulting question string

---

**Level 2: Dependent Calculations**

These calculations depend on Level 1 calculations.

##### Is A Family Feud Top Answer

*Mirrors: `calc_language_candidates_is_a_family_feud_top_answer()`*

**Question:** Would this be a "top answer" on Family Feud for "Is X a language?"

**Dependencies:** `category_contains_language` (Level 1)

**Formula:**
```
AND(
  category_contains_language,
  has_syntax,
  NOT(can_be_held),
  meaning_is_serialized,
  requires_parsing,
  is_ongology_descriptor,
  NOT(has_identity),
  distance_from_concept = 2
)
```

**Algorithm:**
1. First, compute `category_contains_language` (Level 1)
2. Then check ALL of the following conditions are true:
   - `category_contains_language` is true
   - `has_syntax` is true
   - `can_be_held` is false (NOT tangible)
   - `meaning_is_serialized` is true
   - `requires_parsing` is true
   - `is_ongology_descriptor` is true
   - `has_identity` is false (NOT persistent)
   - `distance_from_concept` equals 2 (is a description)
3. If ALL conditions pass, return `true`
4. If ANY condition fails, return `false`

---

**Level 3: Higher-Order Calculations**

These calculations depend on Level 2 calculations.

##### Family Feud Mismatch

*Mirrors: `calc_language_candidates_family_feud_mismatch()`*

**Question:** Is there a mismatch between the computed classification and the manual classification?

**Dependencies:** `is_a_family_feud_top_answer` (Level 2)

**Formula:**
```
IF(is_a_family_feud_top_answer != chosen_language_candidate,
  name & " " &
  IF(is_a_family_feud_top_answer, "Is", "Isn't") &
  " a Family Feud Language, but " &
  IF(chosen_language_candidate, "Is", "Is Not") &
  " marked as a 'Language Candidate.'",
  NULL
)
```

**Algorithm:**
1. First, compute `is_a_family_feud_top_answer` (Level 2)
2. Compare to `chosen_language_candidate` (raw field)
3. If they match, return `null` (no mismatch)
4. If they differ, construct a mismatch message:
   - Example: "Falsifier A Is a Family Feud Language, but Is Not marked as a 'Language Candidate.'"

---

### 2. Is Everything A Language (Argument Steps)

This entity captures the philosophical argument about whether "everything is a language."

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_everything_a_language_id` | string | Primary key |
| `name` | string | Identifier (e.g., NEIAL-001) |
| `argument_name` | string | Branch: "LanguageCanBeFormalized" or "NotEverythingIsALanguage" |
| `argument_category` | string | Role: Definition, Premise, Conclusion, Example, Observation, Refinement |
| `step_type` | string | Subtype of the argument step |
| `statement` | string | Natural language argument text |
| `formalization` | string | Formal logic notation |
| `related_candidate_id` | string | FK to language candidate |
| `evidence_from_rulebook` | string | Predicate values supporting the argument |
| `notes` | string | Additional context |

---

## DAG Execution Order Summary

```
Level 0 (Raw):     All base table fields
                        ↓
Level 1 (Simple):  category_contains_language
                   has_grammar
                   relationship_to_concept
                   family_fued_question
                        ↓
Level 2 (Dependent): is_a_family_feud_top_answer
                        ↓
Level 3 (Higher):  family_feud_mismatch
```

---

## Implementation Notes

When implementing this specification in any language:

1. **Respect the DAG** - Always compute Level 1 before Level 2, and Level 2 before Level 3
2. **Handle nulls** - Use COALESCE/default values as shown in the formulas
3. **String matching** - Category contains language check should be case-insensitive
4. **Mirror PostgreSQL** - The source of truth is `postgres/02-create-functions.sql`
