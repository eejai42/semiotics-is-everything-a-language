# Golang Execution Substrate

Go calculation library generated from the Effortless Rulebook.

## Overview

This substrate compiles rulebook formulas into native Go code, generating structs and calculation functions that mirror the PostgreSQL `calc_*` pattern.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   inject-into-golang.py                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. Load rulebook JSON (structured data)                    │
│                          ↓                                   │
│   2. Parse Excel-dialect formulas into AST                   │
│                          ↓                                   │
│   3. Build dependency DAG for calculation ordering           │
│                          ↓                                   │
│   4. Compile formulas to Go expressions                      │
│                          ↓                                   │
│   5. Generate Calc* methods for each calculated field        │
│                          ↓                                   │
│   6. Output: erb_sdk.go with structs and ComputeAll()        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Individual Calc* Methods**: Mirrors PostgreSQL `calc_*` function pattern
- **ComputeAll() Method**: Computes all calculated fields in DAG order
- **Domain-Agnostic**: Works with any rulebook schema
- **Null-Safe**: Uses pointer types for nullable fields with helper functions
- **Type Preservation**: Proper Go types for boolean, integer, and string fields

## Generated Files

| File | Description |
|------|-------------|
| `erb_sdk.go` | **GENERATED** - Go structs and calculation functions compiled from rulebook formulas |
| `main.go` | **GENERATED** - Test runner that loads blank-test.json and produces test-answers.json |
| `erb_test` | **GENERATED** - Compiled Go binary (test runner) |
| `test-answers.json` | **GENERATED** - Test execution results for grading |
| `test-results.md` | **GENERATED** - Human-readable test report |

## Source Files (Not Cleaned)

| File | Description |
|------|-------------|
| `inject-into-golang.py` | The compiler: parses formulas and generates Go code |
| `inject-substrate.sh` | Shell wrapper for orchestration |
| `take-test.sh` | Shell wrapper for test runner (builds and runs erb_test) |
| `README.md` | This documentation |

## Cleaning

To remove all generated files:

```bash
python3 inject-into-golang.py --clean
```

This will remove:
- `erb_sdk.go`
- `main.go`
- `erb_test`
- `test-answers.json`
- `test-results.md`

## Usage

```go
package main

import "fmt"

func main() {
    // Create a record with raw fields
    record := &LanguageCandidate{
        ChosenLanguageCandidate: strPtr("Music"),
        HasSyntax:               boolPtr(true),
        RequiresParsing:         boolPtr(false),
        // ... other raw fields
    }

    // Compute all calculated fields
    computed := record.ComputeAll()

    // Access computed values
    fmt.Println(*computed.FamilyFuedQuestion)
    fmt.Println(*computed.IsOpenClosedWorldConflicted)
}
```

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
