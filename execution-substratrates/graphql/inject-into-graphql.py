#!/usr/bin/env python3
"""
Generate GraphQL schema and resolvers from the Effortless Rulebook.

This script runs from /execution-substratrates/graphql/ and reads
the rulebook from ../../effortless-rulebook/effortless-rulebook.json

Generates:
- schema.graphql: GraphQL type definitions
- resolvers.js: JavaScript resolver functions for calculated fields
"""

import sys
import re
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, write_readme, get_candidate_name_from_cwd
from orchestration.formula_parser import (
    parse_formula, compile_to_javascript, get_field_dependencies,
    to_snake_case, ASTNode
)


def to_camel_case(name):
    """Convert PascalCase or snake_case to camelCase."""
    # Handle snake_case
    if '_' in name:
        parts = name.split('_')
        return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
    # Handle PascalCase
    return name[0].lower() + name[1:] if name else name


def to_pascal_case(name):
    """Convert snake_case to PascalCase."""
    if '_' in name:
        return ''.join(word.capitalize() for word in name.split('_'))
    return name[0].upper() + name[1:] if name else name


def datatype_to_graphql(datatype, nullable=True):
    """Convert rulebook datatype to GraphQL type."""
    type_map = {
        'string': 'String',
        'boolean': 'Boolean',
        'integer': 'Int',
        'number': 'Float',
    }
    gql_type = type_map.get(datatype, 'String')
    return gql_type if nullable else f'{gql_type}!'


def generate_schema(rulebook):
    """Generate GraphQL schema from rulebook."""
    lines = [
        '# ERB Schema - GraphQL Implementation',
        '# Generated from effortless-rulebook/effortless-rulebook.json',
        '#',
        '# DAG Execution Order:',
        '#   Level 0: Raw fields',
        '#   Level 1: familyFuedQuestion, hasGrammar, relationshipToConcept',
        '#   Level 2: topFamilyFeudAnswer (depends on raw fields)',
        '#   Level 3: familyFeudMismatch (depends on topFamilyFeudAnswer)',
        '',
        'type Query {',
        '  """Get all language candidates with calculated fields"""',
        '  languageCandidates: [LanguageCandidate!]!',
        '',
        '  """Get a single language candidate by ID"""',
        '  languageCandidate(id: ID!): LanguageCandidate',
        '}',
        '',
    ]

    # Generate types for each table
    for table_name, table_data in rulebook.items():
        if table_name.startswith('$') or table_name.startswith('_') or not isinstance(table_data, dict):
            continue
        if 'schema' not in table_data:
            continue

        schema = table_data['schema']
        type_name = to_pascal_case(table_name)

        lines.append(f'"""Entity: {table_name}"""')
        lines.append(f'type {type_name} {{')

        # Separate raw and calculated fields
        raw_fields = []
        calculated_fields = []

        for field in schema:
            field_name = to_camel_case(field['name'])
            gql_type = datatype_to_graphql(field.get('datatype', 'string'), field.get('nullable', True))
            field_type = field.get('type', 'raw')

            if field_type == 'calculated':
                calculated_fields.append((field_name, gql_type, field.get('formula', '')))
            else:
                raw_fields.append((field_name, gql_type))

        # Write raw fields
        lines.append('  # Raw Fields')
        for field_name, gql_type in raw_fields:
            lines.append(f'  {field_name}: {gql_type}')

        # Write calculated fields
        if calculated_fields:
            lines.append('')
            lines.append('  # Calculated Fields')
            for field_name, gql_type, formula in calculated_fields:
                # Add formula as comment
                formula_comment = formula.replace('\n', ' ').strip()[:60] + '...' if len(formula) > 60 else formula.replace('\n', ' ').strip()
                lines.append(f'  """Formula: {formula_comment}"""')
                lines.append(f'  {field_name}: {gql_type}')

        lines.append('}')
        lines.append('')

    return '\n'.join(lines)


def get_calculated_fields(schema):
    """Extract all calculated fields from a schema."""
    return [
        field for field in schema
        if field.get('type') == 'calculated' and field.get('formula')
    ]


def get_raw_fields(schema):
    """Extract all raw fields from a schema."""
    return [field for field in schema if field.get('type') == 'raw']


def build_dag_levels(calculated_fields, raw_field_names):
    """Build DAG levels for calculated fields based on dependencies."""
    field_deps = {}
    for field in calculated_fields:
        formula = field.get('formula', '')
        try:
            ast = parse_formula(formula)
            deps = get_field_dependencies(ast)
            field_deps[field['name']] = set(d for d in deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field['name']] = set()

    levels = []
    assigned = set(raw_field_names)
    remaining = {f['name']: f for f in calculated_fields}

    while remaining:
        current_level = []
        for name, field in list(remaining.items()):
            deps = field_deps.get(name, set())
            if deps <= assigned:
                current_level.append(field)

        if not current_level:
            print(f"Warning: Could not resolve dependencies for: {list(remaining.keys())}")
            levels.append(list(remaining.values()))
            break

        levels.append(current_level)
        for field in current_level:
            assigned.add(field['name'])
            del remaining[field['name']]

    return levels


def generate_js_function(field):
    """Generate a JavaScript calculation function for a field."""
    name = field['name']
    formula = field.get('formula', '')
    func_name = 'calc' + name

    try:
        ast = parse_formula(formula)
        js_expr = compile_to_javascript(ast, 'candidate')
    except Exception as e:
        return f'''/**
 * ERROR: Could not parse formula: {formula}
 * Error: {e}
 */
function {func_name}(candidate) {{
  throw new Error("Formula parsing failed");
}}'''

    # Escape formula for comment
    formula_escaped = formula.replace('*/', '* /').replace('\n', ' ')

    return f'''/**
 * Formula: {formula_escaped}
 */
function {func_name}(candidate) {{
  return {js_expr};
}}'''


def generate_resolvers(rulebook):
    """Generate JavaScript resolver functions from rulebook."""
    lines = [
        '/**',
        ' * ERB SDK - GraphQL Resolvers (JavaScript)',
        ' * =========================================',
        ' * Generated from effortless-rulebook/effortless-rulebook.json',
        ' *',
        ' * All calculation functions are dynamically generated from rulebook formulas.',
        ' */',
        '',
    ]

    # Get schema
    lc_table = rulebook.get('LanguageCandidates', {})
    schema = lc_table.get('schema', [])
    raw_fields = get_raw_fields(schema)
    calculated_fields = get_calculated_fields(schema)
    raw_field_names = {f['name'] for f in raw_fields}

    # Build DAG
    dag_levels = build_dag_levels(calculated_fields, raw_field_names)

    lines.append('// =============================================================================')
    lines.append('// CALCULATED FIELD FUNCTIONS')
    lines.append('// =============================================================================')
    lines.append('')

    # Generate functions for each level
    func_names = []
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append(f'// Level {level_idx + 1} calculations')
        lines.append('// ' + '-' * 40)
        lines.append('')

        for field in level_fields:
            func_code = generate_js_function(field)
            lines.append(func_code)
            lines.append('')
            func_names.append('calc' + field['name'])

    # Generate exports
    lines.append('// =============================================================================')
    lines.append('// EXPORTS')
    lines.append('// =============================================================================')
    lines.append('')
    lines.append('module.exports = {')
    for func_name in func_names:
        lines.append(f'  {func_name},')
    lines.append('};')
    lines.append('')

    return '\n'.join(lines)


def main():
    candidate_name = get_candidate_name_from_cwd()
    print(f"Generating {candidate_name} from rulebook...")

    # Load the rulebook
    try:
        rulebook = load_rulebook()
        print(f"Loaded rulebook with {len(rulebook)} top-level keys")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Generate schema.graphql
    schema_content = generate_schema(rulebook)
    schema_path = Path('schema.graphql')
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(schema_content)
    print(f"Generated: {schema_path}")

    # Generate resolvers.js
    resolvers_content = generate_resolvers(rulebook)
    resolvers_path = Path('resolvers.js')
    with open(resolvers_path, 'w', encoding='utf-8') as f:
        f.write(resolvers_content)
    print(f"Generated: {resolvers_path}")

    # Write README
    write_readme(
        candidate_name,
        "GraphQL schema and resolvers generated from the Effortless Rulebook.\n\n"
        "This substrate generates:\n"
        "- `schema.graphql`: GraphQL type definitions for all entities\n"
        "- `resolvers.js`: JavaScript resolver functions for calculated fields\n\n"
        "The resolvers implement the exact same calculation logic as the PostgreSQL functions, "
        "enabling consistent results across all execution substrates.",
        technology="""**GraphQL** is a query language and runtime for APIs developed by Facebook (2012, open-sourced 2015). Unlike REST's fixed endpoints, GraphQL lets clients request exactly the fields they need in a single query, with strong typing enforced by a schema.

Key characteristics:
- **Schema-first**: Types, queries, and mutations are defined in SDL (Schema Definition Language)
- **Hierarchical queries**: Clients can traverse relationships in a single request
- **Strong typing**: Every field has a type; the schema serves as a contract and documentation
- **Introspection**: Clients can query the schema itself to discover available types and fields

This ERB GraphQL substrate generates both the schema definitions and the JavaScript resolver functions needed to compute calculated fields."""
    )

    print(f"\nDone generating {candidate_name}.")


if __name__ == "__main__":
    main()
