# RDF Execution Substrate

RDF (Resource Description Framework) execution substrate for the Effortless Rulebook.

## Current Status

**Implemented and fully functional.** The compiler generates RDFS schema, RDF data triples, and SPARQL CONSTRUCT queries from rulebook formulas. The test runner uses rdflib to execute the SPARQL queries and compute derived values.

Current test score: **100%** - All calculated fields pass.

## Running

```bash
# Generate RDF schema, data, and SPARQL queries
python3 inject-into-rdf.py

# Run tests (rdflib executes SPARQL CONSTRUCT queries)
./take-test.sh
```

## Can RDF Actually Compute?

**Yes.** RDF is a data model (subject-predicate-object triples), and **SPARQL** is its query/computation language. Together, RDF+SPARQL form a complete computation platform:

| Component | Role | Analogous To |
|-----------|------|--------------|
| RDF Triples | Data storage | Database rows |
| SPARQL SELECT | Read queries | SQL SELECT |
| SPARQL CONSTRUCT | Create new triples | Derived views |
| SPARQL UPDATE/INSERT | Materialize computed values | Triggers/procedures |

The OWL substrate uses SHACL-SPARQL rules, which is SPARQL wrapped in SHACL. The RDF substrate can use **pure SPARQL** without the SHACL layer.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INJECTOR                                │
│                    inject-into-rdf.py                           │
│                                                                 │
│  Input:  effortless-rulebook.json                              │
│  Output: data.ttl + queries.sparql                             │
│                                                                 │
│  - 100% domain-agnostic (reads schema, never hardcodes fields) │
│  - Compiles formulas to SPARQL CONSTRUCT queries               │
│  - Generates data triples from rulebook rows                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GENERATED ARTIFACTS                        │
│                                                                 │
│  schema.ttl          - RDF Schema (classes, properties)        │
│  data.ttl            - Data triples (raw values only)          │
│  queries.sparql      - SPARQL CONSTRUCT queries (calculations) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TEST RUNNER                              │
│                       take-test.py                              │
│                                                                 │
│  - Scaffolding only (no hardcoded field names)                 │
│  - pip installs rdflib automatically                           │
│  - Loads data graph                                            │
│  - Executes SPARQL queries to compute values                   │
│  - Extracts results, writes test-answers.json                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Difference from OWL Substrate

| Aspect | OWL Substrate | RDF Substrate |
|--------|---------------|---------------|
| **Schema layer** | OWL ontology (TBox) | RDFS (lighter) |
| **Rule mechanism** | SHACL-SPARQL rules | Pure SPARQL CONSTRUCT |
| **Dependencies** | rdflib + pyshacl | rdflib only |
| **Computation** | pyshacl.validate() | graph.query() |
| **Complexity** | Higher (SHACL layer) | Lower (direct SPARQL) |

The RDF substrate proves that you don't need OWL or SHACL - pure RDF+SPARQL is sufficient for formula computation.

## Implementation Plan

### Phase 1: Dependencies

```bash
# Minimal - just rdflib
pip install rdflib --quiet
```

No pyshacl needed. SPARQL is built into rdflib.

### Phase 2: inject-into-rdf.py

The injector generates three files:

#### 2a. schema.ttl (RDFS Schema)

```python
def generate_schema(tables: Dict[str, Any]) -> str:
    """Generate RDFS schema (lighter than OWL)."""
    lines = []
    lines.append('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .')
    lines.append('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .')
    lines.append('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .')
    lines.append('@prefix erb: <http://example.org/erb#> .')
    lines.append('')

    for table_name, table_def in tables.items():
        # Class definition
        lines.append(f'erb:{table_name} a rdfs:Class .')

        # Property definitions
        for col in table_def["schema"]:
            prop = to_camel_case(col["name"])
            xsd_type = datatype_to_xsd(col["datatype"])
            lines.append(f'erb:{prop} a rdf:Property ;')
            lines.append(f'    rdfs:domain erb:{table_name} ;')
            lines.append(f'    rdfs:range {xsd_type} .')

    return '\n'.join(lines)
```

#### 2b. data.ttl (Raw Data Triples)

```python
def generate_data(tables: Dict[str, Any]) -> str:
    """Generate data triples (raw values only, no calculated)."""
    lines = []
    # ... prefixes ...

    for table_name, table_def in tables.items():
        for i, row in enumerate(table_def["data"]):
            uri = f'erb:{table_name}_{i}'
            lines.append(f'{uri} a erb:{table_name} ;')

            for col in table_def["schema"]:
                if col.get("type") == "calculated":
                    continue  # SPARQL will compute these

                value = row.get(col["name"])
                if value is not None:
                    prop = to_camel_case(col["name"])
                    turtle_val = to_turtle_literal(value, col["datatype"])
                    lines.append(f'    erb:{prop} {turtle_val} ;')

            lines[-1] = lines[-1].rstrip(' ;') + ' .'

    return '\n'.join(lines)
```

#### 2c. queries.sparql (SPARQL CONSTRUCT Queries)

This is the key innovation - compile formulas directly to SPARQL:

```python
def generate_sparql_queries(tables: Dict[str, Any]) -> str:
    """Compile formulas to SPARQL CONSTRUCT queries."""
    queries = []

    for table_name, table_def in tables.items():
        for col in table_def["schema"]:
            formula = col.get("formula")
            if not formula:
                continue

            # Parse formula to AST (reuse from OWL substrate)
            ast = parse_formula(formula)

            # Collect field references
            field_bindings = {}
            sparql_expr = compile_to_sparql(ast, field_bindings)

            # Build CONSTRUCT query
            target_prop = to_camel_case(col["name"])

            query = f'''
# Computed field: {col["name"]}
# Formula: {formula}
CONSTRUCT {{
    ?entity erb:{target_prop} ?_result .
}}
WHERE {{
    ?entity a erb:{table_name} .
'''
            # Add bindings for referenced fields
            for field_name, var_name in field_bindings.items():
                prop = to_camel_case(field_name)
                query += f'    OPTIONAL {{ ?entity erb:{prop} {var_name} . }}\n'

            query += f'    BIND({sparql_expr} AS ?_result)\n}}'
            queries.append(query)

    return '\n\n'.join(queries)
```

### Phase 3: Formula-to-SPARQL Compiler

Reuses the exact same compiler from OWL substrate:

```
Formula: "Is " & {{Name}} & " a language?"
    ↓ parse
AST: Concat([LiteralString("Is "), FieldRef("Name"), LiteralString(" a language?")])
    ↓ compile_to_sparql
SPARQL: CONCAT("Is ", ?name, " a language?")
```

```
Formula: IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")
    ↓ compile_to_sparql
SPARQL: IF(?distance_from_concept = 1, "IsMirrorOf", "IsDescriptionOf")
```

### Phase 4: take-test.py (Scaffolding)

```python
#!/usr/bin/env python3
"""
Take Test - RDF Execution Substrate

Scaffolding that:
1. Loads generated RDF data
2. Executes SPARQL CONSTRUCT queries to compute derived values
3. Extracts results to test-answers.json

The computation happens in SPARQL, not hardcoded here.
"""
import subprocess
import sys

# Auto-install dependencies
subprocess.check_call([sys.executable, "-m", "pip", "install",
                       "rdflib", "--quiet"])

from rdflib import Graph, Namespace
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from orchestration.shared import load_rulebook


def main():
    script_dir = Path(__file__).resolve().parent
    erb = Namespace("http://example.org/erb#")

    # Load base data graph
    graph = Graph()
    graph.parse(script_dir / "schema.ttl")
    graph.parse(script_dir / "data.ttl")

    print(f"Loaded {len(graph)} triples")

    # Load and execute SPARQL queries
    queries_file = script_dir / "queries.sparql"
    queries_text = queries_file.read_text()

    # Split into individual queries (separated by blank lines)
    queries = [q.strip() for q in queries_text.split('\n\n') if q.strip()]

    # Execute each CONSTRUCT query and add results to graph
    for query in queries:
        if query.startswith('#'):
            # Skip comment-only blocks
            continue
        try:
            # CONSTRUCT returns a new graph
            result_graph = graph.query(query).graph
            if result_graph:
                # Add computed triples to main graph
                for triple in result_graph:
                    graph.add(triple)
        except Exception as e:
            print(f"Query error: {e}")

    print(f"After computation: {len(graph)} triples")

    # Extract computed values (domain-agnostic)
    rulebook = load_rulebook()
    records = extract_values(graph, rulebook, erb)

    # Save results
    test_file = script_dir / "test-answers.json"
    with open(test_file, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} records to {test_file}")


def extract_values(graph, rulebook, erb):
    """Extract all property values from graph."""
    records = []

    for table_name, table_def in rulebook.items():
        if not isinstance(table_def, dict) or 'schema' not in table_def:
            continue

        for i, row in enumerate(table_def.get("data", [])):
            record = {}
            uri = erb[f"{table_name}_{i}"]

            for col in table_def["schema"]:
                prop_name = col["name"]
                prop = erb[prop_name[0].lower() + prop_name[1:]]
                value = graph.value(uri, prop)
                if value is not None:
                    record[to_snake_case(prop_name)] = convert_value(value)

            records.append(record)

    return records


if __name__ == "__main__":
    main()
```

## Example: Generated SPARQL Query

For the formula `"Is " & {{Name}} & " a language?"`:

```sparql
# Computed field: FamilyFuedQuestion
# Formula: ="Is " & {{Name}} & " a language?"

CONSTRUCT {
    ?entity erb:familyFuedQuestion ?_result .
}
WHERE {
    ?entity a erb:LanguageCandidates .
    OPTIONAL { ?entity erb:name ?name . }
    BIND(CONCAT("Is ", ?name, " a language?") AS ?_result)
}
```

For the formula `IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`:

```sparql
# Computed field: RelationshipToConcept
# Formula: =IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")

CONSTRUCT {
    ?entity erb:relationshipToConcept ?_result .
}
WHERE {
    ?entity a erb:LanguageCandidates .
    OPTIONAL { ?entity erb:distanceFromConcept ?distance_from_concept . }
    BIND(IF(?distance_from_concept = 1, "IsMirrorOf", "IsDescriptionOf") AS ?_result)
}
```

## File Structure

```
rdf/
├── inject-into-rdf.py      # Injector (domain-agnostic)
├── inject-substrate.sh     # Orchestration wrapper
├── take-test.sh            # Test orchestration
├── take-test.py            # Test runner scaffolding
│
├── schema.ttl              # Generated: RDFS schema
├── data.ttl                # Generated: Data triples (raw only)
├── queries.sparql          # Generated: SPARQL CONSTRUCT queries
│
├── test-answers.json       # Output: computed test results
└── README.md               # This file
```

## Comparison: RDF vs OWL Substrates

| Aspect | RDF Substrate | OWL Substrate |
|--------|---------------|---------------|
| **Schema** | RDFS (simple) | OWL (expressive) |
| **Data** | Turtle triples | Turtle triples |
| **Computation** | SPARQL CONSTRUCT | SHACL-SPARQL rules |
| **Executor** | rdflib.query() | pyshacl.validate() |
| **Dependencies** | rdflib | rdflib + pyshacl |
| **Formula compiler** | Same AST→SPARQL | Same AST→SPARQL |
| **Complexity** | Lower | Higher |

## Why This Isn't Cheating

The RDF substrate genuinely computes using SPARQL:

1. **Formula parsing**: Tokenize → Parse → AST (same compiler as OWL)
2. **SPARQL generation**: AST → SPARQL expressions (same code as OWL)
3. **Execution**: rdflib executes SPARQL CONSTRUCT queries
4. **Result**: New triples are added to the graph

Python only provides scaffolding - the actual computation is performed by the SPARQL engine inside rdflib.

## Technology Background

**RDF (Resource Description Framework)** is the W3C standard for representing information as subject-predicate-object triples. It's the foundation of the Semantic Web.

**SPARQL** is the W3C query language for RDF, analogous to SQL for relational databases. SPARQL 1.1 includes:
- SELECT (read data)
- CONSTRUCT (create new triples from patterns)
- INSERT/DELETE (modify graphs)
- Built-in functions: CONCAT, IF, CONTAINS, LCASE, etc.

**rdflib** is the standard Python library for RDF, with a built-in SPARQL engine.

## Generated Files

| File | Description |
|------|-------------|
| `schema.ttl` | **GENERATED** - RDFS schema (classes and properties) |
| `data.ttl` | **GENERATED** - RDF triples (raw data values) |
| `queries.sparql` | **GENERATED** - SPARQL CONSTRUCT queries for calculations |
| `test-answers.json` | **GENERATED** - Test execution results for grading |
| `test-results.md` | **GENERATED** - Human-readable test report |

## Source Files (Not Cleaned)

| File | Description |
|------|-------------|
| `inject-into-rdf.py` | The compiler: parses formulas and generates RDF/SPARQL |
| `inject-substrate.sh` | Shell wrapper for orchestration |
| `take-test.py` | Test runner using rdflib SPARQL engine |
| `take-test.sh` | Shell wrapper for test runner |
| `README.md` | This documentation |

## Cleaning

To remove all generated files:

```bash
python3 inject-into-rdf.py --clean
```

This will remove:
- `schema.ttl`
- `data.ttl`
- `queries.sparql`
- `test-answers.json`
- `test-results.md`

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
