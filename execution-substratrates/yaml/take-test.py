#!/usr/bin/env python3
"""
YAML Substrate Test Runner
===========================
Loads blank-test.json, reads schema.yaml for field definitions,
computes all calculated fields using the shared erb_calc.py library,
and saves the results to test-answers.json.

The schema.yaml serves as documentation and contract — this script
uses the shared calculation library to ensure identical results
with the Python substrate.
"""

import json
import os
import sys

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add Python substrate directory to path for shared library
python_substrate_dir = os.path.join(script_dir, "..", "python")
sys.path.insert(0, python_substrate_dir)

# Try to import yaml for schema reading (optional - for logging purposes)
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Schema details will not be logged.")

from erb_calc import compute_all_calculated_fields


def load_schema(schema_path: str) -> dict:
    """Load and parse the YAML schema."""
    if not YAML_AVAILABLE:
        return {}

    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def get_calculated_fields_from_schema(schema: dict) -> list:
    """
    Extract the list of calculated field names from the schema.
    Returns fields in DAG order (level 1, then level 2, then level 3).
    """
    calculated_fields = []

    if 'entities' not in schema:
        return calculated_fields

    for entity_name, entity_def in schema['entities'].items():
        if 'calculated_fields' in entity_def:
            # Sort by dag_level if present
            fields_with_level = []
            for field_name, field_def in entity_def['calculated_fields'].items():
                if isinstance(field_def, dict):
                    level = field_def.get('dag_level', 99)
                    fields_with_level.append((level, field_name, field_def))

            fields_with_level.sort(key=lambda x: x[0])
            calculated_fields.extend([(name, defn) for level, name, defn in fields_with_level])

    return calculated_fields


def main():
    # Input/output paths
    input_path = os.path.join(script_dir, "test-answers.json")
    output_path = os.path.join(script_dir, "test-answers.json")
    schema_path = os.path.join(script_dir, "schema.yaml")

    # Load schema (for documentation/logging purposes)
    if YAML_AVAILABLE and os.path.exists(schema_path):
        schema = load_schema(schema_path)
        calculated_fields = get_calculated_fields_from_schema(schema)

        print(f"YAML substrate: Loaded schema with {len(calculated_fields)} calculated fields")
        for name, defn in calculated_fields:
            formula = defn.get('formula', 'N/A') if isinstance(defn, dict) else 'N/A'
            # Truncate long formulas for display
            formula_str = str(formula).replace('\n', ' ').strip()
            if len(formula_str) > 50:
                formula_str = formula_str[:47] + "..."
            print(f"  - {name}: {formula_str}")
    else:
        print("YAML substrate: Schema not loaded (PyYAML not available or schema.yaml missing)")

    # Load test data
    with open(input_path, 'r') as f:
        records = json.load(f)

    print(f"YAML substrate: Processing {len(records)} records...")

    # Compute all calculated fields for each record using shared library
    computed_records = []
    for record in records:
        computed = compute_all_calculated_fields(record)
        computed_records.append(computed)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(computed_records, f, indent=2)

    print(f"YAML substrate: Saved results to {output_path}")


if __name__ == "__main__":
    main()
