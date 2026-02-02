# ERB Glossary - Predicate Definitions

Human-readable definitions for all predicates in the Effortless Rulebook.

---

## Raw Predicates (Input Fields)

### LanguageCandidateId

**Type:** string

This predicate represents a unique identifier for each language candidate. It is used to track and reference individual language candidates in the classification process.

---

### Name

**Type:** string

This predicate indicates the name of the language candidate being evaluated. It is essential for identifying and distinguishing between different language candidates.

---

### Category

**Type:** string

This predicate specifies the category to which the language candidate belongs, such as natural language or programming language. It helps in understanding the context and classification of the language candidate.

---

### ChosenLanguageCandidate

**Type:** boolean

This boolean predicate indicates whether the language candidate has been selected as a potential language. It plays a crucial role in determining which candidates are considered for further analysis.

---

### HasSyntax

**Type:** boolean

This predicate indicates whether the language candidate has a defined syntax or structure. Syntax is essential for determining if the candidate can be classified as a language.

---

### HasIdentity

**Type:** boolean

This boolean predicate shows whether the language candidate has a clear identity or distinctiveness. Candidates without a strong identity may not qualify as full-fledged languages.

---

### CanBeHeld

**Type:** boolean

This predicate indicates whether the language candidate can be held or maintained as a formal entity. If a candidate cannot be held, it may not be considered a true language.

---

### RequiresParsing

**Type:** boolean

This predicate measures whether the language candidate requires parsing to understand its structure. A candidate that requires parsing is more likely to be classified as a language.

---

### ResolvesToAnAST

**Type:** boolean

This boolean predicate indicates if the language candidate can be resolved into an Abstract Syntax Tree (AST). The ability to resolve to an AST is a strong indicator of a candidate being a language.

---

### HasLinearDecodingPressure

**Type:** boolean

This predicate shows whether the language candidate has linear decoding pressure, which refers to the need to process the language input in a sequential manner. This characteristic is important for classifying a candidate as a language.

---

### IsStableOntologyReference

**Type:** boolean

This boolean predicate indicates if the language candidate serves as a stable reference within an ontology. A stable ontology reference is essential for a candidate to be recognized as a language.

---

### IsLiveOntologyEditor

**Type:** boolean

This predicate measures whether the language candidate functions as a live editor for an ontology. If it does, it may influence its classification as a language.

---

### DimensionalityWhileEditing

**Type:** string

This predicate specifies the dimensionality of the language candidate when being edited. Understanding the dimensionality can help determine the complexity and classification of the candidate.

---

### IsOpenWorld

**Type:** boolean

This boolean predicate indicates if the language candidate operates in an open-world context, where new terms can be added freely. Open-world characteristics can affect how a candidate is classified as a language.

---

### IsClosedWorld

**Type:** boolean

This predicate measures whether the language candidate functions within a closed-world context, where all terms are predefined. This characteristic is vital for understanding the classification of the candidate.

---

### DistanceFromConcept

**Type:** integer

This numeric value measures how far the language candidate is from a core concept of what constitutes a language. The distance helps determine the relevance and classification of the candidate.

---

### ModelObjectFacilityLayer

**Type:** string

This predicate specifies the layer of the model object facility that the language candidate operates within. It aids in understanding the structural context of the candidate.

---

### SortOrder

**Type:** integer

This predicate indicates the order in which language candidates should be evaluated or processed. It helps prioritize candidates during the classification process.

---

## Calculated Predicates (Computed Fields)

### FamilyFuedQuestion

**Type:** string
**Formula:** `="Is " & {{Name}} & " a language?"`

This calculated predicate generates a question that asks if the language candidate is considered a language. It serves as a prompt for determining the candidate's status.

---

### TopFamilyFeudAnswer

**Type:** boolean
**Formula:** `=AND(
  {{HasSyntax}},
  {{RequiresParsing}},
  {{IsDescriptionOf}},
  {{HasLinearDecodingPressure}},
  {{ResolvesToAnAST}},
  {{IsStableOntologyReference}},
  NOT({{CanBeHeld}}),
  NOT({{HasIdentity}})
)`

This boolean predicate evaluates whether the language candidate meets specific criteria indicative of being a language. It is used to help classify the candidate accurately.

---

### FamilyFeudMismatch

**Type:** string
**Formula:** `=IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")`

This calculated predicate identifies discrepancies between the top family feud answer and the chosen language candidate. It highlights candidates that may not align with the typical characteristics of a language.

---

### HasGrammar

**Type:** boolean
**Formula:** `={{HasSyntax}} = TRUE()`

This boolean predicate indicates whether the language candidate has defined grammatical rules. Having grammar is a crucial factor in assessing if a candidate is a language.

---

### IsOpenClosedWorldConflicted

**Type:** boolean
**Formula:** `=AND({{IsOpenWorld}}, {{IsClosedWorld}})`

This predicate evaluates if there is a conflict between open and closed world characteristics of the language candidate. Such conflicts can complicate its classification as a language.

---

### IsDescriptionOf

**Type:** boolean
**Formula:** `={{DistanceFromConcept}} > 1`

This boolean predicate indicates whether the language candidate serves as a description of a core concept. Descriptive candidates may not be classified as full languages.

---

### RelationshipToConcept

**Type:** string
**Formula:** `=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`

This calculated predicate describes the relationship of the language candidate to a core concept, indicating whether it mirrors or describes that concept. This classification helps assess the candidate's language status.

---
