// ERB SDK - Go Test Runner (GENERATED - DO NOT EDIT)
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	scriptDir, err := os.Getwd()
	if err != nil {
		fmt.Printf("Failed to get working directory: %v\n", err)
		os.Exit(1)
	}

	// Paths
	blankTestPath := filepath.Join(scriptDir, "..", "..", "testing", "blank-test.json")
	answersPath := filepath.Join(scriptDir, "test-answers.json")

	// Step 1: Load blank test data
	records, err := LoadRecords(blankTestPath)
	if err != nil {
		fmt.Printf("Failed to load blank test: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Golang substrate: Processing %d records...\n", len(records))

	// Step 2: Compute all calculated fields using the SDK
	var computed []LanguageCandidate
	for _, r := range records {
		computed = append(computed, *r.ComputeAll())
	}

	// Step 3: Save test answers
	if err := SaveRecords(answersPath, computed); err != nil {
		fmt.Printf("Failed to save test answers: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Golang substrate: Saved results to %s\n", answersPath)
}
