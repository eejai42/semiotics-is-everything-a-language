# Go SDK - Language Candidates Rulebook

Go implementation of the ERB calculation functions.

## Technology

**Go (Golang)** is Google's statically-typed, compiled language designed for simplicity, concurrency, and fast compilation. Its struct-based type system and method receivers make it well-suited for implementing ERB's entity/calculation pattern.

Key characteristics:
- **Structs with methods**: Go uses struct types with attached methods rather than classes
- **Pointer receivers**: Methods can modify struct state via pointer receivers (`func (c *Candidate) Calc...`)
- **JSON marshaling**: Built-in `encoding/json` with struct tags for field mapping
- **No inheritance**: Composition over inheritance; interfaces for polymorphism

The Go SDK mirrors the PostgreSQL calc functions as methods on entity structs, enabling the same DAG of calculations to run in-memory without a database.

## Files

- `erb_sdk.go` - Entity structs with calc methods mirroring PostgreSQL
- `main.go` - Demo application

## Usage

```go
import erb "language-candidates/golang"

// Load from rulebook
rulebook, err := erb.LoadFromRulebook("../../effortless-rulebook/effortless-rulebook.json")

// Use calculated fields (DAG-aware)
for _, c := range rulebook.LanguageCandidates.Data {
    view := c.ToView()
    fmt.Printf("%s: is_language=%v\n", *view.Name, view.IsAFamilyFeudTopAnswer)
}

// Or use individual calc methods
candidate := rulebook.LanguageCandidates.Data[0]
fmt.Println(candidate.CalcCategoryContainsLanguage())
fmt.Println(candidate.CalcIsAFamilyFeudTopAnswer())
fmt.Println(candidate.CalcFamilyFeudMismatch())
```

## DAG Execution Order

```
Level 0: Raw fields (from rulebook)
Level 1: CategoryContainsLanguage, HasGrammar, RelationshipToConcept, FamilyFuedQuestion
Level 2: IsAFamilyFeudTopAnswer (depends on CategoryContainsLanguage)
Level 3: FamilyFeudMismatch (depends on IsAFamilyFeudTopAnswer)
```

## Source

Mirrors: `postgres/02-create-functions.sql`
Generated from: `effortless-rulebook/effortless-rulebook.json`
