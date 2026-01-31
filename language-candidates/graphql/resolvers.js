/**
 * ERB SDK - GraphQL Resolvers (JavaScript)
 * =========================================
 * Mirrors the PostgreSQL functions from postgres/02-create-functions.sql
 * Source: effortless-rulebook/effortless-rulebook.json
 *
 * DAG Execution Order:
 *   Level 0: Raw fields
 *   Level 1: categoryContainsLanguage, hasGrammar, relationshipToConcept, familyFuedQuestion
 *   Level 2: isAFamilyFeudTopAnswer (depends on categoryContainsLanguage)
 *   Level 3: familyFeudMismatch (depends on isAFamilyFeudTopAnswer)
 */

// =============================================================================
// CALCULATED FIELD FUNCTIONS - Mirrors PostgreSQL functions exactly
// =============================================================================

// Level 1: Simple calculations on raw fields only
// ------------------------------------------------

/**
 * Mirrors: calc_language_candidates_category_contains_language()
 * Formula: FIND("language", LOWER(category)) > 0
 */
function calcCategoryContainsLanguage(candidate) {
  if (!candidate.category) return false;
  return candidate.category.toLowerCase().includes('language');
}

/**
 * Mirrors: calc_language_candidates_has_grammar()
 * Formula: CAST(has_syntax AS TEXT)
 */
function calcHasGrammar(candidate) {
  if (!candidate.hasSyntax) return '';
  return 'true';
}

/**
 * Mirrors: calc_language_candidates_relationship_to_concept()
 * Formula: IF(distance_from_concept = 1, "IsMirrorOf", "IsDescriptionOf")
 */
function calcRelationshipToConcept(candidate) {
  if (candidate.distanceFromConcept === 1) return 'IsMirrorOf';
  return 'IsDescriptionOf';
}

/**
 * Mirrors: calc_language_candidates_family_fued_question()
 * Formula: "Is " & name & " a language?"
 */
function calcFamilyFuedQuestion(candidate) {
  return `Is ${candidate.name || ''} a language?`;
}

// Level 2: Depends on Level 1 calculations
// ----------------------------------------

/**
 * Mirrors: calc_language_candidates_is_a_family_feud_top_answer()
 * Formula: AND(categoryContainsLanguage, hasSyntax, NOT(canBeHeld), ...)
 */
function calcIsAFamilyFeudTopAnswer(candidate) {
  // Depends on Level 1 calc
  const categoryContainsLanguage = calcCategoryContainsLanguage(candidate);

  return (
    categoryContainsLanguage &&
    (candidate.hasSyntax || false) &&
    !(candidate.canBeHeld || false) &&
    (candidate.meaningIsSerialized || false) &&
    (candidate.requiresParsing || false) &&
    (candidate.isOngologyDescriptor || false) &&
    !(candidate.hasIdentity || false) &&
    candidate.distanceFromConcept === 2
  );
}

// Level 3: Depends on Level 2 calculations
// ----------------------------------------

/**
 * Mirrors: calc_language_candidates_family_feud_mismatch()
 * Formula: IF(is_a_family_feud_top_answer != chosen_language_candidate, ...)
 */
function calcFamilyFeudMismatch(candidate) {
  // Depends on Level 2 calc
  const isTopAnswer = calcIsAFamilyFeudTopAnswer(candidate);
  const chosen = candidate.chosenLanguageCandidate || false;

  if (isTopAnswer !== chosen) {
    const isWord = isTopAnswer ? 'Is' : "Isn't";
    const markedWord = chosen ? 'Is' : 'Is Not';
    return `${candidate.name || ''} ${isWord} a Family Feud Language, but ${markedWord} marked as a 'Language Candidate.'`;
  }
  return null;
}

// =============================================================================
// CORE LANGUAGE DEFINITION (from the rulebook)
// =============================================================================

/**
 * Language(x) := HasSyntax(x) AND RequiresParsing(x) AND Meaning_Is_Serialized(x) AND IsOngologyDescriptor(x)
 */
function isLanguage(candidate) {
  return (
    (candidate.hasSyntax || false) &&
    (candidate.requiresParsing || false) &&
    (candidate.meaningIsSerialized || false) &&
    (candidate.isOngologyDescriptor || false)
  );
}

// =============================================================================
// GRAPHQL RESOLVERS
// =============================================================================

const resolvers = {
  Query: {
    languageCandidates: (_, __, { dataSources }) => {
      return dataSources.rulebook.getLanguageCandidates();
    },
    languageCandidate: (_, { id }, { dataSources }) => {
      return dataSources.rulebook.getLanguageCandidateById(id);
    },
    isEverythingALanguageSteps: (_, __, { dataSources }) => {
      return dataSources.rulebook.getIsEverythingALanguageSteps();
    },
    isLanguage: (_, { id }, { dataSources }) => {
      const candidate = dataSources.rulebook.getLanguageCandidateById(id);
      return candidate ? isLanguage(candidate) : false;
    },
  },

  LanguageCandidate: {
    // Level 1 calculated fields
    categoryContainsLanguage: (parent) => calcCategoryContainsLanguage(parent),
    hasGrammar: (parent) => calcHasGrammar(parent),
    relationshipToConcept: (parent) => calcRelationshipToConcept(parent),
    familyFuedQuestion: (parent) => calcFamilyFuedQuestion(parent),

    // Level 2 calculated fields
    isAFamilyFeudTopAnswer: (parent) => calcIsAFamilyFeudTopAnswer(parent),

    // Level 3 calculated fields
    familyFeudMismatch: (parent) => calcFamilyFeudMismatch(parent),
  },

  IsEverythingALanguage: {
    relatedCandidate: (parent, _, { dataSources }) => {
      if (!parent.relatedCandidateId) return null;
      return dataSources.rulebook.getLanguageCandidateById(parent.relatedCandidateId);
    },
  },
};

module.exports = {
  resolvers,
  // Export calc functions for direct use
  calcCategoryContainsLanguage,
  calcHasGrammar,
  calcRelationshipToConcept,
  calcFamilyFuedQuestion,
  calcIsAFamilyFeudTopAnswer,
  calcFamilyFeudMismatch,
  isLanguage,
};
