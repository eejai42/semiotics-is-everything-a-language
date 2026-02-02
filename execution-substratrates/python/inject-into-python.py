#!/usr/bin/env python3
"""
Generate Python calculation library from the Effortless Rulebook.

This script reads formulas from the rulebook and generates erb_calc.py
with proper calculation functions for all calculated fields.

Generated file is shared by Python and YAML substrates.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, get_candidate_name_from_cwd, handle_clean_arg
from orchestration.formula_parser import (
    parse_formula, compile_to_python, get_field_dependencies,
    to_snake_case, ASTNode, FieldRef, FuncCall, Concat, LiteralString
)


def get_calculated_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all calculated fields from a schema."""
    return [
        field for field in schema
        if field.get('type') == 'calculated' and field.get('formula')
    ]


def get_raw_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all raw fields from a schema."""
    return [field for field in schema if field.get('type') == 'raw']


def build_dag_levels(calculated_fields: List[Dict], raw_field_names: Set[str]) -> List[List[Dict]]:
    """
    Build DAG levels for calculated fields based on dependencies.

    Level 0: Raw fields (not returned, just used as base)
    Level 1+: Calculated fields ordered by dependency
    """
    # Parse formulas and get dependencies
    field_deps = {}
    for field in calculated_fields:
        formula = field.get('formula', '')
        try:
            ast = parse_formula(formula)
            deps = get_field_dependencies(ast)
            field_deps[field['name']] = set(to_snake_case(d) for d in deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field['name']] = set()

    # Build levels
    levels = []
    assigned = set(to_snake_case(name) for name in raw_field_names)
    remaining = {f['name']: f for f in calculated_fields}

    while remaining:
        # Find fields whose dependencies are all assigned
        current_level = []
        for name, field in list(remaining.items()):
            deps = field_deps.get(name, set())
            if deps <= assigned:
                current_level.append(field)

        if not current_level:
            # Circular dependency or missing field - add remaining to final level
            print(f"Warning: Could not resolve dependencies for: {list(remaining.keys())}")
            levels.append(list(remaining.values()))
            break

        # Add to level and mark as assigned
        levels.append(current_level)
        for field in current_level:
            assigned.add(to_snake_case(field['name']))
            del remaining[field['name']]

    return levels


def generate_function_params(deps: List[str]) -> str:
    """Generate function parameter list from dependencies."""
    if not deps:
        return ""
    params = [f"{to_snake_case(d)}" for d in deps]
    return ", ".join(params)


def generate_function_signature(field_name: str, deps: List[str], return_type: str) -> str:
    """Generate function signature with type hints."""
    func_name = f"calc_{to_snake_case(field_name)}"
    params = []
    for d in deps:
        param_name = to_snake_case(d)
        params.append(f"{param_name}")
    params_str = ", ".join(params) if params else ""
    return f"def {func_name}({params_str}):"


def generate_calc_function(field: Dict) -> str:
    """Generate a calculation function for a field."""
    name = field['name']
    formula = field.get('formula', '')
    datatype = field.get('datatype', 'string')

    try:
        ast = parse_formula(formula)
        deps = get_field_dependencies(ast)
        python_expr = compile_to_python(ast)
    except Exception as e:
        return f'''
def calc_{to_snake_case(name)}():
    """ERROR: Could not parse formula: {formula}
    Error: {e}
    """
    raise NotImplementedError("Formula parsing failed")
'''

    # Generate function
    lines = []
    sig = generate_function_signature(name, deps, datatype)
    lines.append(sig)

    # Docstring with formula (escape triple quotes and trailing double quotes)
    formula_escaped = formula.replace('\\', '\\\\').replace('"""', "'''")
    # If formula ends with a quote, add space to prevent """"
    if formula_escaped.endswith('"'):
        formula_escaped = formula_escaped + ' '
    lines.append(f'    """Formula: {formula_escaped}"""')

    # Return expression
    lines.append(f'    return {python_expr}')

    return '\n'.join(lines)


def generate_compute_all_function(
    calculated_fields: List[Dict],
    dag_levels: List[List[Dict]],
    raw_field_names: Set[str]
) -> str:
    """Generate the compute_all_calculated_fields function."""
    lines = []
    lines.append('def compute_all_calculated_fields(record: dict) -> dict:')
    lines.append('    """')
    lines.append('    Compute all calculated fields for a record.')
    lines.append('    Generated from rulebook formulas.')
    lines.append('    """')
    lines.append('    result = dict(record)')
    lines.append('')

    # Process each level
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append(f'    # Level {level_idx + 1} calculations')
        for field in level_fields:
            name = field['name']
            snake_name = to_snake_case(name)
            formula = field.get('formula', '')

            try:
                ast = parse_formula(formula)
                deps = get_field_dependencies(ast)
            except:
                deps = []

            # Generate function call
            if deps:
                args = []
                for dep in deps:
                    dep_snake = to_snake_case(dep)
                    args.append(f"result.get('{dep_snake}')")
                args_str = ', '.join(args)
                lines.append(f"    result['{snake_name}'] = calc_{snake_name}({args_str})")
            else:
                lines.append(f"    result['{snake_name}'] = calc_{snake_name}()")
        lines.append('')

    # Post-process: convert empty strings to None for string fields
    lines.append('    # Convert empty strings to None for string fields')
    lines.append("    for key in ['family_feud_mismatch']:")
    lines.append("        if result.get(key) == '':")
    lines.append('            result[key] = None')
    lines.append('')

    lines.append('    return result')

    return '\n'.join(lines)


def generate_erb_calc(rulebook: Dict) -> str:
    """Generate the complete erb_calc.py content."""
    lines = []

    # Header
    lines.append('"""')
    lines.append('ERB Calculation Library (GENERATED - DO NOT EDIT)')
    lines.append('=================================================')
    lines.append('Generated from: effortless-rulebook/effortless-rulebook.json')
    lines.append('')
    lines.append('This file contains pure functions that compute calculated fields')
    lines.append('from raw field values. Shared by Python and YAML substrates.')
    lines.append('"""')
    lines.append('')
    lines.append('from typing import Optional, Any')
    lines.append('')

    # Process LanguageCandidates table
    lc_table = rulebook.get('LanguageCandidates', {})
    schema = lc_table.get('schema', [])

    calculated_fields = get_calculated_fields(schema)
    raw_fields = get_raw_fields(schema)
    raw_field_names = {f['name'] for f in raw_fields}

    # Build DAG levels
    dag_levels = build_dag_levels(calculated_fields, raw_field_names)

    # Generate calculation functions for each level
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append('')
        lines.append('# ' + '=' * 77)
        lines.append(f'# LEVEL {level_idx + 1} CALCULATIONS')
        lines.append('# ' + '=' * 77)
        lines.append('')

        for field in level_fields:
            lines.append(generate_calc_function(field))
            lines.append('')

    # Generate compute_all function
    lines.append('')
    lines.append('# ' + '=' * 77)
    lines.append('# COMPOSITE FUNCTION')
    lines.append('# ' + '=' * 77)
    lines.append('')
    lines.append(generate_compute_all_function(calculated_fields, dag_levels, raw_field_names))

    return '\n'.join(lines)


def main():
    # Files actually generated by THIS script
    # Note: test-answers.json, test-results.md are test outputs, not generated here
    GENERATED_FILES = [
        'erb_calc.py',
    ]

    # Handle --clean argument
    if handle_clean_arg(GENERATED_FILES, "Python substrate: Removes generated calculation library and test outputs"):
        return

    candidate_name = get_candidate_name_from_cwd()
    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("Python Execution Substrate - Formula Compiler")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Get schema info
    lc_table = rulebook.get('LanguageCandidates', {})
    schema = lc_table.get('schema', [])
    calculated_fields = get_calculated_fields(schema)

    print(f"Found {len(calculated_fields)} calculated fields to compile")
    for field in calculated_fields:
        print(f"  - {field['name']}")

    print()
    print("-" * 70)
    print()

    # Generate erb_calc.py
    print("Generating erb_calc.py...")
    erb_calc_content = generate_erb_calc(rulebook)

    erb_calc_path = script_dir / "erb_calc.py"
    erb_calc_path.write_text(erb_calc_content, encoding='utf-8')
    print(f"Wrote: {erb_calc_path} ({len(erb_calc_content)} bytes)")

    print()
    print("=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
