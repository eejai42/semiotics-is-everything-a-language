// ERB SDK - Go Demo
package main

import (
	"fmt"
	"path/filepath"
	"sort"

	erb "erb_sdk"
)

func main() {
	// Load from rulebook
	rulebookPath := filepath.Join("..", "..", "effortless-rulebook", "effortless-rulebook.json")

	rulebook, err := erb.LoadFromRulebook(rulebookPath)
	if err != nil {
		fmt.Printf("Failed to load rulebook: %v\n", err)
		return
	}

	fmt.Printf("Loaded %d language candidates\n", len(rulebook.LanguageCandidates.Data))
	fmt.Printf("Loaded %d argument steps\n", len(rulebook.IsEverythingALanguage.Data))
	fmt.Println()

	// Sort by sort_order
	candidates := rulebook.LanguageCandidates.Data
	sort.Slice(candidates, func(i, j int) bool {
		iOrder := 999
		jOrder := 999
		if candidates[i].SortOrder != nil {
			iOrder = *candidates[i].SortOrder
		}
		if candidates[j].SortOrder != nil {
			jOrder = *candidates[j].SortOrder
		}
		return iOrder < jOrder
	})

	// Show first candidate with all calculated fields
	if len(candidates) > 0 {
		c := candidates[0]
		name := ""
		if c.Name != nil {
			name = *c.Name
		}
		fmt.Printf("First candidate: %s\n", name)

		view := c.ToView()
		fmt.Printf("  language_candidate_id: %s\n", view.LanguageCandidateID)
		if view.Name != nil {
			fmt.Printf("  name: %s\n", *view.Name)
		}
		if view.Category != nil {
			fmt.Printf("  category: %s\n", *view.Category)
		}
		fmt.Printf("  category_contains_language: %v\n", view.CategoryContainsLanguage)
		fmt.Printf("  has_grammar: %s\n", view.HasGrammar)
		fmt.Printf("  relationship_to_concept: %s\n", view.RelationshipToConcept)
		fmt.Printf("  family_fued_question: %s\n", view.FamilyFuedQuestion)
		fmt.Printf("  is_a_family_feud_top_answer: %v\n", view.IsAFamilyFeudTopAnswer)
		if view.FamilyFeudMismatch != nil {
			fmt.Printf("  family_feud_mismatch: %s\n", *view.FamilyFeudMismatch)
		} else {
			fmt.Printf("  family_feud_mismatch: null\n")
		}
	}
}
