"""
ERB Calculation Library (GENERATED - DO NOT EDIT)
=================================================
Generated from: effortless-rulebook/effortless-rulebook.json

This file contains pure functions that compute calculated fields
from raw field values. Shared by Python and YAML substrates.
"""

from typing import Optional, Any


# =============================================================================
# LEVEL 1 CALCULATIONS
# =============================================================================

def calc_family_fued_question(name):
    """Formula: ="Is " & {{Name}} & " a language?" """
    return ('Is ' + str(name or "") + ' a language?')

def calc_has_grammar(has_syntax):
    """Formula: ={{HasSyntax}} = TRUE()"""
    return (has_syntax == True)

def calc_is_open_closed_world_conflicted(is_open_world, is_closed_world):
    """Formula: =AND({{IsOpenWorld}}, {{IsClosedWorld}})"""
    return ((is_open_world is True) and (is_closed_world is True))

def calc_is_description_of(distance_from_concept):
    """Formula: ={{DistanceFromConcept}} > 1"""
    return (distance_from_concept > 1)

def calc_relationship_to_concept(distance_from_concept):
    """Formula: =IF({{DistanceFromConcept}} = 1, "IsMirrorOf", "IsDescriptionOf")"""
    return ('IsMirrorOf' if (distance_from_concept == 1) else 'IsDescriptionOf')


# =============================================================================
# LEVEL 2 CALCULATIONS
# =============================================================================

def calc_top_family_feud_answer(has_syntax, requires_parsing, is_description_of, has_linear_decoding_pressure, is_stable_ontology_reference, can_be_held, has_identity):
    """Formula: =AND(
  {{HasSyntax}},
  {{RequiresParsing}},
  {{IsDescriptionOf}},
  {{HasLinearDecodingPressure}},
  {{IsStableOntologyReference}},
  NOT({{CanBeHeld}}),
  NOT({{HasIdentity}})
)"""
    return ((has_syntax is True) and (requires_parsing is True) and (is_description_of is True) and (has_linear_decoding_pressure is True) and (is_stable_ontology_reference is True) and (can_be_held is not True) and (has_identity is not True))


# =============================================================================
# LEVEL 3 CALCULATIONS
# =============================================================================

def calc_family_feud_mismatch(top_family_feud_answer, chosen_language_candidate, name, is_open_closed_world_conflicted):
    """Formula: =IF(NOT({{TopFamilyFeudAnswer}} = {{ChosenLanguageCandidate}}),
  {{Name}} & " " & IF({{TopFamilyFeudAnswer}}, "Is", "Isn't") & " a Family Feud Language, but " & 
  IF({{ChosenLanguageCandidate}}, "Is", "Is Not") & " marked as a 'Language Candidate.'") & IF({{IsOpenClosedWorldConflicted}}, " - Open World vs. Closed World Conflict.")"""
    return (str(((str(name or "") + ' ' + str(('Is' if top_family_feud_answer else "Isn't") if ('Is' if top_family_feud_answer else "Isn't") is not None else "") + ' a Family Feud Language, but ' + str(('Is' if chosen_language_candidate else 'Is Not') if ('Is' if chosen_language_candidate else 'Is Not') is not None else "") + " marked as a 'Language Candidate.'") if (not (top_family_feud_answer == chosen_language_candidate)) else None) if ((str(name or "") + ' ' + str(('Is' if top_family_feud_answer else "Isn't") if ('Is' if top_family_feud_answer else "Isn't") is not None else "") + ' a Family Feud Language, but ' + str(('Is' if chosen_language_candidate else 'Is Not') if ('Is' if chosen_language_candidate else 'Is Not') is not None else "") + " marked as a 'Language Candidate.'") if (not (top_family_feud_answer == chosen_language_candidate)) else None) is not None else "") + str((' - Open World vs. Closed World Conflict.' if is_open_closed_world_conflicted else None) if (' - Open World vs. Closed World Conflict.' if is_open_closed_world_conflicted else None) is not None else ""))


# =============================================================================
# COMPOSITE FUNCTION
# =============================================================================

def compute_all_calculated_fields(record: dict) -> dict:
    """
    Compute all calculated fields for a record.
    Generated from rulebook formulas.
    """
    result = dict(record)

    # Level 1 calculations
    result['family_fued_question'] = calc_family_fued_question(result.get('name'))
    result['has_grammar'] = calc_has_grammar(result.get('has_syntax'))
    result['is_open_closed_world_conflicted'] = calc_is_open_closed_world_conflicted(result.get('is_open_world'), result.get('is_closed_world'))
    result['is_description_of'] = calc_is_description_of(result.get('distance_from_concept'))
    result['relationship_to_concept'] = calc_relationship_to_concept(result.get('distance_from_concept'))

    # Level 2 calculations
    result['top_family_feud_answer'] = calc_top_family_feud_answer(result.get('has_syntax'), result.get('requires_parsing'), result.get('is_description_of'), result.get('has_linear_decoding_pressure'), result.get('is_stable_ontology_reference'), result.get('can_be_held'), result.get('has_identity'))

    # Level 3 calculations
    result['family_feud_mismatch'] = calc_family_feud_mismatch(result.get('top_family_feud_answer'), result.get('chosen_language_candidate'), result.get('name'), result.get('is_open_closed_world_conflicted'))

    # Convert empty strings to None for string fields
    for key in ['family_feud_mismatch']:
        if result.get(key) == '':
            result[key] = None

    return result