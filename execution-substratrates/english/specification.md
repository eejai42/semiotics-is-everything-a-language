# ERB Specification - Language Classification Rulebook

---

## Overview

The formal rulebook system was created to address the oversimplified notion that "everything is a language" by providing a structured framework to define what constitutes a language. This system aims to clarify the characteristics that differentiate genuine languages from other forms of communication, ensuring that the definition of language is grounded in measurable and testable properties. By establishing clear criteria, the system seeks to foster a more nuanced understanding of language, avoiding the pitfalls of vague classifications that can lead to confusion and misinterpretation.

At the heart of this framework is an operational definition of language that requires an entity to meet four essential criteria: it must possess syntax, necessitate parsing, serialize meaning, and function as an ontology or descriptor system. This definition establishes a computable classification boundary that delineates what qualifies as a language and what does not. By grounding the definition in these specific attributes, the system provides clarity and focus, facilitating a more rigorous examination of various candidates for language status.

The model structure of the system operates by utilizing a set of raw predicates that serve as foundational inputs, which are then transformed into calculated outputs. These outputs allow for the classification of entities based on their alignment with the operational definition of language. The predicates, such as HasSyntax and RequiresParsing, work together to evaluate each candidate, ultimately leading to a determination of whether an item is classified as a language or not. This systematic approach enables the rigorous assessment of a wide range of candidates, as demonstrated by the evaluation of 25 total candidates, with 14 being classified as languages and 11 as not.

The key insight from this formalization is the critical distinction it draws between language systems, sign vehicles, and semiotic processes. Understanding this differentiation is vital because it helps clarify the nature of communication and meaning production in various contexts. By recognizing that not everything that conveys meaning qualifies as a language, the system encourages a more sophisticated approach to analyzing communication forms, particularly in complex, dynamic environments. This clarity is especially relevant in fields such as linguistics, semiotics, and information science, where precise definitions can significantly impact theory and practice.

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
- **RequiresParsing** (boolean)
- **ResolvesToAnAST** (boolean)
- **HasLinearDecodingPressure** (boolean)
- **IsStableOntologyReference** (boolean)
- **IsLiveOntologyEditor** (boolean)
- **DimensionalityWhileEditing** (string)
- **IsOpenWorld** (boolean)
- **IsClosedWorld** (boolean)
- **DistanceFromConcept** (integer)
- **ModelObjectFacilityLayer** (string)

### Calculated Fields (Derived)

These fields are computed from the raw predicates:

- **FamilyFuedQuestion**
- **TopFamilyFeudAnswer**
- **FamilyFeudMismatch**
- **HasGrammar**
- **IsOpenClosedWorldConflicted**
- **IsDescriptionOf**
- **RelationshipToConcept**

---

## Core Language Definition

An item qualifies as a **Language** if and only if ALL of these are true:

1. HasSyntax = true
2. RequiresParsing = true
3. HasLinearDecodingPressure = true
4. StableOntologyReference = true
5. CanBeHeld = false
6. HasIdentity = false
7. DistanceFromConcept = 2

---

## Calculated Field Instructions

### FamilyFuedQuestion

**Formula:** `="Is " & {{Name}} & " a language?"`

**How to compute:**

1. Take the value of the 'Name' field. 2. Combine it with the phrase 'Is ' at the beginning and ' a language?' at the end. 3. The result is the Family Feud Question.

---

### TopFamilyFeudAnswer

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

**How to compute:**

1. Check the values of the following fields: HasSyntax, RequiresParsing, IsDescriptionOf, HasLinearDecodingPressure, ResolvesToAnAST, IsStableOntologyReference. 2. Ensure that CanBeHeld and HasIdentity are both false. 3. If all conditions are met, the result is true; otherwise, it is false.

---

### FamilyFeudMismatch

**Formula:** `=IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")`

**How to compute:**

1. Compare the value of TopFamilyFeudAnswer with ChosenLanguageCandidate. 2. If they are not equal, take the Name value. 3. Determine if TopFamilyFeudAnswer is true or false and add 'Is' or 'Isn't' accordingly. 4. Check if ChosenLanguageCandidate is true or false and add 'Is' or 'Is Not'. 5. If IsOpenClosedWorldConflicted is true, add the conflict note. 6. Combine all parts into a complete sentence.

---

### HasGrammar

**Formula:** `={{HasSyntax}} = TRUE()`

**How to compute:**

1. Look at the value of the HasSyntax field. 2. If it is true, then HasGrammar is true; otherwise, it is false.

---

### IsOpenClosedWorldConflicted

**Formula:** `=AND({{IsOpenWorld}}, {{IsClosedWorld}})`

**How to compute:**

1. Check if IsOpenWorld is true. 2. Check if IsClosedWorld is also true. 3. If both are true, then the result is true; otherwise, it is false.

---

### IsDescriptionOf

**Formula:** `={{DistanceFromConcept}} > 1`

**How to compute:**

1. Look at the value of DistanceFromConcept. 2. If it is greater than 1, then IsDescriptionOf is true; otherwise, it is false.

---

### RelationshipToConcept

**Formula:** `=IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")`

**How to compute:**

1. Check the value of DistanceFromConcept. 2. If it equals 1, then the result is 'IsMirrorOf'. 3. If it is not equal to 1, then the result is 'IsDescriptionOf'.

---
