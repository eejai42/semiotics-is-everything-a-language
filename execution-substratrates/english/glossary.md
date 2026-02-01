# ERB Glossary - Predicate Definitions

Human-readable definitions for all predicates in the Effortless Rulebook.

---

## Raw Predicates (Input Fields)

### LanguageCandidateId

**Type:** string

This unique identifier represents a specific candidate for classification as a language. It is used to track and reference each language candidate in the classification process.

---

### Name

**Type:** string

This predicate represents the name of the language candidate being evaluated. It is used to identify and refer to the candidate in discussions and analyses.

---

### Category

**Type:** string

This indicates the category to which the language candidate belongs, such as programming languages, natural languages, etc. It helps in understanding the context and classification of the candidate.

---

### ChosenLanguageCandidate

**Type:** boolean

This boolean value indicates whether the language candidate has been selected as a potential language. It plays a crucial role in determining which candidates are considered for further assessment.

---

### HasSyntax

**Type:** boolean

This predicate indicates whether the language candidate has a defined set of rules for structure and arrangement of symbols. It is an important factor in classifying something as a language, as syntax is a fundamental characteristic of most languages.

---

### HasIdentity

**Type:** boolean

This boolean value measures whether the language candidate has a distinct identity or recognition as a language. It helps in identifying established languages versus informal or lesser-known candidates.

---

### CanBeHeld

**Type:** boolean

This predicate indicates if the language candidate can be physically grasped or manipulated. It is used to differentiate between tangible and intangible entities when assessing the nature of the language.

---

### HasGrammar

**Type:** boolean

This indicates whether the language candidate has a set of rules governing the composition of clauses, phrases, and words. Grammar is essential for classifying a candidate as a language since it defines how the language operates.

---

### RequiresParsing

**Type:** boolean

This boolean value indicates whether the language candidate needs to be analyzed for structure and meaning. It is significant in determining the complexity of the language and its suitability for classification.

---

### HasLinearDecodingPressure

**Type:** boolean

This predicate measures whether the language candidate necessitates a sequential or linear approach to decoding information. It is important for understanding how the language functions and is processed.

---

### StableOntologyReference

**Type:** boolean

This boolean value indicates whether the language candidate has a consistent reference framework or ontology. Stability in ontology is crucial for a language's classification as it reflects its reliability and coherence.

---

### DimensionalityWhileEditing

**Type:** string

This string value represents the complexity or number of dimensions involved when editing the language candidate. It provides insight into how the language can be manipulated and its usability in practical applications.

---

### IsOpenWorld

**Type:** boolean

This boolean value indicates whether the language candidate operates in an open world context, meaning it allows for the introduction of new elements. This characteristic can influence its classification as a language based on its adaptability.

---

### IsClosedWorld

**Type:** boolean

This predicate indicates whether the language candidate exists in a closed world context, where all elements are predefined. This is relevant in classifying the candidate as it affects its flexibility and scope.

---

### DistanceFromConcept

**Type:** integer

This numeric value measures how closely related the language candidate is to a core concept of language. It helps in assessing its validity as a language based on its conceptual alignment.

---

### SortOrder

**Type:** integer

This integer value specifies the order in which language candidates are evaluated or presented. It is useful for organizing candidates during the classification process.

---

## Calculated Predicates (Computed Fields)

### FamilyFuedQuestion

**Type:** string
**Formula:** `="Is " & {{Name}} & " a language?"`

This calculated string formulates a question about whether the language candidate is considered a language. It serves as a prompt to initiate discussion or evaluation of the candidate.

---

### TopFamilyFeudAnswer

**Type:** boolean
**Formula:** `=AND(
  {{HasSyntax}},
  NOT({{CanBeHeld}}),
  {{HasLinearDecodingPressure}},
  {{RequiresParsing}},
  {{StableOntologyReference}},
  NOT({{HasIdentity}}),
  {{DistanceFromConcept}}=2
)`

This boolean value determines if the language candidate meets specific criteria that would classify it as a language. It aggregates several raw attributes to provide a clear classification outcome.

---

### FamilyFeudMismatch

**Type:** string
**Formula:** `=IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")`

This calculated string identifies discrepancies between the language candidate's classification and its characteristics. It highlights conflicts that may need further exploration in the classification process.

---

### IsOpenClosedWorldConflicted

**Type:** boolean
**Formula:** `=AND({{IsOpenWorld}}, {{IsClosedWorld}})`

This boolean value indicates whether there is a conflict between the open and closed world assumptions of the language candidate. Understanding this conflict is vital for accurate classification.

---

### RelationshipToConcept

**Type:** string
**Formula:** `=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`

This calculated string defines the relationship of the language candidate to a core concept based on its distance from that concept. It helps in clarifying how the candidate relates to established ideas of what constitutes a language.

---
