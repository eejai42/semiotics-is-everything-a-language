# Is Everything a Language?

> A formalized argument that "language" is a testable, computable boundary—not a universal property.

This repository implements a philosophical argument as executable code. The thesis: **not everything is a language**, and we can prove it by defining "language" through testable predicates, then showing that many things fail those tests.

---

## Table of Contents

1. [The Argument](#the-argument)
   - [Part I: Language Can Be Formalized](#part-i-language-can-be-formalized)
   - [Part II: Not Everything Is a Language](#part-ii-not-everything-is-a-language)
   - [Conclusion](#conclusion)
2. [The Predicates](#the-predicates)
3. [The Evaluation Matrix](#the-evaluation-matrix)
4. [The DAG (Inference Levels)](#the-dag-inference-levels)
5. [Execution Layers](#execution-layers)
6. [Quick Start](#quick-start)
7. [Architecture](#architecture)
8. [Transpilers](#transpilers)

---

## The Argument

### Part I: Language Can Be Formalized

**Motivation:** The phrase "everything is a language" is seductive but vacuous. If everything can be "interpreted," then "language" loses meaning. We need a stricter, testable definition.

**The Operational Definition:**

An item **x** is a **Language** if and only if:

```
Language(x) := HasSyntax(x) ∧ RequiresParsing(x) ∧ Meaning_Is_Serialized(x) ∧ IsOntologyDescriptor(x)
```

In plain English:
- **HasSyntax** — It has explicit grammar rules
- **RequiresParsing** — It must be parsed to be understood
- **Meaning_Is_Serialized** — Its meaning can be encoded/stored
- **IsOntologyDescriptor** — It functions as a system for describing things

**Witnesses:** This definition isn't empty. Clear witnesses satisfy it:

| Witness | HasSyntax | RequiresParsing | MeaningSerialized | IsOntologyDescriptor | Language? |
|---------|:---------:|:---------------:|:-----------------:|:--------------------:|:---------:|
| English | ✓ | ✓ | ✓ | ✓ | **Yes** |
| Python  | ✓ | ✓ | ✓ | ✓ | **Yes** |

**Conclusion:** Language *can* be formalized as a computable classification over explicit predicates.

---

### Part II: Not Everything Is a Language

**The Exclusion Principle:** If Language(x) requires all four predicates, then failing *any one* means x is not a language:

```
∀x (¬(HasSyntax(x) ∧ RequiresParsing(x) ∧ Meaning_Is_Serialized(x) ∧ IsOntologyDescriptor(x)) → ¬Language(x))
```

**Counterexamples:**

| Candidate | Why It Fails | Verdict |
|-----------|--------------|:-------:|
| A Chair | No syntax, no parsing, meaning not serialized, not a descriptor | ❌ Not a language |
| A Coffee Mug | No syntax, no parsing, meaning not serialized, not a descriptor | ❌ Not a language |
| A Thunderstorm | No syntax, meaning not serialized, not a descriptor | ❌ Not a language |
| The Mona Lisa | No syntax, no parsing, meaning not serialized | ❌ Not a language |

These things can be *interpreted* (semiotically meaningful), but they don't constitute *language systems*.

**Fuzzy Boundaries — Running Software:**

Running applications present an interesting case. They often *contain* languages (source code, UI grammars, config files) but as executing processes, they behave like dynamic systems rather than static serialized language artifacts:

| Candidate | Contains Language? | Is A Language? | Why? |
|-----------|:------------------:|:--------------:|------|
| Running Calculator App | Yes (code inside) | ❌ No | Dynamic process, not serialized artifact |
| A Game of Fortnite | Yes (code inside) | ❌ No | Interactive system, has identity |
| Editing an XLSX Doc | Yes (Excel formulas) | ❌ No | Runtime state, not the document itself |

**Refinement — Three Categories:**

```
LanguageSystem(x)    — syntax + parsing + serialized meaning + descriptor role
SemioticProcess(x)   — interactive/dynamic meaning production (running apps)
SignVehicle(x)       — object/phenomenon used as a sign (chair, thunderstorm)
```

This gives us a place to classify running apps and games without forcing "language" to swallow everything.

---

### Conclusion

> **Given a formalizable definition of language, not everything is a language; some things are better treated as sign vehicles or semiotic processes, with running applications as a key fuzzy region that benefits from explicit modeling.**

Formally:

```
Formalizable(Language) ∧ ∃x ¬Language(x) ⇒ ¬(EverythingIsALanguage)
```

---

## The Predicates

The evaluation uses 8 predicates—4 core definitional predicates and 4 auxiliary predicates that refine the classification:

### Core Predicates (the definition)

| Predicate | Question | Required for Language? |
|-----------|----------|:----------------------:|
| `has_syntax` | Does it have explicit grammar rules? | ✓ Yes |
| `requires_parsing` | Must it be parsed to extract meaning? | ✓ Yes |
| `meaning_is_serialized` | Can its meaning be encoded/stored? | ✓ Yes |
| `is_ontology_descriptor` | Does it describe/classify things? | ✓ Yes |

### Auxiliary Predicates (refinements)

| Predicate | Question | For Language, should be: |
|-----------|----------|:------------------------:|
| `can_be_held` | Is it a tangible physical object? | ✗ False |
| `has_identity` | Does it have persistent individual identity? | ✗ False |
| `distance_from_concept` | Is it the thing (1) or a description of it (2)? | = 2 |
| `category_contains_language` | Does its category name include "language"? | ✓ True |

---

## The Evaluation Matrix

Here's the punchline—24 candidates evaluated against the predicates:

### ✅ Languages (pass all criteria)

| Candidate | Category | Syntax | Parsing | Serialized | Descriptor | Held | Identity | Distance |
|-----------|----------|:------:|:-------:|:----------:|:----------:|:----:|:--------:|:--------:|
| English | Natural Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| Spoken Words | Natural Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| Sign Language | Natural Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| French | Natural Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| Python | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| JavaScript | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| Binary Code | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| A CSV File | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| A UML File | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| An XLSX Doc | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| An DOCX Doc | Formal Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |
| OWL/RDF/GraphQL/... | Natural Language | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 2 |

### ❌ Not Languages (fail one or more criteria)

| Candidate | Category | Syntax | Parsing | Serialized | Descriptor | Held | Identity | Distance | Fails On |
|-----------|----------|:------:|:-------:|:----------:|:----------:|:----:|:--------:|:--------:|----------|
| A Chair | Physical Object | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | 1 | All core predicates |
| A Coffee Mug | Physical Object | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | 1 | All core predicates |
| A Smartphone | Physical Object | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | 1 | Syntax, parsing, descriptor |
| The Mona Lisa | Physical Object | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | 1 | Syntax, parsing, serialized |
| A Thunderstorm | Physical Event | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | 1 | Syntax, serialized, descriptor |
| Running Calculator App | Running Software | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | 1 | Syntax, serialized, descriptor, identity |
| A Running App | Running Software | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ | 1 | Syntax, descriptor, identity |
| A Game of Fortnite | Running Software | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | 1 | Syntax, serialized, descriptor, identity |
| Editing an XLSX Doc | Running Software | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | 1 | Syntax, parsing, serialized, distance |
| Editing an DOCX Doc | Running Software | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | 1 | Syntax, parsing, serialized, distance |

### 🧪 Falsifiers (test cases for the formula)

| Candidate | Category | Computed Result | Marked As | Mismatch? |
|-----------|----------|:---------------:|:---------:|:---------:|
| Falsifier A | "MISSING: Have you seen this Language?" | ❌ No (category fails) | ❌ No | — |
| Falsifier B | "MISSING: Have you seen this Language?" | ❌ No (multiple failures) | ✓ Yes | **Yes** — marked as language but formula says no |

---

## The DAG (Inference Levels)

Calculated fields are computed in dependency order:

```
Level 0 (Raw Data)
    │
    ├── has_syntax, requires_parsing, meaning_is_serialized, is_ontology_descriptor
    ├── can_be_held, has_identity, distance_from_concept
    ├── category, name, chosen_language_candidate
    │
    ▼
Level 1 (Simple Derivations)
    │
    ├── category_contains_language  ← FIND("language", LOWER(category)) > 0
    ├── has_grammar                 ← CAST(has_syntax AS TEXT)
    ├── relationship_to_concept     ← IF(distance = 1, "IsMirrorOf", "IsDescriptionOf")
    ├── family_feud_question        ← "Is " + name + " a language?"
    │
    ▼
Level 2 (Core Classification)
    │
    └── is_a_family_feud_top_answer ← AND(category_contains_language, has_syntax,
    │                                      NOT(can_be_held), meaning_is_serialized,
    │                                      requires_parsing, is_ontology_descriptor,
    │                                      NOT(has_identity), distance_from_concept = 2)
    │
    ▼
Level 3 (Validation)
    │
    └── family_feud_mismatch        ← IF(computed ≠ marked, report discrepancy)
```

### For Instance: "Is Python a language?"

**Level 0** — Raw facts from the database:
```
name: "Python"
category: "Formal Language"
has_syntax: true
requires_parsing: true
meaning_is_serialized: true
is_ontology_descriptor: true
can_be_held: false
has_identity: false
distance_from_concept: 2
```

**Level 1** — Derived values:
```
category_contains_language: true   ← "formal language" contains "language"
relationship_to_concept: "IsDescriptionOf"  ← distance = 2
family_feud_question: "Is Python a language?"
```

**Level 2** — The verdict:
```
is_a_family_feud_top_answer: true
  ← category_contains_language (✓)
  ← has_syntax (✓)
  ← NOT(can_be_held) (✓)
  ← meaning_is_serialized (✓)
  ← requires_parsing (✓)
  ← is_ontology_descriptor (✓)
  ← NOT(has_identity) (✓)
  ← distance_from_concept = 2 (✓)
```

**Level 3** — Validation:
```
family_feud_mismatch: null   ← computed (true) matches marked (true)
```

---

## Execution Layers

The same logic is implemented in 12+ formats, proving the argument is computable across paradigms.

### For Instance: `is_a_family_feud_top_answer` in Three Languages

**PostgreSQL** ([postgres/02-create-functions.sql](postgres/02-create-functions.sql)):
```sql
CREATE OR REPLACE FUNCTION calc_language_candidates_is_a_family_feud_top_answer(p_id TEXT)
RETURNS BOOLEAN AS $$
  SELECT
    calc_language_candidates_category_contains_language(p_id)
    AND COALESCE(has_syntax, FALSE)
    AND NOT COALESCE(can_be_held, FALSE)
    AND COALESCE(meaning_is_serialized, FALSE)
    AND COALESCE(requires_parsing, FALSE)
    AND COALESCE(is_ongology_descriptor, FALSE)
    AND NOT COALESCE(has_identity, FALSE)
    AND distance_from_concept = 2
  FROM language_candidates WHERE language_candidate_id = p_id;
$$ LANGUAGE SQL STABLE;
```

**Python** ([language-candidates/python/erb_sdk.py](language-candidates/python/erb_sdk.py)):
```python
def calc_is_a_family_feud_top_answer(self) -> bool:
    category_contains_language = self.calc_category_contains_language()
    return (
        category_contains_language
        and (self.has_syntax or False)
        and not (self.can_be_held or False)
        and (self.meaning_is_serialized or False)
        and (self.requires_parsing or False)
        and (self.is_ongology_descriptor or False)
        and not (self.has_identity or False)
        and self.distance_from_concept == 2
    )
```

**RDF/Turtle** ([language-candidates/rdf/schema.ttl](language-candidates/rdf/schema.ttl)):
```turtle
erb:isAFamilyFeudTopAnswer a rdf:Property ;
    rdfs:domain erb:LanguageCandidate ;
    rdfs:range xsd:boolean ;
    rdfs:comment """
        Formula: AND(categoryContainsLanguage, hasSyntax, NOT(canBeHeld),
                     meaningIsSerialized, requiresParsing, isOngologyDescriptor,
                     NOT(hasIdentity), distanceFromConcept = 2)
        DAG Level: 2
    """ .
```

### All Execution Layers

| Layer | Description | Run | README |
|-------|-------------|-----|--------|
| **PostgreSQL** | Source of truth — tables, calc functions, views | [init-db.sh](postgres/init-db.sh) | [README](postgres/README.md) |
| **Python** | SDK with dataclasses and calc methods | [run.sh](language-candidates/python/run.sh) | [README](language-candidates/python/README.md) |
| **Go** | Structs with calculation methods | [run.sh](language-candidates/golang/run.sh) | [README](language-candidates/golang/README.md) |
| **English** | Human-readable specification | — | [specification.md](language-candidates/english/specification.md) |
| **GraphQL** | Schema with resolvers | [run.sh](language-candidates/graphql/run.sh) | [README](language-candidates/graphql/README.md) |
| **RDF/Turtle** | Linked data ontology | [run.sh](language-candidates/rdf/run.sh) | [README](language-candidates/rdf/README.md) |
| **OWL** | Semantic web ontology | [run.sh](language-candidates/owl/run.sh) | [README](language-candidates/owl/README.md) |
| **YAML** | LLM-friendly schema | [run.sh](language-candidates/yaml/run.sh) | [README](language-candidates/yaml/README.md) |
| **CSV** | Tabular field definitions | [run.sh](language-candidates/csv/run.sh) | [README](language-candidates/csv/README.md) |
| **UML** | Entity relationship diagrams | [run.sh](language-candidates/uml/run.sh) | [README](language-candidates/uml/README.md) |
| **DOCX** | Word document export | [run.sh](language-candidates/docx/run.sh) | [README](language-candidates/docx/README.md) |
| **Binary** | Encoded schema representation | [run.sh](language-candidates/binary/run.sh) | [README](language-candidates/binary/README.md) |

---

## Quick Start

### Run the Python SDK

```bash
cd language-candidates/python
./run.sh
```

Or directly:
```bash
python erb_sdk.py
```

Output:
```
Loaded 24 language candidates
Loaded 16 argument steps

First candidate: English
  language_candidate_id: english
  name: English
  is_a_family_feud_top_answer: True
  family_feud_mismatch: None
  ...
```

### Query the PostgreSQL View

```sql
-- See all candidates with computed classification
SELECT name, category, is_a_family_feud_top_answer, family_feud_mismatch
FROM vw_language_candidates
ORDER BY sort_order;

-- Find mismatches between computed and marked
SELECT name, family_feud_mismatch
FROM vw_language_candidates
WHERE family_feud_mismatch IS NOT NULL;
```

---

## Architecture

This project follows the **Effortless Rulebook (ERB)** pattern:

```
Airtable (Source of Truth)
         ↓
effortless-rulebook.json (CMCC format)
         ↓
Code Generation (ssotme transpilers)
         ↓
12+ Execution Layers (all implementing the same logic)
```

For schema details, see [README.SCHEMA.md](README.SCHEMA.md).

---

## Transpilers

The build pipeline uses `ssotme` transpilers to generate all execution layers from the single source of truth. Each transpiler reads from `effortless-rulebook.json` and produces a specific output format.

### Source Sync

| Transpiler | Direction | Description |
|------------|-----------|-------------|
| `airtabletorulebook` | Airtable → JSON | Pulls schema + data from Airtable into [effortless-rulebook.json](effortless-rulebook/effortless-rulebook.json) |
| `rulebooktoairtable` | JSON → Airtable | Pushes local changes back to Airtable (disabled by default) |

### Code Generation

| Transpiler | Output | README |
|------------|--------|--------|
| `rulebooktopostgres` | PostgreSQL DDL (tables, functions, views, policies, data) | [postgres/README.md](postgres/README.md) |
| `rulebooktopython` | Python SDK with dataclasses | [language-candidates/python/README.md](language-candidates/python/README.md) |
| `rulebooktogolang` | Go structs with calc methods | [language-candidates/golang/README.md](language-candidates/golang/README.md) |
| `rulebooktoenglish` | Human-readable specification | [language-candidates/english/README.md](language-candidates/english/README.md) |
| `rulebooktographql` | GraphQL schema + resolvers | [language-candidates/graphql/README.md](language-candidates/graphql/README.md) |
| `rulebooktordf` | RDF/Turtle linked data | [language-candidates/rdf/README.md](language-candidates/rdf/README.md) |
| `rulebooktoowl` | OWL semantic web ontology | [language-candidates/owl/README.md](language-candidates/owl/README.md) |
| `rulebooktoyaml` | YAML schema (LLM-friendly) | [language-candidates/yaml/README.md](language-candidates/yaml/README.md) |
| `rulebooktocsv` | CSV field definitions | [language-candidates/csv/README.md](language-candidates/csv/README.md) |
| `rulebooktouml` | UML entity diagrams | [language-candidates/uml/README.md](language-candidates/uml/README.md) |
| `rulebooktodocx` | Word document export | [language-candidates/docx/README.md](language-candidates/docx/README.md) |
| `rulebooktobinary` | Binary schema encoding | [language-candidates/binary/README.md](language-candidates/binary/README.md) |

### Utility

| Transpiler | Description |
|------------|-------------|
| `init-db` | Runs [postgres/init-db.sh](postgres/init-db.sh) to initialize the database |
| `JsonHbarsTransform` | Generates [README.SCHEMA.md](README.SCHEMA.md) from Handlebars template |

### Running Transpilers

```bash
# Build all transpilers
ssotme -buildall

# Build a specific transpiler
ssotme -build rulebooktopython

# Build with dependencies disabled (faster)
ssotme -build -id
```

See [ssotme.json](ssotme.json) for full configuration.

---

*Generated from [effortless-rulebook.json](effortless-rulebook/effortless-rulebook.json)*
