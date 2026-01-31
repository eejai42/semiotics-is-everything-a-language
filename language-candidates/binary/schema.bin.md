# ERB Schema - Binary Format Specification

*Mirrors the PostgreSQL functions from postgres/02-create-functions.sql*
*Source: effortless-rulebook/effortless-rulebook.json*

## Binary Wire Format

This document specifies a compact binary representation of the ERB schema.

### Header (16 bytes)

```
Offset  Size  Field
------  ----  -----
0x00    4     Magic number: 0x45524253 ("ERBS")
0x04    2     Version: 0x0001
0x06    2     Flags: 0x0000
0x08    4     Entity count
0x0C    4     Reserved
```

### Entity Types

```
0x01 = LanguageCandidate
0x02 = IsEverythingALanguage
```

### Field Types

```
0x00 = null
0x01 = boolean (1 byte: 0x00=false, 0x01=true)
0x02 = integer (4 bytes, big-endian)
0x03 = string (2-byte length prefix + UTF-8 bytes)
```

### LanguageCandidate Record Layout

```
Offset  Size     Field                        Type      DAG Level
------  -------  ---------------------------  --------  ---------
0x00    1        entity_type                  byte      -
0x01    2+N      language_candidate_id        string    0 (raw)
...     2+N      name                         string    0 (raw)
...     2+N      category                     string    0 (raw)
...     1        can_be_held                  boolean   0 (raw)
...     1        meaning_is_serialized        boolean   0 (raw)
...     1        requires_parsing             boolean   0 (raw)
...     1        is_ongology_descriptor       boolean   0 (raw)
...     1        has_syntax                   boolean   0 (raw)
...     1        chosen_language_candidate    boolean   0 (raw)
...     4        sort_order                   integer   0 (raw)
...     1        has_identity                 boolean   0 (raw)
...     4        distance_from_concept        integer   0 (raw)
```

### Calculated Fields (Optional Extension)

When the `INCLUDE_CALC` flag (0x0001) is set:

```
...     1        category_contains_language   boolean   1 (calc)
...     2+N      has_grammar                  string    1 (calc)
...     2+N      relationship_to_concept      string    1 (calc)
...     2+N      family_fued_question         string    1 (calc)
...     1        is_a_family_feud_top_answer  boolean   2 (calc)
...     2+N      family_feud_mismatch         string    3 (calc)
```

### DAG Execution Order for Calculations

When deserializing and computing calculated fields:

```
Level 0: Read all raw fields
Level 1: Compute in any order:
         - category_contains_language = FIND("language", LOWER(category)) > 0
         - has_grammar = CAST(has_syntax AS TEXT)
         - relationship_to_concept = IF(distance_from_concept = 1, "IsMirrorOf", "IsDescriptionOf")
         - family_fued_question = "Is " + name + " a language?"
Level 2: Compute (requires Level 1):
         - is_a_family_feud_top_answer = AND(category_contains_language, has_syntax, ...)
Level 3: Compute (requires Level 2):
         - family_feud_mismatch = IF(mismatch, message, null)
```

### Calculation Functions (Pseudocode)

```
// Level 1
calc_category_contains_language(category):
    IF category IS NULL: RETURN false
    RETURN CONTAINS(LOWERCASE(category), "language")

calc_has_grammar(has_syntax):
    IF has_syntax IS NULL OR has_syntax IS false: RETURN ""
    RETURN "true"

calc_relationship_to_concept(distance_from_concept):
    IF distance_from_concept == 1: RETURN "IsMirrorOf"
    RETURN "IsDescriptionOf"

calc_family_fued_question(name):
    RETURN "Is " + (name OR "") + " a language?"

// Level 2
calc_is_a_family_feud_top_answer(record):
    category_contains_language = calc_category_contains_language(record.category)
    RETURN (
        category_contains_language AND
        (record.has_syntax OR false) AND
        NOT (record.can_be_held OR false) AND
        (record.meaning_is_serialized OR false) AND
        (record.requires_parsing OR false) AND
        (record.is_ongology_descriptor OR false) AND
        NOT (record.has_identity OR false) AND
        record.distance_from_concept == 2
    )

// Level 3
calc_family_feud_mismatch(record):
    is_top_answer = calc_is_a_family_feud_top_answer(record)
    chosen = record.chosen_language_candidate OR false
    IF is_top_answer != chosen:
        is_word = IF is_top_answer THEN "Is" ELSE "Isn't"
        marked_word = IF chosen THEN "Is" ELSE "Is Not"
        RETURN record.name + " " + is_word + " a Family Feud Language, but " +
               marked_word + " marked as a 'Language Candidate.'"
    RETURN NULL
```

### Core Language Definition

```
is_language(record):
    RETURN (
        (record.has_syntax OR false) AND
        (record.requires_parsing OR false) AND
        (record.meaning_is_serialized OR false) AND
        (record.is_ongology_descriptor OR false)
    )
```

### Example Binary (Hex)

```
45 52 42 53  # Magic: "ERBS"
00 01        # Version: 1
00 01        # Flags: INCLUDE_CALC
00 00 00 01  # Entity count: 1
00 00 00 00  # Reserved

01           # Entity type: LanguageCandidate
00 07 65 6E 67 6C 69 73 68  # ID: "english"
00 07 45 6E 67 6C 69 73 68  # Name: "English"
00 10 4E 61 74 75 72 61 6C 20 4C 61 6E 67 75 61 67 65  # Category: "Natural Language"
00           # can_be_held: false
01           # meaning_is_serialized: true
01           # requires_parsing: true
01           # is_ongology_descriptor: true
01           # has_syntax: true
01           # chosen_language_candidate: true
00 00 00 01  # sort_order: 1
00           # has_identity: false
00 00 00 02  # distance_from_concept: 2

# Calculated fields (with INCLUDE_CALC flag)
01           # category_contains_language: true
00 04 74 72 75 65  # has_grammar: "true"
00 0F 49 73 44 65 73 63 72 69 70 74 69 6F 6E 4F 66  # relationship_to_concept: "IsDescriptionOf"
00 19 49 73 20 45 6E 67 6C 69 73 68 20 61 20 6C 61 6E 67 75 61 67 65 3F  # family_fued_question: "Is English a language?"
01           # is_a_family_feud_top_answer: true
00 00        # family_feud_mismatch: null (empty string)
```
