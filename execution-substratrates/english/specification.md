# ERB Specification - Language Classification Rulebook

---

## Overview

This rulebook system aims to provide a structured framework for understanding and defining "language" in a way that counters the overly broad assertion that "everything is a language." The objective is to formalize the concept of language by establishing clear criteria grounded in testable properties, such as syntax, parsing requirements, linear decoding pressure, and stability in ontology reference. By doing so, the system not only clarifies what constitutes a language but also delineates the boundaries that separate true languages from other forms of expression or communication.

At the core of this system is an operational definition of language, which posits that an item qualifies as a language if it possesses syntax, necessitates parsing, serializes meaning, and serves as an ontology or descriptor system. This definition is formalized into a set of necessary conditions that any candidate must satisfy to be classified as a language. The operational framework is reinforced by clear witnesses, such as English and Python, which fulfill these criteria, thereby validating the definition.

The model structure of this system is built upon a series of predicates that evaluate the properties of potential language candidates. Raw input properties are assessed using these predicates, which lead to calculated outputs that indicate whether a candidate meets the established criteria for being classified as a language. This structured approach allows for an analytical assessment of various entities, resulting in a classification system that identifies 14 candidates as languages and 11 as not languages, demonstrating the effectiveness of the framework.

The key insight of this system lies in its ability to differentiate between language systems, which adhere to the defined criteria, and other phenomena that may carry meaning but do not function as languages. By distinguishing language systems from sign vehicles and semiotic processes, this framework enriches our understanding of communication and meaning-making. It highlights the importance of formal definitions in academic and practical applications, ensuring that the term "language" retains its specific and meaningful connotation rather than being diluted by broad interpretations.

---

## Model Structure

The model operates on a set of raw predicates (input properties) that are evaluated for each candidate,
which then feed into calculated fields that derive the final classification.

### Raw Predicates (Inputs)

These are the fundamental properties evaluated for each candidate:

- **ChosenLanguageCandidate** (boolean)
- **HasSyntax** (boolean)
- **HasIdentity** (boolean)
- **CanBeHeld** (boolean)
- **HasGrammar** (boolean)
- **RequiresParsing** (boolean)
- **HasLinearDecodingPressure** (boolean)
- **StableOntologyReference** (boolean)
- **DimensionalityWhileEditing** (string)
- **IsOpenWorld** (boolean)
- **IsClosedWorld** (boolean)
- **DistanceFromConcept** (integer)

### Calculated Fields (Derived)

These fields are computed from the raw predicates:

- **FamilyFuedQuestion**
- **TopFamilyFeudAnswer**
- **FamilyFeudMismatch**
- **IsOpenClosedWorldConflicted**
- **RelationshipToConcept**

---

## Core Language Definition

An item qualifies as a **Language** if and only if ALL of these are true:

1. HasSyntax = true
2. RequiresParsing = true
3. Meaning_Is_Serialized = true (MeaningIsSerialized)
4. IsOngologyDescriptor = true
5. CanBeHeld = false
6. HasIdentity = false
7. DistanceFromConcept = 2

---

## Calculated Field Instructions

### FamilyFuedQuestion

**Formula:** `="Is " & {{Name}} & " a language?"`

**How to compute:**

1. Take the value of the 'Name' field. 2. Combine it with the phrase 'Is ' and the phrase ' a language?' 3. The result is your Family Fued Question.

---

### TopFamilyFeudAnswer

**Formula:** `=AND(
  {{HasSyntax}},
  NOT({{CanBeHeld}}),
  {{HasLinearDecodingPressure}},
  {{RequiresParsing}},
  {{StableOntologyReference}},
  NOT({{HasIdentity}}),
  {{DistanceFromConcept}}=2
)`

**How to compute:**

1. Check if 'HasSyntax' is true. 2. Ensure 'CanBeHeld' is false. 3. Confirm 'HasLinearDecodingPressure' is true. 4. Verify 'RequiresParsing' is true. 5. Check if 'StableOntologyReference' is true. 6. Ensure 'HasIdentity' is false. 7. Confirm that 'DistanceFromConcept' equals 2. 8. If all conditions are met, the result is true; otherwise, it is false.

---

### FamilyFeudMismatch

**Formula:** `=IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")`

**How to compute:**

1. Evaluate if 'TopFamilyFeudAnswer' does not equal 'ChosenLanguageCandidate'. 2. If they do not match, take the 'Name' value. 3. Add 'Is' or 'Isn't' based on 'TopFamilyFeudAnswer'. 4. Add the phrase 'a Family Feud Language, but'. 5. Add 'Is' or 'Is Not' based on 'ChosenLanguageCandidate'. 6. Optionally, add ' - Open World vs. Closed World Conflict.' if 'IsOpenClosedWorldConflicted' is true.

---

### IsOpenClosedWorldConflicted

**Formula:** `=AND({{IsOpenWorld}}, {{IsClosedWorld}})`

**How to compute:**

1. Check if 'IsOpenWorld' is true. 2. Also, check if 'IsClosedWorld' is true. 3. If both are true, then 'IsOpenClosedWorldConflicted' is true; otherwise, it is false.

---

### RelationshipToConcept

**Formula:** `=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`

**How to compute:**

1. Check the value of 'DistanceFromConcept'. 2. If it equals 1, the result is 'IsMirrorOf'. 3. If it does not equal 1, the result is 'IsDescriptionOf'.

---
