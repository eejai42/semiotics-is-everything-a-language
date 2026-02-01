// ERB SDK - Go Implementation (GENERATED - DO NOT EDIT)
// ======================================================
// Generated from: effortless-rulebook/effortless-rulebook.json
//
// This file contains structs and calculation functions
// for all tables defined in the rulebook.

package main

import (
	"encoding/json"
	"fmt"
	"os"
)

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// boolVal safely dereferences a *bool, returning false if nil
func boolVal(b *bool) bool {
	if b == nil {
		return false
	}
	return *b
}

// stringVal safely dereferences a *string, returning "" if nil
func stringVal(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// nilIfEmpty returns nil for empty strings, otherwise a pointer to the string
func nilIfEmpty(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// =============================================================================
// ISEVERYTHINGALANGUAGE TABLE
// =============================================================================

// IsEverythingALanguage represents a row in the IsEverythingALanguage table
type IsEverythingALanguage struct {
	IsEverythingALanguageId string `json:"is_everything_a_language_id"`
	Name *string `json:"name"`
	ArgumentName *string `json:"argument_name"`
	ArgumentCategory *string `json:"argument_category"`
	StepType *string `json:"step_type"`
	Statement *string `json:"statement"`
	Formalization *string `json:"formalization"`
	RelatedCandidateName *string `json:"related_candidate_name"`
	RelatedCandidateId *string `json:"related_candidate_id"`
	EvidenceFromRulebook *string `json:"evidence_from_rulebook"`
	Notes *string `json:"notes"`
}

// =============================================================================
// LANGUAGECANDIDATES TABLE
// =============================================================================

// LanguageCandidate represents a row in the LanguageCandidates table
type LanguageCandidate struct {
	LanguageCandidateId string `json:"language_candidate_id"`
	Name *string `json:"name"`
	Category *string `json:"category"`
	ChosenLanguageCandidate *bool `json:"chosen_language_candidate"`
	HasSyntax *bool `json:"has_syntax"`
	HasIdentity *bool `json:"has_identity"`
	CanBeHeld *bool `json:"can_be_held"`
	RequiresParsing *bool `json:"requires_parsing"`
	HasLinearDecodingPressure *bool `json:"has_linear_decoding_pressure"`
	StableOntologyReference *bool `json:"stable_ontology_reference"`
	DimensionalityWhileEditing *string `json:"dimensionality_while_editing"`
	IsOpenWorld *bool `json:"is_open_world"`
	IsClosedWorld *bool `json:"is_closed_world"`
	DistanceFromConcept *int `json:"distance_from_concept"`
	SortOrder *int `json:"sort_order"`
	FamilyFuedQuestion *string `json:"family_fued_question"`
	TopFamilyFeudAnswer *bool `json:"top_family_feud_answer"`
	FamilyFeudMismatch *string `json:"family_feud_mismatch"`
	HasGrammar *bool `json:"has_grammar"`
	IsOpenClosedWorldConflicted *bool `json:"is_open_closed_world_conflicted"`
	RelationshipToConcept *string `json:"relationship_to_concept"`
}

// --- Individual Calculation Functions ---

// CalcFamilyFuedQuestion computes the FamilyFuedQuestion calculated field
// Formula: ="Is " & {{Name}} & " a language?"
func (tc *LanguageCandidate) CalcFamilyFuedQuestion() string {
	return "Is " + stringVal(tc.Name) + " a language?"
}

// CalcTopFamilyFeudAnswer computes the TopFamilyFeudAnswer calculated field
// Formula: =AND(   {{HasSyntax}},   NOT({{CanBeHeld}}),   {{HasLinearDecodingPressure}},   {{RequiresParsing}},   {{StableOntologyReference}},   NOT({{HasIdentity}}),   {{DistanceFromConcept}}=2 )
func (tc *LanguageCandidate) CalcTopFamilyFeudAnswer() bool {
	return (boolVal(tc.HasSyntax) && !boolVal(tc.CanBeHeld) && boolVal(tc.HasLinearDecodingPressure) && boolVal(tc.RequiresParsing) && boolVal(tc.StableOntologyReference) && !boolVal(tc.HasIdentity) && (tc.DistanceFromConcept != nil && *tc.DistanceFromConcept == 2))
}

// CalcFamilyFeudMismatch computes the FamilyFeudMismatch calculated field
// Formula: =IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),   {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " &    IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")
func (tc *LanguageCandidate) CalcFamilyFeudMismatch() string {
	return func() string { if !((boolVal(tc.TopFamilyFeudAnswer) == boolVal(tc.ChosenLanguageCandidate))) { return stringVal(tc.Name) + " " + func() string { if boolVal(tc.TopFamilyFeudAnswer) { return "Is" }; return "Isn't" }() + " a Family Feud Language, but " + func() string { if boolVal(tc.ChosenLanguageCandidate) { return "Is" }; return "Is Not" }() + " marked as a 'Language Candidate.'" }; return "" }() + func() string { if boolVal(tc.IsOpenClosedWorldConflicted) { return " - Open World vs. Closed World Conflict." }; return "" }()
}

// CalcHasGrammar computes the HasGrammar calculated field
// Formula: =AND({{HasSyntax}})
func (tc *LanguageCandidate) CalcHasGrammar() bool {
	return (boolVal(tc.HasSyntax))
}

// CalcIsOpenClosedWorldConflicted computes the IsOpenClosedWorldConflicted calculated field
// Formula: =AND({{IsOpenWorld}}, {{IsClosedWorld}})
func (tc *LanguageCandidate) CalcIsOpenClosedWorldConflicted() bool {
	return (boolVal(tc.IsOpenWorld) && boolVal(tc.IsClosedWorld))
}

// CalcRelationshipToConcept computes the RelationshipToConcept calculated field
// Formula: =IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")
func (tc *LanguageCandidate) CalcRelationshipToConcept() string {
	return func() string { if (tc.DistanceFromConcept != nil && *tc.DistanceFromConcept == 1) { return "IsMirrorOf" }; return "IsDescriptionOf" }()
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *LanguageCandidate) ComputeAll() *LanguageCandidate {
	// Level 1 calculations
	familyFuedQuestion := "Is " + stringVal(tc.Name) + " a language?"
	topFamilyFeudAnswer := (boolVal(tc.HasSyntax) && !boolVal(tc.CanBeHeld) && boolVal(tc.HasLinearDecodingPressure) && boolVal(tc.RequiresParsing) && boolVal(tc.StableOntologyReference) && !boolVal(tc.HasIdentity) && (tc.DistanceFromConcept != nil && *tc.DistanceFromConcept == 2))
	hasGrammar := (boolVal(tc.HasSyntax))
	isOpenClosedWorldConflicted := (boolVal(tc.IsOpenWorld) && boolVal(tc.IsClosedWorld))
	relationshipToConcept := func() string { if (tc.DistanceFromConcept != nil && *tc.DistanceFromConcept == 1) { return "IsMirrorOf" }; return "IsDescriptionOf" }()

	// Level 2 calculations
	familyFeudMismatch := func() string { if !((topFamilyFeudAnswer == boolVal(tc.ChosenLanguageCandidate))) { return stringVal(tc.Name) + " " + func() string { if topFamilyFeudAnswer { return "Is" }; return "Isn't" }() + " a Family Feud Language, but " + func() string { if boolVal(tc.ChosenLanguageCandidate) { return "Is" }; return "Is Not" }() + " marked as a 'Language Candidate.'" }; return "" }() + func() string { if isOpenClosedWorldConflicted { return " - Open World vs. Closed World Conflict." }; return "" }()

	return &LanguageCandidate{
		LanguageCandidateId: tc.LanguageCandidateId,
		Name: tc.Name,
		Category: tc.Category,
		ChosenLanguageCandidate: tc.ChosenLanguageCandidate,
		HasSyntax: tc.HasSyntax,
		HasIdentity: tc.HasIdentity,
		CanBeHeld: tc.CanBeHeld,
		RequiresParsing: tc.RequiresParsing,
		HasLinearDecodingPressure: tc.HasLinearDecodingPressure,
		StableOntologyReference: tc.StableOntologyReference,
		DimensionalityWhileEditing: tc.DimensionalityWhileEditing,
		IsOpenWorld: tc.IsOpenWorld,
		IsClosedWorld: tc.IsClosedWorld,
		DistanceFromConcept: tc.DistanceFromConcept,
		SortOrder: tc.SortOrder,
		FamilyFuedQuestion: nilIfEmpty(familyFuedQuestion),
		TopFamilyFeudAnswer: &topFamilyFeudAnswer,
		FamilyFeudMismatch: nilIfEmpty(familyFeudMismatch),
		HasGrammar: &hasGrammar,
		IsOpenClosedWorldConflicted: &isOpenClosedWorldConflicted,
		RelationshipToConcept: nilIfEmpty(relationshipToConcept),
	}
}

// =============================================================================
// FILE I/O (for LanguageCandidates)
// =============================================================================

// LoadRecords loads records from a JSON file
func LoadRecords(path string) ([]LanguageCandidate, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []LanguageCandidate
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveRecords saves computed records to a JSON file
func SaveRecords(path string, records []LanguageCandidate) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}