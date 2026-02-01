#!/usr/bin/env python3
"""
RDF Execution Substrate - Formula-to-SPARQL Compiler

This compiler:
1. Reads the rulebook (schema + formulas + data)
2. Generates schema.ttl (RDFS schema - classes and properties)
3. Generates data.ttl (RDF triples - raw values only)
4. Generates queries.sparql (SPARQL CONSTRUCT queries for calculations)

The rulebook is the source of truth. RDF/SPARQL is derived, not authored.
This script is 100% domain-agnostic - all field names come from the rulebook.

Key difference from OWL substrate: Uses pure SPARQL CONSTRUCT instead of SHACL rules.
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook


# =============================================================================
# AST NODE TYPES (reused from OWL substrate)
# =============================================================================

@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass


@dataclass
class LiteralBool(ASTNode):
    value: bool


@dataclass
class LiteralInt(ASTNode):
    value: int


@dataclass
class LiteralString(ASTNode):
    value: str


@dataclass
class FieldRef(ASTNode):
    name: str  # Field name without {{ }}


@dataclass
class BinaryOp(ASTNode):
    op: str  # '=', '<>', '<', '<=', '>', '>='
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op: str  # 'NOT'
    operand: ASTNode


@dataclass
class FuncCall(ASTNode):
    name: str  # 'AND', 'OR', 'IF', 'LOWER', 'FIND'
    args: List[ASTNode]


@dataclass
class Concat(ASTNode):
    parts: List[ASTNode]


# =============================================================================
# LEXER
# =============================================================================

class TokenType(Enum):
    STRING = auto()
    NUMBER = auto()
    FIELD_REF = auto()
    FUNC_NAME = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    AMPERSAND = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int


def tokenize(formula: str) -> List[Token]:
    """Tokenize an Excel-dialect formula."""
    tokens = []

    # Remove leading = if present
    if formula.startswith('='):
        formula = formula[1:]

    i = 0
    while i < len(formula):
        c = formula[i]

        # Skip whitespace
        if c in ' \t\n\r':
            i += 1
            continue

        # String literal
        if c == '"':
            j = i + 1
            while j < len(formula) and formula[j] != '"':
                if formula[j] == '\\':
                    j += 2
                else:
                    j += 1
            if j >= len(formula):
                raise SyntaxError(f"Unterminated string at position {i}")
            value = formula[i+1:j]
            tokens.append(Token(TokenType.STRING, value, i))
            i = j + 1
            continue

        # Field reference {{Name}}
        if formula[i:i+2] == '{{':
            j = formula.find('}}', i)
            if j == -1:
                raise SyntaxError(f"Unterminated field reference at position {i}")
            field_name = formula[i+2:j]
            tokens.append(Token(TokenType.FIELD_REF, field_name, i))
            i = j + 2
            continue

        # Number
        if c.isdigit() or (c == '-' and i + 1 < len(formula) and formula[i+1].isdigit()):
            j = i
            if c == '-':
                j += 1
            while j < len(formula) and formula[j].isdigit():
                j += 1
            value = int(formula[i:j])
            tokens.append(Token(TokenType.NUMBER, value, i))
            i = j
            continue

        # Operators
        if formula[i:i+2] == '<>':
            tokens.append(Token(TokenType.NOT_EQUALS, '<>', i))
            i += 2
            continue
        if formula[i:i+2] == '<=':
            tokens.append(Token(TokenType.LE, '<=', i))
            i += 2
            continue
        if formula[i:i+2] == '>=':
            tokens.append(Token(TokenType.GE, '>=', i))
            i += 2
            continue
        if c == '<':
            tokens.append(Token(TokenType.LT, '<', i))
            i += 1
            continue
        if c == '>':
            tokens.append(Token(TokenType.GT, '>', i))
            i += 1
            continue
        if c == '=':
            tokens.append(Token(TokenType.EQUALS, '=', i))
            i += 1
            continue
        if c == '&':
            tokens.append(Token(TokenType.AMPERSAND, '&', i))
            i += 1
            continue
        if c == '(':
            tokens.append(Token(TokenType.LPAREN, '(', i))
            i += 1
            continue
        if c == ')':
            tokens.append(Token(TokenType.RPAREN, ')', i))
            i += 1
            continue
        if c == ',':
            tokens.append(Token(TokenType.COMMA, ',', i))
            i += 1
            continue

        # Function names / identifiers
        if c.isalpha() or c == '_':
            j = i
            while j < len(formula) and (formula[j].isalnum() or formula[j] == '_'):
                j += 1
            name = formula[i:j].upper()
            tokens.append(Token(TokenType.FUNC_NAME, name, i))
            i = j
            continue

        raise SyntaxError(f"Unexpected character '{c}' at position {i}")

    tokens.append(Token(TokenType.EOF, None, len(formula)))
    return tokens


# =============================================================================
# PARSER
# =============================================================================

class Parser:
    """Recursive descent parser for Excel-dialect formulas."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected: TokenType = None) -> Token:
        tok = self.current()
        if expected and tok.type != expected:
            raise SyntaxError(f"Expected {expected}, got {tok.type} at position {tok.pos}")
        self.pos += 1
        return tok

    def parse(self) -> ASTNode:
        result = self.parse_concat()
        if self.current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token {self.current()} after expression")
        return result

    def parse_concat(self) -> ASTNode:
        left = self.parse_comparison()
        parts = [left]
        while self.current().type == TokenType.AMPERSAND:
            self.consume(TokenType.AMPERSAND)
            right = self.parse_comparison()
            parts.append(right)
        if len(parts) == 1:
            return parts[0]
        return Concat(parts=parts)

    def parse_comparison(self) -> ASTNode:
        left = self.parse_primary()
        op_map = {
            TokenType.EQUALS: '=',
            TokenType.NOT_EQUALS: '<>',
            TokenType.LT: '<',
            TokenType.LE: '<=',
            TokenType.GT: '>',
            TokenType.GE: '>=',
        }
        if self.current().type in op_map:
            op = op_map[self.current().type]
            self.consume()
            right = self.parse_primary()
            return BinaryOp(op=op, left=left, right=right)
        return left

    def parse_primary(self) -> ASTNode:
        tok = self.current()

        if tok.type == TokenType.STRING:
            self.consume()
            return LiteralString(value=tok.value)

        if tok.type == TokenType.NUMBER:
            self.consume()
            return LiteralInt(value=tok.value)

        if tok.type == TokenType.FIELD_REF:
            self.consume()
            return FieldRef(name=tok.value)

        if tok.type == TokenType.FUNC_NAME:
            name = tok.value.upper()
            self.consume()

            if name == 'TRUE':
                if self.current().type == TokenType.LPAREN:
                    self.consume(TokenType.LPAREN)
                    self.consume(TokenType.RPAREN)
                return LiteralBool(value=True)

            if name == 'FALSE':
                if self.current().type == TokenType.LPAREN:
                    self.consume(TokenType.LPAREN)
                    self.consume(TokenType.RPAREN)
                return LiteralBool(value=False)

            self.consume(TokenType.LPAREN)
            args = []
            if self.current().type != TokenType.RPAREN:
                args.append(self.parse_concat())
                while self.current().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_concat())
            self.consume(TokenType.RPAREN)

            if name == 'NOT' and len(args) == 1:
                return UnaryOp(op='NOT', operand=args[0])

            return FuncCall(name=name, args=args)

        if tok.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_concat()
            self.consume(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"Unexpected token {tok.type} at position {tok.pos}")


def parse_formula(formula_text: str) -> ASTNode:
    """Parse an Excel-dialect formula into an AST."""
    tokens = tokenize(formula_text)
    parser = Parser(tokens)
    return parser.parse()


# =============================================================================
# SPARQL EXPRESSION COMPILER
# =============================================================================

def field_to_sparql_var(field_name: str) -> str:
    """Convert field name to SPARQL variable (snake_case)."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', field_name)
    return '?' + re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def field_to_property_uri(field_name: str) -> str:
    """Convert field name to property URI (camelCase)."""
    if field_name:
        return 'erb:' + field_name[0].lower() + field_name[1:]
    return 'erb:unknown'


def escape_sparql_string(s: str) -> str:
    """Escape a string for SPARQL double-quoted literals.

    Single quotes don't need escaping in double-quoted strings.
    """
    return s.replace('\\', '\\\\').replace('"', '\\"')


def compile_to_sparql(ast: ASTNode, field_bindings: Dict[str, str] = None) -> str:
    """Compile an AST node to a SPARQL expression."""
    if field_bindings is None:
        field_bindings = {}

    if isinstance(ast, LiteralBool):
        return 'true' if ast.value else 'false'

    if isinstance(ast, LiteralInt):
        return str(ast.value)

    if isinstance(ast, LiteralString):
        escaped = escape_sparql_string(ast.value)
        return f'"{escaped}"'

    if isinstance(ast, FieldRef):
        var_name = field_to_sparql_var(ast.name)
        field_bindings[ast.name] = var_name
        return var_name

    if isinstance(ast, UnaryOp):
        if ast.op == 'NOT':
            operand = compile_to_sparql(ast.operand, field_bindings)
            return f'(!({operand}))'
        raise ValueError(f"Unknown unary op: {ast.op}")

    if isinstance(ast, BinaryOp):
        left = compile_to_sparql(ast.left, field_bindings)
        right = compile_to_sparql(ast.right, field_bindings)
        op_map = {'=': '=', '<>': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
        sparql_op = op_map.get(ast.op, '=')
        return f'({left} {sparql_op} {right})'

    if isinstance(ast, FuncCall):
        if ast.name == 'AND':
            parts = [compile_to_sparql(arg, field_bindings) for arg in ast.args]
            return '(' + ' && '.join(parts) + ')'

        if ast.name == 'OR':
            parts = [compile_to_sparql(arg, field_bindings) for arg in ast.args]
            return '(' + ' || '.join(parts) + ')'

        if ast.name == 'IF':
            if len(ast.args) < 2:
                raise ValueError("IF requires at least 2 arguments")
            cond = compile_to_sparql(ast.args[0], field_bindings)
            then_val = compile_to_sparql(ast.args[1], field_bindings)
            else_val = compile_to_sparql(ast.args[2], field_bindings) if len(ast.args) > 2 else '""'
            return f'IF({cond}, {then_val}, {else_val})'

        if ast.name == 'NOT':
            if len(ast.args) != 1:
                raise ValueError("NOT requires 1 argument")
            operand = compile_to_sparql(ast.args[0], field_bindings)
            return f'(!({operand}))'

        if ast.name == 'LOWER':
            if len(ast.args) != 1:
                raise ValueError("LOWER requires 1 argument")
            arg = compile_to_sparql(ast.args[0], field_bindings)
            return f'LCASE({arg})'

        if ast.name == 'FIND':
            if len(ast.args) != 2:
                raise ValueError("FIND requires 2 arguments")
            needle = compile_to_sparql(ast.args[0], field_bindings)
            haystack = compile_to_sparql(ast.args[1], field_bindings)
            return f'CONTAINS({haystack}, {needle})'

        raise ValueError(f"Unknown function: {ast.name}")

    if isinstance(ast, Concat):
        parts = [compile_to_sparql(part, field_bindings) for part in ast.parts]
        return 'CONCAT(' + ', '.join(parts) + ')'

    raise ValueError(f"Unknown AST node type: {type(ast)}")


# =============================================================================
# RDF/TURTLE GENERATORS
# =============================================================================

def datatype_to_xsd(datatype: str) -> str:
    """Convert rulebook datatype to XSD type."""
    dt = datatype.lower()
    if dt == 'boolean':
        return 'xsd:boolean'
    elif dt == 'integer':
        return 'xsd:integer'
    else:
        return 'xsd:string'


def value_to_turtle(value: Any, datatype: str) -> str:
    """Convert a Python value to Turtle literal syntax."""
    if value is None:
        return None
    dt = datatype.lower()
    if dt == 'boolean':
        return 'true' if value else 'false'
    elif dt == 'integer':
        return str(int(value)) if value is not None else '0'
    else:
        # String - escape for Turtle
        s = str(value)
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'


def generate_schema_ttl(tables: Dict[str, Any]) -> str:
    """Generate RDFS schema from rulebook tables."""
    lines = []

    # Prefixes
    lines.append('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .')
    lines.append('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .')
    lines.append('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .')
    lines.append('@prefix erb: <http://example.org/erb#> .')
    lines.append('')
    lines.append('# RDF Schema for ERB')
    lines.append('# Generated from effortless-rulebook.json')
    lines.append('')

    # Generate classes and properties for each table
    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        if not schema:
            continue

        # Class definition
        class_uri = f'erb:{table_name}'
        lines.append(f'# === Class: {table_name} ===')
        lines.append(f'{class_uri} a rdfs:Class ;')
        lines.append(f'    rdfs:label "{table_name}" .')
        lines.append('')

        # Property definitions
        for col in schema:
            col_name = col.get('name', '')
            col_datatype = col.get('datatype', 'string')
            col_type = col.get('type', 'raw')

            prop_uri = field_to_property_uri(col_name)
            xsd_type = datatype_to_xsd(col_datatype)

            lines.append(f'{prop_uri} a rdf:Property ;')
            lines.append(f'    rdfs:domain {class_uri} ;')
            lines.append(f'    rdfs:range {xsd_type} ;')
            lines.append(f'    rdfs:label "{col_name}" .')
            lines.append('')

    return '\n'.join(lines)


def generate_data_ttl(tables: Dict[str, Any]) -> str:
    """Generate RDF data triples from rulebook tables (raw values only)."""
    lines = []

    # Prefixes
    lines.append('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .')
    lines.append('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .')
    lines.append('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .')
    lines.append('@prefix erb: <http://example.org/erb#> .')
    lines.append('')
    lines.append('# RDF Data Triples for ERB')
    lines.append('# Raw values only - calculated fields computed via SPARQL')
    lines.append('')

    # Generate individuals for each table
    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        data = table_def.get('data', [])

        if not schema or not data:
            continue

        # Build column info map
        col_info = {}
        for col in schema:
            col_name = col.get('name', '')
            col_info[col_name] = {
                'datatype': col.get('datatype', 'string'),
                'type': col.get('type', 'raw'),
                'formula': col.get('formula')
            }

        lines.append(f'# === Individuals: {table_name} ===')
        lines.append('')

        class_uri = f'erb:{table_name}'

        for i, row in enumerate(data):
            ind_uri = f'erb:{table_name}_{i}'

            lines.append(f'{ind_uri} a {class_uri} ;')

            # Add raw data properties only (not calculated)
            props = []
            for col_name, info in col_info.items():
                if info['type'] == 'calculated':
                    continue  # SPARQL will compute these

                value = row.get(col_name)
                if value is None:
                    continue

                prop_uri = field_to_property_uri(col_name)
                turtle_val = value_to_turtle(value, info['datatype'])
                if turtle_val is not None:
                    props.append(f'    {prop_uri} {turtle_val}')

            if props:
                lines.append(' ;\n'.join(props) + ' .')
            else:
                lines[-1] = lines[-1].replace(' ;', ' .')

            lines.append('')

    return '\n'.join(lines)


def generate_sparql_queries(tables: Dict[str, Any]) -> str:
    """Generate SPARQL CONSTRUCT queries from formulas."""
    queries = []

    queries.append('# SPARQL CONSTRUCT Queries for ERB')
    queries.append('# Each query computes a derived/calculated field')
    queries.append('# Queries are separated by double newlines')
    queries.append('')

    for table_name, table_def in sorted(tables.items()):
        if table_name.startswith('_') or table_name.startswith('$'):
            continue

        schema = table_def.get('schema', [])
        if not schema:
            continue

        # Collect calculated fields with formulas
        for col in schema:
            formula = col.get('formula')
            if not formula:
                continue

            col_name = col.get('name', '')

            try:
                ast = parse_formula(formula)
                field_bindings = {}
                sparql_expr = compile_to_sparql(ast, field_bindings)

                # Build WHERE clause bindings
                where_parts = [f'    ?entity a erb:{table_name} .']
                for field_name, var_name in sorted(field_bindings.items()):
                    prop_uri = field_to_property_uri(field_name)
                    where_parts.append(f'    OPTIONAL {{ ?entity {prop_uri} {var_name} . }}')

                where_clause = '\n'.join(where_parts)

                # Target property
                target_prop = field_to_property_uri(col_name)

                query = f'''# Computed field: {col_name}
# Formula: {formula.replace(chr(10), " ")}
PREFIX erb: <http://example.org/erb#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

CONSTRUCT {{
    ?entity {target_prop} ?_result .
}}
WHERE {{
{where_clause}
    BIND({sparql_expr} AS ?_result)
}}'''
                queries.append(query)

            except Exception as e:
                queries.append(f'# Computed field: {col_name}')
                queries.append(f'# Formula parse error: {e}')
                queries.append('')

    return '\n\n'.join(queries)


# =============================================================================
# MAIN
# =============================================================================

def main():
    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("RDF Execution Substrate - Formula-to-SPARQL Compiler")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Filter to just table definitions (exclude metadata keys)
    tables = {k: v for k, v in rulebook.items()
              if isinstance(v, dict) and 'schema' in v}

    print(f"Found {len(tables)} tables: {', '.join(tables.keys())}")

    # Count calculated fields
    total_calc = 0
    for table_name, table_def in tables.items():
        for col in table_def.get('schema', []):
            if col.get('formula'):
                total_calc += 1
    print(f"Found {total_calc} calculated fields to compile")

    print("\n" + "-" * 70)

    # Generate schema.ttl (RDFS schema)
    print("\nGenerating schema.ttl (RDFS schema)...")
    schema_content = generate_schema_ttl(tables)
    schema_path = script_dir / "schema.ttl"
    schema_path.write_text(schema_content, encoding='utf-8')
    print(f"   Wrote: {schema_path} ({len(schema_content)} bytes)")

    # Generate data.ttl (raw data triples)
    print("\nGenerating data.ttl (raw data triples)...")
    data_content = generate_data_ttl(tables)
    data_path = script_dir / "data.ttl"
    data_path.write_text(data_content, encoding='utf-8')
    print(f"   Wrote: {data_path} ({len(data_content)} bytes)")

    # Generate queries.sparql (SPARQL CONSTRUCT queries)
    print("\nGenerating queries.sparql (SPARQL CONSTRUCT queries)...")
    queries_content = generate_sparql_queries(tables)
    queries_path = script_dir / "queries.sparql"
    queries_path.write_text(queries_content, encoding='utf-8')
    print(f"   Wrote: {queries_path} ({len(queries_content)} bytes)")

    print("\n" + "=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
