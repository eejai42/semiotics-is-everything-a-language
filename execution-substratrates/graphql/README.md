# GraphQL Execution Substrate

GraphQL schema and resolvers generated from the Effortless Rulebook.

## Overview

This substrate generates a complete GraphQL implementation including type definitions and JavaScript resolver functions. The generated code can be used with any GraphQL server (Apollo, Express-GraphQL, etc.).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  inject-into-graphql.py                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. Load rulebook JSON (structured data)                    │
│                          ↓                                   │
│   2. Parse Excel-dialect formulas into AST                   │
│                          ↓                                   │
│   3. Build dependency DAG for calculation ordering           │
│                          ↓                                   │
│   4. Compile formulas to JavaScript expressions              │
│                          ↓                                   │
│   5. Generate GraphQL SDL (schema.graphql)                   │
│                          ↓                                   │
│   6. Generate JavaScript calc functions (resolvers.js)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Schema-First Design**: GraphQL SDL with strongly-typed fields
- **JavaScript Resolvers**: calc* functions for each calculated field
- **DAG-Ordered Execution**: Calculated fields computed in dependency order
- **Domain-Agnostic**: Works with any rulebook schema
- **Consistent Logic**: Same formulas as PostgreSQL, Python, and other substrates

## Generated Files

| File | Description |
|------|-------------|
| `schema.graphql` | **GENERATED** - GraphQL type definitions for all entities |
| `resolvers.js` | **GENERATED** - JavaScript resolver functions for calculated fields |
| `test-answers.json` | **GENERATED** - Test execution results for grading |
| `test-results.md` | **GENERATED** - Human-readable test report |

## Source Files (Not Cleaned)

| File | Description |
|------|-------------|
| `inject-into-graphql.py` | The compiler: parses formulas and generates GraphQL/JS code |
| `inject-substrate.sh` | Shell wrapper for orchestration (also regenerates shared erb_calc.py) |
| `take-test.py` | Test runner that uses shared Python calculation library |
| `take-test.sh` | Shell wrapper for test runner |
| `README.md` | This documentation |

## Cleaning

To remove all generated files:

```bash
python3 inject-into-graphql.py --clean
```

This will remove:
- `schema.graphql`
- `resolvers.js`
- `test-answers.json`
- `test-results.md`

## Technology

**GraphQL** is a query language and runtime for APIs developed by Facebook (2012, open-sourced 2015). Unlike REST's fixed endpoints, GraphQL lets clients request exactly the fields they need in a single query, with strong typing enforced by a schema.

Key characteristics:
- **Schema-first**: Types, queries, and mutations are defined in SDL (Schema Definition Language)
- **Hierarchical queries**: Clients can traverse relationships in a single request
- **Strong typing**: Every field has a type; the schema serves as a contract and documentation
- **Introspection**: Clients can query the schema itself to discover available types and fields

## Usage

```javascript
const { calcFamilyFuedQuestion, calcIsOpenClosedWorldConflicted } = require('./resolvers');

const candidate = {
  chosenLanguageCandidate: 'Music',
  hasSyntax: true,
  requiresParsing: false,
  // ... other raw fields
};

// Compute individual fields
const question = calcFamilyFuedQuestion(candidate);
const conflicted = calcIsOpenClosedWorldConflicted(candidate);
```

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
