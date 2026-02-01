#!/usr/bin/env python3
"""
Take Test - Binary Execution Substrate

This script runs the test by:
1. Loading test-answers.json
2. Packing each record into a TestAnswer struct (bytes)
3. Calling the GENERATED assembly evaluators via ctypes
4. Unpacking results back to Python
5. Saving test-answers.json

The ABI (ARM64 Apple Silicon):
    - Input: TestAnswer struct pointer (x0 -> saved to x19)
    - Bool functions: return 0/1 in w0
    - String functions: return (ptr, len) in (x0, x1)
"""

import ctypes
import json
import platform
import re
import struct
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook


# =============================================================================
# DATA TYPES (must match inject-into-binary.py)
# =============================================================================

class DataType(Enum):
    BOOL = auto()
    INT = auto()
    STRING = auto()
    NULL = auto()


@dataclass
class FieldInfo:
    name: str
    datatype: DataType
    offset: int
    size: int
    json_name: str  # Original JSON field name for lookups


# =============================================================================
# FIELD NAME NORMALIZATION (must match inject-into-binary.py)
# =============================================================================

FIELD_NAME_MAP = {
    'NAME': 'name',
    'CATEGORY': 'category',
    'HASSYNTAX': 'has_syntax',
    'HASIDENTITY': 'has_identity',
    'CANBEHELD': 'can_be_held',
    'REQUIRESPARSING': 'requires_parsing',
    'MEANINGISSERIALIZED': 'meaning_is_serialized',
    'ISONGOLOGYDESCRIPTOR': 'is_ongology_descriptor',
    'CHOSENLANGUAGECANDIDATE': 'chosen_language_candidate',
    'DISTANCEFROMCONCEPT': 'distance_from_concept',
    'ISOPENWORLD': 'is_open_world',
    'ISCLOSEDWORLD': 'is_closed_world',
    'SORTORDER': 'sort_order',
    'TOPFAMILYFEUDANSWER': 'top_family_feud_answer',
    'ISOPENCLOTEDWORLDCONFLICTED': 'is_open_closed_world_conflicted',
    'ISOPENCLOSEDWORLDCONFLICTED': 'is_open_closed_world_conflicted',
}


def normalize_field_name(name: str) -> str:
    """Normalize field name to internal format (must match compiler)."""
    upper = name.replace(' ', '').upper()
    if upper in FIELD_NAME_MAP:
        return FIELD_NAME_MAP[upper]
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return result


def json_key_to_snake(name: str) -> str:
    """Convert JSON key (snake_case) to normalized internal name."""
    return name.lower().replace(' ', '_')


# =============================================================================
# STRUCT LAYOUT COMPUTATION
# =============================================================================

def build_schema(columns: List[dict]) -> tuple:
    """
    Build schema with field offsets from column definitions.
    Must match the layout computed by inject-into-binary.py.

    Returns: (schema dict, total struct size)
    """
    schema = {}
    offset = 0

    for col in columns:
        name = col.get('name', '')
        field_name = normalize_field_name(name)
        datatype_str = col.get('datatype', 'string').lower()

        if datatype_str == 'boolean':
            dt = DataType.BOOL
            size = 1
        elif datatype_str == 'integer':
            dt = DataType.INT
            size = 8
        else:  # string
            dt = DataType.STRING
            size = 16  # ptr + len

        # Align offset (must match compiler)
        if dt == DataType.INT or dt == DataType.STRING:
            offset = (offset + 7) & ~7  # 8-byte align

        schema[field_name] = FieldInfo(
            name=field_name,
            datatype=dt,
            offset=offset,
            size=size,
            json_name=json_key_to_snake(name)
        )
        offset += size

    # Final size with alignment
    total_size = (offset + 7) & ~7
    return schema, total_size


# =============================================================================
# STRUCT PACKING
# =============================================================================

class StringTable:
    """Manages string interning for struct packing."""

    def __init__(self):
        self.strings: List[bytes] = []
        self.buffers: List[ctypes.c_char_p] = []

    def intern(self, s: str) -> tuple:
        """Intern a string, return (ptr, len)."""
        encoded = s.encode('utf-8')
        # Create a ctypes buffer that won't be garbage collected
        buf = ctypes.create_string_buffer(encoded)
        self.buffers.append(buf)
        ptr = ctypes.addressof(buf)
        return (ptr, len(encoded))


def pack_test_answer(record: dict, schema: Dict[str, FieldInfo],
                     total_size: int, string_table: StringTable) -> bytes:
    """
    Pack a JSON record into TestAnswer struct bytes.
    """
    # Create zeroed buffer
    buf = bytearray(total_size)

    for field_name, info in schema.items():
        # Map JSON key variations
        json_key = info.json_name

        # Try multiple key formats
        value = None
        for key in [json_key, field_name, info.json_name.replace('_', '')]:
            if key in record:
                value = record[key]
                break

        if value is None:
            # Field not in record, leave as zeros (null)
            continue

        if info.datatype == DataType.BOOL:
            bool_val = 1 if value else 0
            struct.pack_into('B', buf, info.offset, bool_val)

        elif info.datatype == DataType.INT:
            int_val = int(value) if value is not None else 0
            struct.pack_into('<q', buf, info.offset, int_val)

        elif info.datatype == DataType.STRING:
            str_val = str(value) if value is not None else ""
            ptr, length = string_table.intern(str_val)
            struct.pack_into('<Q', buf, info.offset, ptr)      # ptr
            struct.pack_into('<Q', buf, info.offset + 8, length)  # len

    return bytes(buf)


# =============================================================================
# LIBRARY LOADING AND FUNCTION CALLING
# =============================================================================

def load_library(lib_path: Path) -> ctypes.CDLL:
    """Load the generated assembly library."""
    if not lib_path.exists():
        raise FileNotFoundError(f"Library not found: {lib_path}")
    return ctypes.CDLL(str(lib_path))


def setup_function(lib: ctypes.CDLL, func_name: str, returns_string: bool):
    """Configure a function's signature."""
    try:
        func = getattr(lib, func_name)
        func.argtypes = [ctypes.c_void_p]  # TestAnswer* pointer

        if returns_string:
            # String functions return (ptr, len) in (x0, x1)
            # We can use a structure or just get x0 as pointer
            func.restype = ctypes.c_uint64  # Just get x0 for now
        else:
            # Bool functions return 0/1 in w0
            func.restype = ctypes.c_int

        return func
    except AttributeError:
        return None


class StringResult(ctypes.Structure):
    """Structure to capture both ptr (x0) and len (x1) return values."""
    _fields_ = [("ptr", ctypes.c_uint64), ("len", ctypes.c_uint64)]


def call_string_function(lib: ctypes.CDLL, func_name: str, struct_ptr: int) -> str:
    """
    Call a string-returning function.

    The ARM64 assembly returns ptr in x0, len in x1.
    We use a structure return type to capture both values.
    """
    func = getattr(lib, func_name)
    func.argtypes = [ctypes.c_void_p]
    # Use StringResult structure to capture both x0 and x1
    func.restype = StringResult

    # Call the function
    result = func(struct_ptr)

    if result.ptr == 0 or result.len == 0:
        return ""

    # Read exactly 'len' bytes from the pointer
    try:
        raw = ctypes.string_at(result.ptr, result.len)
        return raw.decode('utf-8', errors='replace')
    except Exception:
        return ""


def call_bool_function(lib: ctypes.CDLL, func_name: str, struct_ptr: int) -> bool:
    """Call a bool-returning function."""
    func = getattr(lib, func_name)
    func.argtypes = [ctypes.c_void_p]
    func.restype = ctypes.c_int

    result = func(struct_ptr)
    return bool(result)


# =============================================================================
# CALCULATED FIELD DEFINITIONS
# =============================================================================

# Map of calculated field names to their function names and return types
# Note: On macOS, ctypes automatically adds underscore prefix to symbol names
CALCULATED_FIELDS = {
    'family_fued_question': ('eval_family_fued_question', 'string'),
    'top_family_feud_answer': ('eval_top_family_feud_answer', 'bool'),
    'family_feud_mismatch': ('eval_family_feud_mismatch', 'string'),
    'has_grammar': ('eval_has_grammar', 'bool'),
    'is_open_closed_world_conflicted': ('eval_is_open_closed_world_conflicted', 'bool'),
    'relationship_to_concept': ('eval_relationship_to_concept', 'string'),
}

# Map internal names to JSON output keys
JSON_OUTPUT_KEYS = {
    'family_fued_question': 'family_fued_question',
    'top_family_feud_answer': 'top_family_feud_answer',
    'family_feud_mismatch': 'family_feud_mismatch',
    'has_grammar': 'has_grammar',
    'is_open_closed_world_conflicted': 'is_open_closed_world_conflicted',
    'relationship_to_concept': 'relationship_to_concept',
}


# =============================================================================
# MAIN
# =============================================================================

def main():
    script_dir = Path(__file__).resolve().parent
    test_file = script_dir / "test-answers.json"

    print("=" * 70)
    print("Binary Execution Substrate - Test Execution")
    print("=" * 70)
    print()

    # Determine library path
    system = platform.system()
    if system == "Darwin":
        lib_name = "erb_calc.dylib"
    elif system == "Linux":
        lib_name = "erb_calc.so"
    else:
        print(f"ERROR: Unsupported platform: {system}")
        sys.exit(1)

    lib_path = script_dir / lib_name

    # Check library exists
    print(f"Loading library: {lib_path}")
    if not lib_path.exists():
        print(f"ERROR: Library not found at {lib_path}")
        print("Run: python inject-into-binary.py first")
        sys.exit(1)

    # Load the library
    try:
        lib = load_library(lib_path)
        print("Library loaded successfully")
    except Exception as e:
        print(f"ERROR: Failed to load library: {e}")
        sys.exit(1)

    # Load rulebook to get schema
    print("\nLoading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Build schema
    language_candidates = rulebook.get("LanguageCandidates", {})
    columns = language_candidates.get("schema", [])
    schema, struct_size = build_schema(columns)
    print(f"Schema built: {len(schema)} fields, struct size: {struct_size} bytes")

    # Load test data
    print(f"\nLoading test data: {test_file}")
    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        sys.exit(1)

    with open(test_file, "r") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    # Verify calculated field functions exist
    print("\nVerifying assembly functions...")
    available_funcs = {}
    for field_name, (func_name, ret_type) in CALCULATED_FIELDS.items():
        try:
            func = getattr(lib, func_name)
            available_funcs[field_name] = (func_name, ret_type)
            print(f"  Found: {func_name} -> {ret_type}")
        except AttributeError:
            print(f"  Missing: {func_name}")

    if not available_funcs:
        print("ERROR: No assembly functions found!")
        sys.exit(1)

    # Process each record
    print(f"\nProcessing {len(data)} records...")

    # Keep all string tables alive for the duration
    all_string_tables = []

    for i, record in enumerate(data):
        try:
            # Create string table for this record (keep reference alive)
            string_table = StringTable()
            all_string_tables.append(string_table)

            # Pack record to struct bytes
            struct_bytes = pack_test_answer(record, schema, struct_size, string_table)

            # Create ctypes buffer from bytes
            struct_buf = ctypes.create_string_buffer(struct_bytes, struct_size)
            struct_ptr = ctypes.addressof(struct_buf)

            # Call each available function
            for field_name, (func_name, ret_type) in available_funcs.items():
                json_key = JSON_OUTPUT_KEYS.get(field_name, field_name)

                try:
                    if ret_type == 'bool':
                        result = call_bool_function(lib, func_name, struct_ptr)
                    else:  # string
                        result = call_string_function(lib, func_name, struct_ptr)

                    record[json_key] = result
                except Exception as e:
                    print(f"  Warning: Error calling {func_name} for record {i}: {e}")
                    import traceback
                    traceback.print_exc()

            if (i + 1) % 5 == 0 or i == len(data) - 1:
                print(f"  Processed {i + 1}/{len(data)} records")
        except Exception as e:
            print(f"ERROR processing record {i}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save results
    print(f"\nSaving results to: {test_file}")
    with open(test_file, "w") as f:
        json.dump(data, f, indent=2)

    print("\nTest execution complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
