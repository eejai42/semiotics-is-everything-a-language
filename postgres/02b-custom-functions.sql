-- ============================================================================
-- CUSTOM FUNCTIONS - User-defined calculation functions
-- ============================================================================
-- These functions override the auto-generated functions in 02-create-functions.sql
-- to provide correct implementations based on the rulebook formulas.
-- ============================================================================

-- ============================================================================
-- DAG Level 1: Only references Level 0 (raw fields from base table)
-- ============================================================================

-- Formula: ="Is " & {{Name}} & " a language?"
CREATE OR REPLACE FUNCTION calc_language_candidates_family_fued_question(p_language_candidate_id TEXT)
RETURNS TEXT AS $$
  SELECT 'Is ' || COALESCE(name, '') || ' a language?'
  FROM language_candidates
  WHERE language_candidate_id = p_language_candidate_id;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Formula: ={{HasSyntax}} = TRUE()
CREATE OR REPLACE FUNCTION calc_language_candidates_has_grammar(p_language_candidate_id TEXT)
RETURNS BOOLEAN AS $$
  SELECT COALESCE(has_syntax, FALSE)
  FROM language_candidates
  WHERE language_candidate_id = p_language_candidate_id;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Formula: =IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")
CREATE OR REPLACE FUNCTION calc_language_candidates_relationship_to_concept(p_language_candidate_id TEXT)
RETURNS TEXT AS $$
  SELECT CASE
    WHEN distance_from_concept = 1 THEN 'IsMirrorOf'
    ELSE 'IsDescriptionOf'
  END
  FROM language_candidates
  WHERE language_candidate_id = p_language_candidate_id;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Formula: =AND({{IsOpenWorld}} = TRUE(), {{IsClosedWorld}} = TRUE())
CREATE OR REPLACE FUNCTION calc_language_candidates_is_open_closed_world_conflicted(p_language_candidate_id TEXT)
RETURNS BOOLEAN AS $$
  SELECT COALESCE(is_open_world, FALSE) AND COALESCE(is_closed_world, FALSE)
  FROM language_candidates
  WHERE language_candidate_id = p_language_candidate_id;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ============================================================================
-- DAG Level 2: References Level 0 (raw fields)
-- ============================================================================

-- Formula: =AND({{HasSyntax}}, NOT({{CanBeHeld}}), {{HasLinearDecodingPressure}},
--              {{RequiresParsing}}, {{StableOntologyReference}}, NOT({{HasIdentity}}),
--              {{DistanceFromConcept}}=2)
-- CREATE OR REPLACE FUNCTION calc_language_candidates_top_family_feud_answer(p_language_candidate_id TEXT)
-- RETURNS BOOLEAN AS $$
--   SELECT
--     COALESCE(has_syntax, FALSE)
--     AND NOT COALESCE(can_be_held, FALSE)
--     AND COALESCE(has_linear_decoding_pressure, FALSE)
--     AND COALESCE(requires_parsing, FALSE)
--     AND COALESCE(stable_ontology_reference, FALSE)
--     AND NOT COALESCE(has_identity, FALSE)
--     AND COALESCE(distance_from_concept = 2, FALSE)
--   FROM language_candidates
--   WHERE language_candidate_id = p_language_candidate_id;
-- $$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ============================================================================
-- DAG Level 3: References Level 2 (top_family_feud_answer) and Level 0 (raw fields)
-- ============================================================================

-- Formula: =IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
--   {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " &
--   IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") &
--   IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")
CREATE OR REPLACE FUNCTION calc_language_candidates_family_feud_mismatch(p_language_candidate_id TEXT)
RETURNS TEXT AS $$
  SELECT
    CASE
      WHEN COALESCE(calc_language_candidates_top_family_feud_answer(p_language_candidate_id), FALSE)
           = COALESCE(chosen_language_candidate, FALSE)
      THEN
        CASE
          WHEN calc_language_candidates_is_open_closed_world_conflicted(p_language_candidate_id)
          THEN ' - Open World vs. Closed World Conflict.'
          ELSE NULL
        END
      ELSE name || ' ' ||
           CASE WHEN calc_language_candidates_top_family_feud_answer(p_language_candidate_id) THEN 'Is' ELSE 'Isn''t' END ||
           ' a Family Feud Language, but ' ||
           CASE WHEN chosen_language_candidate THEN 'Is' ELSE 'Is Not' END ||
           ' marked as a ''Language Candidate.''' ||
           CASE
             WHEN calc_language_candidates_is_open_closed_world_conflicted(p_language_candidate_id)
             THEN ' - Open World vs. Closed World Conflict.'
             ELSE ''
           END
    END
  FROM language_candidates
  WHERE language_candidate_id = p_language_candidate_id;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;
