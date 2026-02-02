/**
 * ERB SDK - GraphQL Resolvers (JavaScript)
 * =========================================
 * Generated from effortless-rulebook/effortless-rulebook.json
 *
 * All calculation functions are dynamically generated from rulebook formulas.
 */

// =============================================================================
// CALCULATED FIELD FUNCTIONS
// =============================================================================

// Level 1 calculations
// ----------------------------------------

/**
 * Formula: ="Is " & {{Name}} & " a language?"
 */
function calcFamilyFuedQuestion(candidate) {
  return `Is ${candidate.name || ""} a language?`;
}

/**
 * Formula: ={{HasSyntax}} = TRUE()
 */
function calcHasGrammar(candidate) {
  return (candidate.hasSyntax === true);
}

/**
 * Formula: =AND({{IsOpenWorld}}, {{IsClosedWorld}})
 */
function calcIsOpenClosedWorldConflicted(candidate) {
  return ((candidate.isOpenWorld === true) && (candidate.isClosedWorld === true));
}

/**
 * Formula: ={{DistanceFromConcept}} > 1
 */
function calcIsDescriptionOf(candidate) {
  return (candidate.distanceFromConcept > 1);
}

/**
 * Formula: =IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")
 */
function calcRelationshipToConcept(candidate) {
  return ((candidate.distanceFromConcept === 1) ? 'IsMirrorOf' : 'IsDescriptionOf');
}

// Level 2 calculations
// ----------------------------------------

/**
 * Formula: =AND(   {{HasSyntax}},   {{RequiresParsing}},   {{IsDescriptionOf}},   {{HasLinearDecodingPressure}},   {{ResolvesToAnAST}},   {{IsStableOntologyReference}},   NOT({{CanBeHeld}}),   NOT({{HasIdentity}}) )
 */
function calcTopFamilyFeudAnswer(candidate) {
  return ((candidate.hasSyntax === true) && (candidate.requiresParsing === true) && (candidate.isDescriptionOf === true) && (candidate.hasLinearDecodingPressure === true) && (candidate.resolvesToAnAST === true) && (candidate.isStableOntologyReference === true) && ((candidate.canBeHeld !== true) === true) && ((candidate.hasIdentity !== true) === true));
}

// Level 3 calculations
// ----------------------------------------

/**
 * Formula: =IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),   {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " &    IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")
 */
function calcFamilyFeudMismatch(candidate) {
  return `${(((candidate.topFamilyFeudAnswer === candidate.chosenLanguageCandidate) !== true) ? `${candidate.name || ""} ${(candidate.topFamilyFeudAnswer ? 'Is' : 'Isn\'t') || ""} a Family Feud Language, but ${(candidate.chosenLanguageCandidate ? 'Is' : 'Is Not') || ""} marked as a 'Language Candidate.'` : null) || ""}${(candidate.isOpenClosedWorldConflicted ? ' - Open World vs. Closed World Conflict.' : null) || ""}`;
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  calcFamilyFuedQuestion,
  calcHasGrammar,
  calcIsOpenClosedWorldConflicted,
  calcIsDescriptionOf,
  calcRelationshipToConcept,
  calcTopFamilyFeudAnswer,
  calcFamilyFeudMismatch,
};
