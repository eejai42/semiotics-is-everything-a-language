# Binary Substrate: Formula-to-Native Evaluator Pipeline

## Overview

**Python does all orchestration + compilation + plumbing.**
**The ONLY runtime computation is:**

```
test_answer bytes → asm evaluator(test_answer_struct_ptr, candidate_id) → scalar result
```

This is a domain-agnostic "formula → tiny native evaluator" pipeline where field names, domain concepts, and business logic exist only at compile time. At runtime, it's pure byte offsets and generic operations.

---

Remaining Bugs in Binary Substrate
1. Calculated fields not computed before dependent formulas
The family_feud_mismatch formula reads {{TopFamilyFeudAnswer}} from the struct at offset 64, but the test runner packs the original JSON value (which is null/missing for calculated fields), not the computed value. The assembly functions are self-contained and don't call each other.

Fix needed: In take-test.py, call eval_top_family_feud_answer first and write the result back to the struct buffer at offset 64 before calling eval_family_feud_mismatch.

2. String return capturing may not work reliably
The StringResult struct approach to capture both x0 (ptr) and x1 (len) may not work correctly on ARM64 - ctypes struct returns don't always map to register pairs the way we need.

Fix needed: Either use a wrapper that stores x1 in a global, or have the assembly write the length to a known memory location.

3. Static buffer reuse between calls
The static result buffers (_result_buf_*) are 1KB each and not cleared between calls. Consecutive calls may have leftover data if the new string is shorter.

Fix needed: Zero the buffer at the start of each function, or always rely on the returned length (fix #2 first).

4. JSON field name mapping inconsistencies
The pack_test_answer function tries multiple key formats but may not correctly map all JSON keys (e.g., chosen_language_candidate vs ChosenLanguageCandidate) to struct offsets.

Fix needed: Verify the field name normalization matches between the compiler's build_schema and the runtime's packing logic.

5. family_fued_question formula uses wrong string literal length
In erb_calc.s:228, the code loads mov x1, #12 for str_1 (" a language?") but str_0 is loaded with mov x1, #3 - need to verify all literal lengths match their actual string contents.

## Original Implementation Plan

### Phase 0: Define a Tiny, Domain-Agnostic ABI

**Input Memory Struct: `TestAnswer`**
- Laid out as fixed offsets
- Contains only generic types: `bool`, `i64`, `f64`, `string_ref`, and optionally `null`
- Strings represented as `(ptr, len)` or `string_id` into an intern table

```
┌─────────────────────────────────────────────────┐
│  TestAnswer struct (example layout)             │
├─────────────────────────────────────────────────┤
│  Offset 0:   string_ptr   8 bytes               │
│  Offset 8:   string_len   8 bytes               │
│  Offset 16:  bool field   1 byte                │
│  Offset 17:  bool field   1 byte                │
│  ...                                            │
│  Offset 24:  i64 field    8 bytes               │
│  ...                                            │
└─────────────────────────────────────────────────┘
```

**Evaluator Signature (per computed value):**
```c
TaggedValue eval_X(const TestAnswer* ta, const char* candidate_id_ptr, int candidate_id_len);
```

**TaggedValue:**
```c
typedef struct {
    uint8_t tag;      // 0=null, 1=bool, 2=i64, 3=f64, 4=string
    union {
        bool    as_bool;
        int64_t as_i64;
        double  as_f64;
        struct { char* ptr; size_t len; } as_string;
    } payload;
} TaggedValue;
```

---

### Phase 1: Python — Parse + Lower Formulas into Minimal IR DAG

1. Read `test_answers.json`
2. For each "computed value" to reproduce:
   - Parse its Excel-dialect expression into an AST
   - Lower AST → **typed IR DAG** using only generic ops:
     - `IF`, `AND/OR/NOT`
     - Comparisons (`=`, `<>`, `<`, `<=`, `>`, `>=`)
     - Arithmetic (optional)
     - String ops (`&` concat, `LEN`, etc. if needed)
   - Resolve cell/field references into **offset reads** from `TestAnswer`
     - No domain words; just `field_17`, `field_42`, etc.
   - Constant-fold anything possible

---

### Phase 2: Python — Generate Assembly for Each DAG

Emit one asm function per computed value:
- Prologue allocates/uses stack scratch only for that DAG
- Loads inputs from `TestAnswer` by offset
- Executes IR ops (branchless where easy, branches for `IF`)
- Returns a `TaggedValue`

Include a tiny shared "runtime" in asm/C for:
- String compare
- String concat (optional)
- Boolean short-circuit
- Null semantics

Keep it minimal; everything else is inlined per-function.

---

### Phase 3: Python — Build Shared Library and Load It

1. Use `clang`/`nasm`/`as` to compile to `.so`/`.dylib`/`.dll`
2. Load via `ctypes` (or `cffi`) with the ABI above
3. Export a simple registry:
   - `get_fn(name) -> function pointer`
   - Or stable symbol naming: `eval_<hash>`

---

### Phase 4: Runtime Script (Domain-Agnostic Injector)

```python
# 1. Read test_answers.json
# 2. For each test_answer:
#    - Pack it into the TestAnswer struct (bytes)
#    - Call the selected asm evaluator(s) with:
#      * pointer to struct
#      * candidate identifier (bytes)
#    - Receive TaggedValue, decode to Python scalar
# 3. Write results back to the XLSX (or any sink)
```

This follows the same injector pattern as other substrates.

---

### Phase 5: "Only 3-4 Syntaxes" Support Strategy

Implement a **small set of IR patterns** that cover the Excel dialect:

| # | Pattern | Covers |
|---|---------|--------|
| 1 | Boolean logic blocks | `AND/OR/NOT` |
| 2 | Ternary blocks | `IF(cond, a, b)` |
| 3 | Comparisons + arithmetic | `=`, `<>`, `<`, `+`, `-`, etc. |
| 4 | String ops | concat `&` + equality |

Everything else either:
- Gets precomputed in Python, or
- Expands into these primitives during lowering

---

### Phase 6: Correctness Harness

For each computed value, run:
1. Python reference evaluator (AST interpreted) vs asm evaluator
2. Diff on a sample of `test_answers`
3. Only ship asm outputs when the harness matches

---

## File Structure

| File | Description |
|------|-------------|
| `inject-into-binary.py` | **THE COMPILER**: parses formulas → generates asm → builds .dylib |
| `erb_calc.asm` | **GENERATED** assembly (never hand-written) |
| `erb_calc.o` | Assembled object file |
| `erb_calc.dylib` / `.so` | Compiled shared library |
| `take-test.py` | Test runner: packs JSON → calls asm → unpacks results |
| `take-test.sh` | Shell wrapper |
| `test-answers.json` | Computed results for grading |

---

## The Contract

The ERB contract: **the same formula definitions work across all substrates**.

- SQL substrate: formulas → SQL expressions in views
- Python substrate: formulas → Python expressions
- GraphQL substrate: formulas → resolver logic
- **Binary substrate: formulas → x86-64 assembly**

The formula is the single source of truth. The assembly is derived, not authored.

---

## Current Status

**NOT IMPLEMENTED**

Run `./inject-substrate.sh` to see what's missing.
