# Plan: Dynamic Formula Injection for Golang, GraphQL, Python, and YAML

## Executive Summary

The current implementations of these 4 substrates are **broken** because they have **hardcoded field names** (`MeaningIsSerialized`, `IsOngologyDescriptor`) that were renamed in the rulebook to (`HasLinearDecodingPressure`, `StableOntologyReference`).

The **root cause** is that these substrates don't actually inject from the rulebook - they have manually written calculation code that must be updated whenever the schema changes.

The **solution** is to follow the pattern established by:
- **XLSX** - Dynamically evaluates formulas from rulebook
- **OWL** - Parses formula AST and compiles to SPARQL
- **PostgreSQL** - Generates SQL functions from rulebook formulas

---

## Architecture Pattern (Source of Truth)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  effortless-rulebook.json                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ LanguageCandidates.schema[]:                                    │   │
│  │   - name: "TopFamilyFeudAnswer"                                 │   │
│  │     type: "calculated"                                          │   │
│  │     formula: "=AND({{HasSyntax}}, NOT({{CanBeHeld}}), ...)"    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     inject-into-{lang}.py     │
                    │  1. Load rulebook             │
                    │  2. Parse formulas → AST      │
                    │  3. Compile AST → target code │
                    │  4. Write generated file      │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │erb_calc.py│   │erb_sdk.go │   │resolvers.js│
            │(GENERATED)│   │(GENERATED)│   │(GENERATED) │
            └───────────┘   └───────────┘   └───────────┘
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │take-test  │   │take-test  │   │take-test  │
            │(SCAFFOLD) │   │(SCAFFOLD) │   │(SCAFFOLD) │
            └───────────┘   └───────────┘   └───────────┘
```

**Key principle:** The `take-test` scripts are **scaffolding** that:
- Load JSON data
- Import the generated calculation library
- Iterate over records and call calculation functions
- Write test-answers.json

The calculation logic lives in the **generated** files, not the test runners.

---

## Shared Infrastructure: Formula Parser

The OWL substrate already has a complete formula parser (`inject-into-owl.py` lines 42-347). We should **extract this to `orchestration/formula_parser.py`** so all substrates can reuse it.

### Formula Parser Components

```python
# orchestration/formula_parser.py

# AST Node Types
@dataclass
class LiteralBool(ASTNode): value: bool
@dataclass
class LiteralInt(ASTNode): value: int
@dataclass
class LiteralString(ASTNode): value: str
@dataclass
class FieldRef(ASTNode): name: str  # e.g., "HasSyntax"
@dataclass
class BinaryOp(ASTNode): op: str, left: ASTNode, right: ASTNode
@dataclass
class UnaryOp(ASTNode): op: str, operand: ASTNode
@dataclass
class FuncCall(ASTNode): name: str, args: List[ASTNode]
@dataclass
class Concat(ASTNode): parts: List[ASTNode]

# Main API
def parse_formula(formula_text: str) -> ASTNode
def get_field_references(ast: ASTNode) -> List[str]  # Extract all {{FieldName}} refs
```

---

## Substrate 1: Python (`execution-substratrates/python/`)

### Current State
- `inject-into-python.py` - **STUB** (only writes README)
- `erb_calc.py` - **MANUALLY WRITTEN** with hardcoded field names
- `take-test.py` - Imports `erb_calc.py` and calls `compute_all_calculated_fields()`

### Target State
- `inject-into-python.py` - **GENERATES** `erb_calc.py` from rulebook
- `erb_calc.py` - **GENERATED** (overwritten on each inject)
- `take-test.py` - **UNCHANGED** (it's already correct scaffolding)

### Implementation Plan

#### Step 1: Create Python Code Generator

The injector will generate Python functions like:

```python
# erb_calc.py (GENERATED - DO NOT EDIT)
# Generated from: effortless-rulebook/effortless-rulebook.json

def calc_family_fued_question(name):
    """Formula: ="Is " & {{Name}} & " a language?" """
    return f"Is {name or ''} a language?"

def calc_top_family_feud_answer(
    has_syntax, can_be_held, has_linear_decoding_pressure,
    requires_parsing, stable_ontology_reference, has_identity,
    distance_from_concept
):
    """Formula: =AND({{HasSyntax}}, NOT({{CanBeHeld}}), ...) """
    return (
        (has_syntax is True)
        and (can_be_held is not True)
        and (has_linear_decoding_pressure is True)
        and (requires_parsing is True)
        and (stable_ontology_reference is True)
        and (has_identity is not True)
        and (distance_from_concept == 2)
    )

# ... more calc_* functions ...

def compute_all_calculated_fields(record: dict) -> dict:
    """Compute all calculated fields for a record."""
    result = dict(record)

    # Level 1 calculations
    result['family_fued_question'] = calc_family_fued_question(
        record.get('name')
    )
    # ... etc ...

    return result
```

#### Step 2: AST to Python Compiler

```python
def compile_to_python(ast: ASTNode) -> str:
    """Compile an AST node to Python expression."""
    if isinstance(ast, LiteralBool):
        return 'True' if ast.value else 'False'
    if isinstance(ast, LiteralString):
        return repr(ast.value)
    if isinstance(ast, FieldRef):
        return to_snake_case(ast.name)  # HasSyntax -> has_syntax
    if isinstance(ast, FuncCall):
        if ast.name == 'AND':
            parts = [compile_to_python(arg) for arg in ast.args]
            return '(' + ' and '.join(parts) + ')'
        if ast.name == 'NOT':
            return f'(not ({compile_to_python(ast.args[0])}))'
        if ast.name == 'IF':
            cond = compile_to_python(ast.args[0])
            then_val = compile_to_python(ast.args[1])
            else_val = compile_to_python(ast.args[2]) if len(ast.args) > 2 else 'None'
            return f'({then_val} if {cond} else {else_val})'
    # ... etc
```

#### Step 3: Update inject-into-python.py

```python
def main():
    rulebook = load_rulebook()
    tables = get_tables(rulebook)

    # Generate erb_calc.py
    code = generate_python_calc_module(tables)
    Path('erb_calc.py').write_text(code)

    # Update README
    write_readme(...)
```

### Files Changed
| File | Action |
|------|--------|
| `orchestration/formula_parser.py` | **NEW** - Shared parser |
| `python/inject-into-python.py` | **REWRITE** - Full generator |
| `python/erb_calc.py` | **GENERATED** - No manual edits |
| `python/take-test.py` | **UNCHANGED** |

---

## Substrate 2: YAML (`execution-substratrates/yaml/`)

### Current State
- `inject-substrate.sh` - Just runs tests (no generation)
- `schema.yaml` - **MANUALLY WRITTEN** with hardcoded field names
- `take-test.py` - Imports Python's `erb_calc.py`

### Target State
- `inject-into-yaml.py` - **NEW** - Generates `schema.yaml` from rulebook
- `schema.yaml` - **GENERATED** (overwritten on each inject)
- `take-test.py` - **UNCHANGED** (it correctly uses Python's erb_calc)

### Implementation Plan

YAML is documentation-focused. The injector generates a schema that documents:
- All raw and calculated fields
- Their datatypes
- Their formulas (as comments)
- DAG dependencies

The test runner already uses Python's `erb_calc.py`, so once Python is fixed, YAML will also work.

```yaml
# schema.yaml (GENERATED - DO NOT EDIT)
# Generated from: effortless-rulebook/effortless-rulebook.json

entities:
  LanguageCandidate:
    raw_fields:
      has_linear_decoding_pressure:  # RENAMED from meaning_is_serialized
        type: boolean
        nullable: true
      stable_ontology_reference:      # RENAMED from is_ongology_descriptor
        type: boolean
        nullable: true
      # ...

    calculated_fields:
      top_family_feud_answer:
        type: boolean
        depends_on: [has_syntax, can_be_held, has_linear_decoding_pressure, ...]
        formula: |
          AND({{HasSyntax}}, NOT({{CanBeHeld}}), {{HasLinearDecodingPressure}}, ...)
```

### Files Changed
| File | Action |
|------|--------|
| `yaml/inject-into-yaml.py` | **NEW** - Schema generator |
| `yaml/inject-substrate.sh` | **UPDATE** - Call inject-into-yaml.py |
| `yaml/schema.yaml` | **GENERATED** |
| `yaml/take-test.py` | **UNCHANGED** |

---

## Substrate 3: Golang (`execution-substratrates/golang/`)

### Current State
- `inject-into-golang.py` - **STUB** (only writes README)
- `erb_sdk.go` - **MANUALLY WRITTEN** with hardcoded field names
- `main.go` - Test runner that uses erb_sdk.go

### Target State
- `inject-into-golang.py` - **GENERATES** `erb_calc.go` from rulebook
- `erb_calc.go` - **GENERATED** - Contains calc functions
- `erb_types.go` - **GENERATED** - Contains struct definitions
- `main.go` - **UPDATED** - Imports generated code

### Implementation Plan

#### Step 1: AST to Go Compiler

```go
// Generated function example:
// CalcTopFamilyFeudAnswer computes: =AND({{HasSyntax}}, NOT({{CanBeHeld}}), ...)
func CalcTopFamilyFeudAnswer(
    hasSyntax *bool,
    canBeHeld *bool,
    hasLinearDecodingPressure *bool,
    requiresParsing *bool,
    stableOntologyReference *bool,
    hasIdentity *bool,
    distanceFromConcept *int,
) bool {
    return boolVal(hasSyntax) &&
        !boolVal(canBeHeld) &&
        boolVal(hasLinearDecodingPressure) &&
        boolVal(requiresParsing) &&
        boolVal(stableOntologyReference) &&
        !boolVal(hasIdentity) &&
        (distanceFromConcept != nil && *distanceFromConcept == 2)
}
```

#### Step 2: Generate Type Definitions

```go
// erb_types.go (GENERATED)
type LanguageCandidate struct {
    LanguageCandidateID         string  `json:"language_candidate_id"`
    Name                        *string `json:"name"`
    HasLinearDecodingPressure   *bool   `json:"has_linear_decoding_pressure"`
    StableOntologyReference     *bool   `json:"stable_ontology_reference"`
    // ... all fields from schema
}
```

#### Step 3: Update inject-into-golang.py

The injector will:
1. Parse all schemas from rulebook
2. Generate `erb_types.go` with struct definitions
3. Generate `erb_calc.go` with calculation functions
4. Generate `erb_view.go` with the view struct and ToView() method

### Files Changed
| File | Action |
|------|--------|
| `golang/inject-into-golang.py` | **REWRITE** - Full generator |
| `golang/erb_types.go` | **NEW/GENERATED** - Type definitions |
| `golang/erb_calc.go` | **NEW/GENERATED** - Calculation functions |
| `golang/erb_view.go` | **NEW/GENERATED** - View and ToView() |
| `golang/erb_sdk.go` | **DELETE** - Replaced by generated files |
| `golang/main.go` | **UPDATE** - Use generated code |

---

## Substrate 4: GraphQL (`execution-substratrates/graphql/`)

### Current State
- `inject-into-graphql.py` - Generates schema.graphql dynamically, BUT `generate_resolvers()` has **HARDCODED** calculation logic
- `resolvers.js` - **GENERATED** but from hardcoded template
- `take-test.py` - Has **DUPLICATED** hardcoded calculation logic

### Target State
- `inject-into-graphql.py` - Generates BOTH schema.graphql AND resolvers.js dynamically
- `resolvers.js` - **GENERATED** with dynamic field names
- `take-test.py` - Imports and uses resolvers.js (or regenerated Python equivalent)

### Implementation Plan

#### Step 1: AST to JavaScript Compiler

```javascript
// resolvers.js (GENERATED)
/**
 * CalcTopFamilyFeudAnswer
 * Formula: =AND({{HasSyntax}}, NOT({{CanBeHeld}}), ...)
 */
function calcTopFamilyFeudAnswer(candidate) {
  return (
    (candidate.hasSyntax === true) &&
    (candidate.canBeHeld !== true) &&
    (candidate.hasLinearDecodingPressure === true) &&  // DYNAMIC!
    (candidate.requiresParsing === true) &&
    (candidate.stableOntologyReference === true) &&     // DYNAMIC!
    (candidate.hasIdentity !== true) &&
    (candidate.distanceFromConcept === 2)
  );
}
```

#### Step 2: Update generate_resolvers()

Instead of hardcoded strings, iterate over calculated fields and compile formulas:

```python
def generate_resolvers(rulebook):
    lines = [header]

    for table_name, table_def in rulebook.items():
        for field in table_def.get('schema', []):
            if field.get('type') == 'calculated':
                formula = field.get('formula')
                ast = parse_formula(formula)
                js_code = compile_to_javascript(ast)

                lines.append(f'function calc{field["name"]}(candidate) {{')
                lines.append(f'  return {js_code};')
                lines.append('}')

    return '\n'.join(lines)
```

#### Step 3: Fix take-test.py

The test runner should either:
- **Option A**: Import resolvers.js via Node subprocess
- **Option B**: Generate a Python equivalent from the same AST
- **Option C (recommended)**: Share the Python erb_calc.py (like YAML does)

### Files Changed
| File | Action |
|------|--------|
| `graphql/inject-into-graphql.py` | **REWRITE** - Dynamic resolvers |
| `graphql/resolvers.js` | **GENERATED** |
| `graphql/take-test.py` | **UPDATE** - Use shared Python calc |

---

## Implementation Order

### Phase 1: Shared Infrastructure
1. Extract formula parser from OWL to `orchestration/formula_parser.py`
2. Add `compile_to_python()`, `compile_to_go()`, `compile_to_javascript()` functions
3. Test parser with all existing formulas in rulebook

### Phase 2: Python Substrate (Foundation)
1. Rewrite `inject-into-python.py` to use formula parser
2. Generate `erb_calc.py` dynamically
3. Verify tests pass

### Phase 3: YAML Substrate (Depends on Python)
1. Create `inject-into-yaml.py` to generate schema.yaml
2. Verify tests pass (uses Python's erb_calc.py)

### Phase 4: GraphQL Substrate
1. Update `inject-into-graphql.py` with dynamic resolver generation
2. Update `take-test.py` to use shared Python calc
3. Verify tests pass

### Phase 5: Golang Substrate
1. Rewrite `inject-into-golang.py` with Go code generation
2. Split into `erb_types.go`, `erb_calc.go`, `erb_view.go`
3. Update `main.go`
4. Verify tests pass

---

## Testing Strategy

After each phase, run:

```bash
cd orchestration
./orchestrate.sh
```

This runs all substrates and compares their test-answers.json against the answer key.

**Success criteria:** All 4 substrates should produce identical results to:
- `testing/answer-key.json`
- Working substrates (xlsx, owl, postgres, rdf, etc.)

---

## Risk Mitigation

### Formula Complexity
Some formulas are complex (nested IF, AND with NOT, string concatenation). The OWL parser already handles these. Risk is LOW.

### Go Type Safety
Go requires explicit types and nil checks. The generator must handle:
- `*bool` vs `bool`
- Nil checks with helper functions like `boolVal()`
- Proper JSON struct tags

### JavaScript Quirks
JavaScript truthiness differs from Python. Must use explicit `=== true` and `!== true` comparisons.

---

## Success Metrics

1. **Zero hardcoded field names** in any generated file
2. **Rename test**: Change a field name in rulebook → re-run inject → tests still pass
3. **Add field test**: Add new calculated field to rulebook → re-run inject → new field appears in generated code
4. **100% test score** on all 4 substrates

---

## Appendix: Formula Examples from Rulebook

### TopFamilyFeudAnswer (complex AND)
```
=AND(
  {{HasSyntax}},
  NOT({{CanBeHeld}}),
  {{HasLinearDecodingPressure}},
  {{RequiresParsing}},
  {{StableOntologyReference}},
  NOT({{HasIdentity}}),
  {{DistanceFromConcept}}=2
)
```

### FamilyFuedQuestion (string concat)
```
="Is " & {{Name}} & " a language?"
```

### FamilyFeudMismatch (nested IF)
```
=IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " &
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") &
  IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")
```

### IsOpenClosedWorldConflicted (simple AND)
```
=AND({{IsOpenWorld}}, {{IsClosedWorld}})
```

### RelationshipToConcept (simple IF)
```
=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")
```
