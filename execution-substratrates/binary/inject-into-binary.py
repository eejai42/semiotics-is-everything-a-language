#!/usr/bin/env python3
"""
Binary Execution Substrate - Formula-to-Assembly Compiler

This compiler:
1. Reads the rulebook (formulas)
2. Parses each formula into an AST
3. Lowers AST → typed IR DAG
4. Generates x86-64 assembly from IR
5. Compiles asm → .dylib/.so

The formula is the source of truth. Assembly is derived, not authored.
"""

import sys
import re
import subprocess
import platform
from pathlib import Path
from dataclasses import dataclass, field
from typing import Union, List, Optional, Dict, Any
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, handle_clean_arg


# =============================================================================
# DATA TYPES
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
    size: int  # bytes


# =============================================================================
# AST NODE TYPES
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
# IR NODE TYPES (Typed, with offsets resolved)
# =============================================================================

@dataclass
class IRNode:
    result_type: DataType


@dataclass
class IRLoadBool(IRNode):
    offset: int
    field_name: str


@dataclass
class IRLoadInt(IRNode):
    offset: int
    field_name: str


@dataclass
class IRLoadString(IRNode):
    ptr_offset: int
    len_offset: int
    field_name: str


@dataclass
class IRLiteralBool(IRNode):
    value: bool


@dataclass
class IRLiteralInt(IRNode):
    value: int


@dataclass
class IRLiteralString(IRNode):
    value: str
    label: str = ""  # Label for string in data section


@dataclass
class IRNot(IRNode):
    operand: IRNode


@dataclass
class IRAnd(IRNode):
    operands: List[IRNode]


@dataclass
class IROr(IRNode):
    operands: List[IRNode]


@dataclass
class IRCompare(IRNode):
    op: str  # 'eq', 'ne', 'lt', 'le', 'gt', 'ge'
    left: IRNode
    right: IRNode


@dataclass
class IRIf(IRNode):
    condition: IRNode
    then_branch: IRNode
    else_branch: IRNode


@dataclass
class IRConcat(IRNode):
    parts: List[IRNode]


# =============================================================================
# PHASE 1: LEXER
# =============================================================================

class TokenType(Enum):
    STRING = auto()      # "text"
    NUMBER = auto()      # 123
    FIELD_REF = auto()   # {{Name}}
    FUNC_NAME = auto()   # AND, OR, NOT, IF, TRUE, FALSE
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    COMMA = auto()       # ,
    AMPERSAND = auto()   # &
    EQUALS = auto()      # =
    NOT_EQUALS = auto()  # <>
    LT = auto()          # <
    LE = auto()          # <=
    GT = auto()          # >
    GE = auto()          # >=
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int


def tokenize(formula: str) -> List[Token]:
    """Tokenize an Excel-dialect formula."""
    tokens = []
    pos = 0

    # Remove leading = if present
    if formula.startswith('='):
        formula = formula[1:]
        pos = 1

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
# PHASE 1: PARSER
# =============================================================================

class Parser:
    """Recursive descent parser for Excel-dialect formulas."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self) -> Token:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]

    def consume(self, expected: TokenType = None) -> Token:
        tok = self.current()
        if expected and tok.type != expected:
            raise SyntaxError(f"Expected {expected}, got {tok.type} at position {tok.pos}")
        self.pos += 1
        return tok

    def parse(self) -> ASTNode:
        """Parse the entire formula and return AST."""
        result = self.parse_concat()
        if self.current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token {self.current()} after expression")
        return result

    def parse_concat(self) -> ASTNode:
        """Parse string concatenation (lowest precedence)."""
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
        """Parse comparison operators."""
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
        """Parse primary expressions: literals, field refs, function calls."""
        tok = self.current()

        # String literal
        if tok.type == TokenType.STRING:
            self.consume()
            return LiteralString(value=tok.value)

        # Number literal
        if tok.type == TokenType.NUMBER:
            self.consume()
            return LiteralInt(value=tok.value)

        # Field reference
        if tok.type == TokenType.FIELD_REF:
            self.consume()
            return FieldRef(name=tok.value)

        # Function call or built-in constant
        if tok.type == TokenType.FUNC_NAME:
            name = tok.value.upper()
            self.consume()

            # TRUE() and FALSE() are boolean literals
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

            # Function call with arguments
            self.consume(TokenType.LPAREN)
            args = []

            if self.current().type != TokenType.RPAREN:
                args.append(self.parse_concat())
                while self.current().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_concat())

            self.consume(TokenType.RPAREN)

            # Special handling for NOT (unary)
            if name == 'NOT' and len(args) == 1:
                return UnaryOp(op='NOT', operand=args[0])

            return FuncCall(name=name, args=args)

        # Parenthesized expression
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
# PHASE 2: IR LOWERING
# =============================================================================

# Canonical field name mapping (from various casing to internal names)
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
    # Calculated fields (for referencing other calculations)
    'TOPFAMILYFEUDANSWER': 'top_family_feud_answer',
    'ISOPENCLOTEDWORLDCONFLICTED': 'is_open_closed_world_conflicted',
    'ISOPENCLOSEDWORLDCONFLICTED': 'is_open_closed_world_conflicted',
}


def normalize_field_name(name: str) -> str:
    """Normalize field name to internal format."""
    # Remove spaces and convert to uppercase for lookup
    upper = name.replace(' ', '').upper()
    if upper in FIELD_NAME_MAP:
        return FIELD_NAME_MAP[upper]
    # Convert CamelCase to snake_case
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return result


class IRLowerer:
    """Lower AST to typed IR with resolved field offsets."""

    def __init__(self, schema: Dict[str, FieldInfo], string_literals: Dict[str, str]):
        self.schema = schema
        self.string_literals = string_literals  # label -> value
        # Initialize counter to avoid collisions with existing entries
        self.literal_counter = len(string_literals)

    def get_string_label(self, value: str) -> str:
        """Get or create a label for a string literal."""
        for label, val in self.string_literals.items():
            if val == value:
                return label
        label = f"str_{self.literal_counter}"
        self.literal_counter += 1
        self.string_literals[label] = value
        return label

    def lower(self, ast: ASTNode) -> IRNode:
        """Lower an AST node to IR."""

        if isinstance(ast, LiteralBool):
            return IRLiteralBool(result_type=DataType.BOOL, value=ast.value)

        if isinstance(ast, LiteralInt):
            return IRLiteralInt(result_type=DataType.INT, value=ast.value)

        if isinstance(ast, LiteralString):
            label = self.get_string_label(ast.value)
            return IRLiteralString(result_type=DataType.STRING, value=ast.value, label=label)

        if isinstance(ast, FieldRef):
            field_name = normalize_field_name(ast.name)
            if field_name not in self.schema:
                raise ValueError(f"Unknown field: {ast.name} (normalized: {field_name})")
            info = self.schema[field_name]

            if info.datatype == DataType.BOOL:
                return IRLoadBool(result_type=DataType.BOOL, offset=info.offset, field_name=field_name)
            elif info.datatype == DataType.INT:
                return IRLoadInt(result_type=DataType.INT, offset=info.offset, field_name=field_name)
            elif info.datatype == DataType.STRING:
                return IRLoadString(
                    result_type=DataType.STRING,
                    ptr_offset=info.offset,
                    len_offset=info.offset + 8,
                    field_name=field_name
                )
            else:
                raise ValueError(f"Unknown field type: {info.datatype}")

        if isinstance(ast, UnaryOp):
            if ast.op == 'NOT':
                operand = self.lower(ast.operand)
                return IRNot(result_type=DataType.BOOL, operand=operand)
            raise ValueError(f"Unknown unary op: {ast.op}")

        if isinstance(ast, BinaryOp):
            left = self.lower(ast.left)
            right = self.lower(ast.right)
            op_map = {'=': 'eq', '<>': 'ne', '<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge'}
            return IRCompare(result_type=DataType.BOOL, op=op_map[ast.op], left=left, right=right)

        if isinstance(ast, FuncCall):
            if ast.name == 'AND':
                operands = [self.lower(arg) for arg in ast.args]
                return IRAnd(result_type=DataType.BOOL, operands=operands)

            if ast.name == 'OR':
                operands = [self.lower(arg) for arg in ast.args]
                return IROr(result_type=DataType.BOOL, operands=operands)

            if ast.name == 'IF':
                if len(ast.args) < 2 or len(ast.args) > 3:
                    raise ValueError(f"IF requires 2 or 3 arguments, got {len(ast.args)}")
                cond = self.lower(ast.args[0])
                then_br = self.lower(ast.args[1])
                # If no else clause, default to empty string (for string results) or false (for bool)
                if len(ast.args) == 3:
                    else_br = self.lower(ast.args[2])
                else:
                    # Default else branch based on then branch type
                    if then_br.result_type == DataType.STRING:
                        else_br = IRLiteralString(result_type=DataType.STRING, value="", label=self.get_string_label(""))
                    elif then_br.result_type == DataType.BOOL:
                        else_br = IRLiteralBool(result_type=DataType.BOOL, value=False)
                    else:
                        else_br = IRLiteralInt(result_type=DataType.INT, value=0)
                # Result type is the type of the branches (they should match)
                result_type = then_br.result_type
                return IRIf(result_type=result_type, condition=cond, then_branch=then_br, else_branch=else_br)

            if ast.name == 'NOT':
                if len(ast.args) != 1:
                    raise ValueError(f"NOT requires 1 argument, got {len(ast.args)}")
                operand = self.lower(ast.args[0])
                return IRNot(result_type=DataType.BOOL, operand=operand)

            raise ValueError(f"Unknown function: {ast.name}")

        if isinstance(ast, Concat):
            parts = [self.lower(part) for part in ast.parts]
            return IRConcat(result_type=DataType.STRING, parts=parts)

        raise ValueError(f"Unknown AST node type: {type(ast)}")


def build_schema(columns: List[dict]) -> Dict[str, FieldInfo]:
    """Build schema with field offsets from column definitions."""
    schema = {}
    offset = 0

    # First pass: collect all fields
    for col in columns:
        name = col.get('name', '')
        # Normalize to snake_case
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

        # Align offset
        if dt == DataType.INT or dt == DataType.STRING:
            offset = (offset + 7) & ~7  # 8-byte align

        schema[field_name] = FieldInfo(
            name=field_name,
            datatype=dt,
            offset=offset,
            size=size
        )
        offset += size

    return schema


def lower_to_ir(ast: ASTNode, schema: Dict[str, FieldInfo], string_literals: Dict[str, str]) -> IRNode:
    """Lower AST to typed IR DAG."""
    lowerer = IRLowerer(schema, string_literals)
    return lowerer.lower(ast)


# =============================================================================
# PHASE 3: ASSEMBLY CODE GENERATION (ARM64 / Apple Silicon)
# =============================================================================

class AsmGenerator:
    """Generate ARM64 assembly from IR."""

    # Class-level counter for globally unique labels
    _global_label_counter = 0
    # Track which functions need static result buffers (use set to avoid duplicates)
    _result_buffers = set()

    def __init__(self, string_literals: Dict[str, str]):
        self.string_literals = string_literals
        self.func_name = ""
        self.temp_string_counter = 0
        self.needs_result_buffer = False

    def new_label(self, prefix: str = "L") -> str:
        AsmGenerator._global_label_counter += 1
        return f"{prefix}_{AsmGenerator._global_label_counter}"

    def generate_function(self, ir: IRNode, func_name: str) -> str:
        """Generate a complete ARM64 function for an IR tree."""
        self.func_name = func_name
        self.needs_result_buffer = False
        lines = []

        # Function header
        lines.append(f"    .globl _{func_name}")
        lines.append(f"    .p2align 2")
        lines.append(f"_{func_name}:")

        # Prologue - save frame pointer and link register, plus callee-saved regs
        lines.append("    stp x29, x30, [sp, #-16]!")   # Save fp, lr
        lines.append("    mov x29, sp")                  # Set up frame pointer
        lines.append("    stp x19, x20, [sp, #-16]!")   # Save callee-saved
        lines.append("    stp x21, x22, [sp, #-16]!")
        lines.append("    stp x23, x24, [sp, #-16]!")
        lines.append("    sub sp, sp, #256")            # Stack space for temps

        # Save struct pointer in x19 (callee-saved)
        lines.append("    mov x19, x0")  # x19 = TestAnswer* ptr

        # Generate code for the IR tree
        result_reg, code = self.gen_ir(ir)
        lines.extend(code)

        # Move result to x0/w0 if not already there
        if result_reg != "x0" and result_reg != "w0":
            if ir.result_type == DataType.BOOL:
                if result_reg.startswith("w"):
                    lines.append(f"    mov w0, {result_reg}")
                else:
                    lines.append(f"    and w0, {result_reg}, #0xff")
            else:
                lines.append(f"    mov x0, {result_reg}")

        # Epilogue
        lines.append("    add sp, sp, #256")
        lines.append("    ldp x23, x24, [sp], #16")
        lines.append("    ldp x21, x22, [sp], #16")
        lines.append("    ldp x19, x20, [sp], #16")
        lines.append("    ldp x29, x30, [sp], #16")
        lines.append("    ret")
        lines.append("")

        return "\n".join(lines)

    def gen_ir(self, ir: IRNode, dest_reg: str = "x0") -> tuple:
        """Generate ARM64 assembly for an IR node. Returns (result_reg, [lines])."""
        lines = []

        if isinstance(ir, IRLiteralBool):
            val = 1 if ir.value else 0
            lines.append(f"    mov w0, #{val}")
            return ("w0", lines)

        if isinstance(ir, IRLiteralInt):
            if ir.value >= 0 and ir.value < 65536:
                lines.append(f"    mov x0, #{ir.value}")
            else:
                # Load large constant
                lines.append(f"    mov x0, #{ir.value & 0xffff}")
                if ir.value > 0xffff:
                    lines.append(f"    movk x0, #{(ir.value >> 16) & 0xffff}, lsl #16")
                if ir.value > 0xffffffff:
                    lines.append(f"    movk x0, #{(ir.value >> 32) & 0xffff}, lsl #32")
                    lines.append(f"    movk x0, #{(ir.value >> 48) & 0xffff}, lsl #48")
            return ("x0", lines)

        if isinstance(ir, IRLiteralString):
            # Return pointer to string literal in x0, length in x1
            lines.append(f"    adrp x0, {ir.label}@PAGE")
            lines.append(f"    add x0, x0, {ir.label}@PAGEOFF")
            lines.append(f"    mov x1, #{len(ir.value)}")
            return ("x0", lines)

        if isinstance(ir, IRLoadBool):
            lines.append(f"    ldrb w0, [x19, #{ir.offset}]")
            return ("w0", lines)

        if isinstance(ir, IRLoadInt):
            lines.append(f"    ldr x0, [x19, #{ir.offset}]")
            return ("x0", lines)

        if isinstance(ir, IRLoadString):
            lines.append(f"    ldr x0, [x19, #{ir.ptr_offset}]")
            lines.append(f"    ldr x1, [x19, #{ir.len_offset}]")
            return ("x0", lines)

        if isinstance(ir, IRNot):
            _, op_code = self.gen_ir(ir.operand)
            lines.extend(op_code)
            lines.append("    eor w0, w0, #1")  # Flip the boolean
            return ("w0", lines)

        if isinstance(ir, IRAnd):
            false_label = self.new_label("and_false")
            end_label = self.new_label("and_end")

            for operand in ir.operands:
                _, op_code = self.gen_ir(operand)
                lines.extend(op_code)
                # Check if result is false (short-circuit)
                lines.append("    cbz w0, " + false_label)

            # All true
            lines.append("    mov w0, #1")
            lines.append(f"    b {end_label}")

            # Short-circuit false
            lines.append(f"{false_label}:")
            lines.append("    mov w0, #0")

            lines.append(f"{end_label}:")
            return ("w0", lines)

        if isinstance(ir, IROr):
            true_label = self.new_label("or_true")
            end_label = self.new_label("or_end")

            for operand in ir.operands:
                _, op_code = self.gen_ir(operand)
                lines.extend(op_code)
                # Check if result is true (short-circuit)
                lines.append("    cbnz w0, " + true_label)

            # All false
            lines.append("    mov w0, #0")
            lines.append(f"    b {end_label}")

            # Short-circuit true
            lines.append(f"{true_label}:")
            lines.append("    mov w0, #1")

            lines.append(f"{end_label}:")
            return ("w0", lines)

        if isinstance(ir, IRCompare):
            # Evaluate left operand
            _, left_code = self.gen_ir(ir.left)
            lines.extend(left_code)

            # Save left result in callee-saved registers
            if ir.left.result_type == DataType.BOOL:
                lines.append("    mov w20, w0")
            elif ir.left.result_type == DataType.STRING:
                lines.append("    mov x20, x0")  # ptr
                lines.append("    mov x21, x1")  # len
            else:
                lines.append("    mov x20, x0")

            # Evaluate right operand
            _, right_code = self.gen_ir(ir.right)
            lines.extend(right_code)

            if ir.left.result_type == DataType.STRING or ir.right.result_type == DataType.STRING:
                # String comparison - call runtime
                # Args: x0=ptr1, x1=len1, x2=ptr2, x3=len2
                lines.append("    mov x2, x0")    # right ptr
                lines.append("    mov x3, x1")    # right len
                lines.append("    mov x0, x20")   # left ptr
                lines.append("    mov x1, x21")   # left len
                lines.append("    bl _string_equals")

                if ir.op == 'ne':
                    lines.append("    eor w0, w0, #1")
            else:
                # Integer or bool comparison
                if ir.left.result_type == DataType.BOOL:
                    lines.append("    cmp w20, w0")
                else:
                    lines.append("    cmp x20, x0")

                # Set result based on comparison
                if ir.op == 'eq':
                    lines.append("    cset w0, eq")
                elif ir.op == 'ne':
                    lines.append("    cset w0, ne")
                elif ir.op == 'lt':
                    lines.append("    cset w0, lt")
                elif ir.op == 'le':
                    lines.append("    cset w0, le")
                elif ir.op == 'gt':
                    lines.append("    cset w0, gt")
                elif ir.op == 'ge':
                    lines.append("    cset w0, ge")

            return ("w0", lines)

        if isinstance(ir, IRIf):
            else_label = self.new_label("if_else")
            end_label = self.new_label("if_end")

            # Evaluate condition
            _, cond_code = self.gen_ir(ir.condition)
            lines.extend(cond_code)
            lines.append(f"    cbz w0, {else_label}")

            # Then branch
            _, then_code = self.gen_ir(ir.then_branch)
            lines.extend(then_code)
            if ir.result_type == DataType.STRING:
                lines.append("    mov x20, x0")  # Save string ptr
                lines.append("    mov x21, x1")  # Save string len
            else:
                lines.append("    mov x20, x0")
            lines.append(f"    b {end_label}")

            # Else branch
            lines.append(f"{else_label}:")
            _, else_code = self.gen_ir(ir.else_branch)
            lines.extend(else_code)
            if ir.result_type == DataType.STRING:
                lines.append("    mov x20, x0")
                lines.append("    mov x21, x1")
            else:
                lines.append("    mov x20, x0")

            # End - move result to x0
            lines.append(f"{end_label}:")
            if ir.result_type == DataType.STRING:
                lines.append("    mov x0, x20")
                lines.append("    mov x1, x21")
            elif ir.result_type == DataType.BOOL:
                lines.append("    mov w0, w20")
            else:
                lines.append("    mov x0, x20")

            return ("x0" if ir.result_type != DataType.BOOL else "w0", lines)

        if isinstance(ir, IRConcat):
            # String concatenation - build result in a static buffer
            # Mark that this function needs a result buffer
            self.needs_result_buffer = True
            buffer_label = f"_result_buf_{self.func_name}"
            AsmGenerator._result_buffers.add(self.func_name)

            part_data = []  # List of (ptr_stack_offset, len_stack_offset)

            for i, part in enumerate(ir.parts):
                _, part_code = self.gen_ir(part)
                lines.extend(part_code)

                # For non-string parts, convert to string
                if part.result_type == DataType.BOOL:
                    # Convert bool to "true" or "false"
                    true_label = self.new_label("bool_true")
                    end_label = self.new_label("bool_end")
                    lines.append(f"    cbnz w0, {true_label}")
                    lines.append("    adrp x0, _str_false@PAGE")
                    lines.append("    add x0, x0, _str_false@PAGEOFF")
                    lines.append("    mov x1, #5")  # len("false")
                    lines.append(f"    b {end_label}")
                    lines.append(f"{true_label}:")
                    lines.append("    adrp x0, _str_true@PAGE")
                    lines.append("    add x0, x0, _str_true@PAGEOFF")
                    lines.append("    mov x1, #4")  # len("true")
                    lines.append(f"{end_label}:")
                elif part.result_type == DataType.INT:
                    # Convert int to string - call helper
                    lines.append("    mov x1, x0")  # value
                    lines.append("    sub x0, x29, #200")  # buffer for int->string
                    lines.append("    bl _int_to_string")
                    # x0 = ptr, x1 = len

                # Save ptr and len on stack
                save_offset = 16 + (i * 16)  # Offset from sp
                lines.append(f"    str x0, [sp, #{save_offset}]")      # ptr
                lines.append(f"    str x1, [sp, #{save_offset + 8}]")  # len
                part_data.append((save_offset, save_offset + 8))

            # Now concatenate all parts using a STATIC buffer
            # Start with first part
            lines.append(f"    ldr x0, [sp, #{part_data[0][0]}]")
            lines.append(f"    ldr x1, [sp, #{part_data[0][1]}]")

            # Load static buffer address into x22
            lines.append(f"    adrp x22, {buffer_label}@PAGE")
            lines.append(f"    add x22, x22, {buffer_label}@PAGEOFF")

            for i in range(1, len(part_data)):
                # Concat current result with next part
                # _string_concat convention: x0=dest, x1=s1_ptr, x2=s1_len, x3=s2_ptr, x4=s2_len
                # Before: x0=current_ptr, x1=current_len
                lines.append(f"    ldr x4, [sp, #{part_data[i][1]}]")   # x4 = s2_len (load first)
                lines.append(f"    ldr x3, [sp, #{part_data[i][0]}]")   # x3 = s2_ptr
                lines.append("    mov x2, x1")    # x2 = s1_len (from current)
                lines.append("    mov x1, x0")    # x1 = s1_ptr (from current)
                lines.append("    mov x0, x22")   # x0 = dest buffer
                lines.append("    bl _string_concat")
                # Result in x0 (ptr to buffer), x1 (total len)

            return ("x0", lines)

        raise ValueError(f"Unknown IR node type: {type(ir)}")


def generate_assembly(ir: IRNode, field_name: str, string_literals: Dict[str, str]) -> str:
    """Generate x86-64 assembly from IR DAG."""
    gen = AsmGenerator(string_literals)
    return gen.generate_function(ir, f"eval_{field_name}")


def generate_string_runtime() -> str:
    """Generate the ARM64 string runtime library in assembly."""
    return """
; String runtime for ERB Binary Substrate (ARM64 / Apple Silicon)
; Calling convention: Apple ARM64 ABI

    .text
    .p2align 2

; bool _string_equals(const char* s1, size_t len1, const char* s2, size_t len2)
; x0 = s1, x1 = len1, x2 = s2, x3 = len2
; Returns 1 if strings are equal, 0 otherwise in w0
    .globl _string_equals
_string_equals:
    cmp x1, x3                  ; Compare lengths first
    b.ne Lstr_eq_false
    cbz x1, Lstr_eq_true        ; If both empty, equal

    ; Compare byte by byte
    mov x4, #0                  ; index
Lstr_eq_loop:
    ldrb w5, [x0, x4]
    ldrb w6, [x2, x4]
    cmp w5, w6
    b.ne Lstr_eq_false
    add x4, x4, #1
    cmp x4, x1
    b.lt Lstr_eq_loop

Lstr_eq_true:
    mov w0, #1
    ret

Lstr_eq_false:
    mov w0, #0
    ret

; char* _string_concat(char* dest, const char* s1, size_t len1, const char* s2, size_t len2)
; x0 = dest, x1 = s1_ptr, x2 = s1_len, x3 = s2_ptr, x4 = s2_len
; Returns dest in x0, total length in x1
    .globl _string_concat
_string_concat:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    stp x19, x20, [sp, #-16]!
    stp x21, x22, [sp, #-16]!

    mov x19, x0                 ; save dest
    mov x20, x2                 ; save s1_len
    mov x21, x4                 ; save s2_len

    ; Copy s1 to dest
    mov x5, #0                  ; index
    cbz x2, Lconcat_s2          ; skip if s1 empty
Lconcat_s1_loop:
    ldrb w6, [x1, x5]
    strb w6, [x0, x5]
    add x5, x5, #1
    cmp x5, x2
    b.lt Lconcat_s1_loop

Lconcat_s2:
    ; Copy s2 after s1
    add x0, x19, x20            ; dest + s1_len
    mov x5, #0                  ; index
    cbz x21, Lconcat_done       ; skip if s2 empty
Lconcat_s2_loop:
    ldrb w6, [x3, x5]
    strb w6, [x0, x5]
    add x5, x5, #1
    cmp x5, x21
    b.lt Lconcat_s2_loop

Lconcat_done:
    mov x0, x19                 ; return dest ptr
    add x1, x20, x21            ; return total length

    ldp x21, x22, [sp], #16
    ldp x19, x20, [sp], #16
    ldp x29, x30, [sp], #16
    ret

; int_to_string: convert integer to string
; x0 = buffer, x1 = integer value
; Returns: x0 = buffer ptr, x1 = string length
    .globl _int_to_string
_int_to_string:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    stp x19, x20, [sp, #-16]!
    stp x21, x22, [sp, #-16]!

    mov x19, x0                 ; save buffer start
    mov x20, x0                 ; current position
    mov x2, x1                  ; value to convert

    ; Handle negative
    cmp x2, #0
    b.ge Lits_positive
    neg x2, x2
    mov w3, #'-'
    strb w3, [x20], #1

Lits_positive:
    mov x21, x20                ; start of digits

    ; Generate digits in reverse
    mov x3, #10
Lits_loop:
    udiv x4, x2, x3             ; quotient
    msub x5, x4, x3, x2         ; remainder = x2 - (x4 * 10)
    add w5, w5, #'0'
    strb w5, [x20], #1
    mov x2, x4
    cbnz x2, Lits_loop

    ; Calculate length
    sub x22, x20, x19           ; length

    ; Reverse digits (x21 = start, x20-1 = end)
    sub x20, x20, #1            ; point to last digit
Lits_reverse:
    cmp x21, x20
    b.ge Lits_done
    ldrb w3, [x21]
    ldrb w4, [x20]
    strb w4, [x21], #1
    strb w3, [x20]
    sub x20, x20, #1
    b Lits_reverse

Lits_done:
    mov x0, x19                 ; return buffer ptr
    mov x1, x22                 ; return length

    ldp x21, x22, [sp], #16
    ldp x19, x20, [sp], #16
    ldp x29, x30, [sp], #16
    ret

    .data
    .globl _str_true
_str_true:
    .asciz "true"
    .globl _str_false
_str_false:
    .asciz "false"

"""


def generate_data_section(string_literals: Dict[str, str], result_buffers: List[str]) -> str:
    """Generate the data section with string literals and result buffers (ARM64)."""
    lines = ["    .data"]
    for label, value in string_literals.items():
        # Escape the string for assembly (single quotes don't need escaping)
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'    .globl {label}')
        lines.append(f'{label}:')
        lines.append(f'    .asciz "{escaped}"')
        lines.append(f'    .globl {label}_len')
        lines.append(f'{label}_len:')
        lines.append(f'    .quad {len(value)}')

    # Add static result buffers for functions that do string concatenation
    lines.append("")
    lines.append("    ; Static result buffers for string concatenation")
    lines.append("    .bss")
    for func_name in result_buffers:
        buffer_label = f"_result_buf_{func_name}"
        lines.append(f"    .globl {buffer_label}")
        lines.append(f"    .p2align 3")
        lines.append(f"{buffer_label}:")
        lines.append(f"    .space 1024")  # 1KB buffer per function

    return "\n".join(lines)


# =============================================================================
# PHASE 4: BUILD PIPELINE
# =============================================================================

def assemble_and_link(asm_source: str, output_path: Path) -> Path:
    """Assemble and link the generated assembly to a shared library."""

    asm_file = output_path / "erb_calc.s"
    obj_file = output_path / "erb_calc.o"

    system = platform.system()
    if system == "Darwin":
        lib_file = output_path / "erb_calc.dylib"
    else:
        lib_file = output_path / "erb_calc.so"

    # Write assembly source
    asm_file.write_text(asm_source)
    print(f"   Wrote: {asm_file}")

    # Assemble
    if system == "Darwin":
        # macOS: use clang to assemble (handles .s files with Intel syntax)
        cmd = ["clang", "-c", "-o", str(obj_file), str(asm_file)]
    else:
        # Linux: use as or clang
        cmd = ["as", "-o", str(obj_file), str(asm_file)]

    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   Assembly failed: {result.stderr}")
        raise RuntimeError(f"Assembly failed: {result.stderr}")
    print(f"   Created: {obj_file}")

    # Link
    if system == "Darwin":
        cmd = ["clang", "-shared", "-o", str(lib_file), str(obj_file)]
    else:
        cmd = ["ld", "-shared", "-o", str(lib_file), str(obj_file)]

    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   Linking failed: {result.stderr}")
        raise RuntimeError(f"Linking failed: {result.stderr}")
    print(f"   Created: {lib_file}")

    return lib_file


# =============================================================================
# MAIN: ORCHESTRATE THE COMPILER PIPELINE
# =============================================================================

def main():
    # Define generated files for this substrate
    GENERATED_FILES = [
        'erb_calc.s',
        'erb_calc.o',
        'erb_calc.dylib',
        'erb_calc.so',
        'test-answers.json',
        'test-results.md',
    ]

    # Handle --clean argument
    if handle_clean_arg(GENERATED_FILES, "Binary substrate: Removes generated assembly and compiled library"):
        return

    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("Binary Execution Substrate - Formula-to-Assembly Compiler")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Extract schema and formulas
    language_candidates = rulebook.get("LanguageCandidates", {})
    columns = language_candidates.get("schema", [])  # Note: it's "schema" not "columns"

    # Build schema with field offsets
    print("\n📐 Building schema...")
    schema = build_schema(columns)
    for field_name, info in schema.items():
        print(f"   {field_name}: offset={info.offset}, type={info.datatype.name}, size={info.size}")

    # Find calculated fields (those with formulas)
    calculated_fields = []
    for col in columns:
        formula = col.get("formula") or col.get("calculation")
        if formula:
            field_name = normalize_field_name(col.get("name", ""))
            calculated_fields.append({
                "name": field_name,
                "formula": formula,
                "type": col.get("datatype", "string")
            })

    print(f"\n📋 Found {len(calculated_fields)} calculated fields to compile:")
    for cf in calculated_fields:
        formula_preview = cf['formula'][:60] + '...' if len(cf['formula']) > 60 else cf['formula']
        print(f"   • {cf['name']}: {formula_preview}")

    print("\n" + "-" * 70)
    print("\n🔧 Compiling formulas to assembly...\n")

    # Shared string literals across all functions
    string_literals = {}

    # Clear the result buffers set from any previous runs
    AsmGenerator._result_buffers = set()

    # Compile each formula
    all_functions = []

    for cf in calculated_fields:
        print(f"\n>>> Compiling: {cf['name']}")
        print(f"    Formula: {cf['formula']}")

        # Phase 1: Parse
        print("    Phase 1: Parsing...")
        try:
            ast = parse_formula(cf['formula'])
            print(f"    AST: {type(ast).__name__}")
        except Exception as e:
            print(f"    ❌ Parse error: {e}")
            sys.exit(1)

        # Phase 2: Lower to IR
        print("    Phase 2: Lowering to IR...")
        try:
            ir = lower_to_ir(ast, schema, string_literals)
            print(f"    IR: {type(ir).__name__}, result_type={ir.result_type.name}")
        except Exception as e:
            print(f"    ❌ Lowering error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # Phase 3: Generate assembly
        print("    Phase 3: Generating assembly...")
        try:
            asm = generate_assembly(ir, cf['name'], string_literals)
            all_functions.append(asm)
            print(f"    Generated {len(asm.splitlines())} lines of assembly")
        except Exception as e:
            print(f"    ❌ Codegen error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        print("    ✅ Done")

    # Phase 4: Combine and build
    print("\n" + "-" * 70)
    print("\n🔨 Building shared library...")

    # Generate string runtime
    runtime = generate_string_runtime()

    # Generate data section for string literals and result buffers
    data_section = generate_data_section(string_literals, AsmGenerator._result_buffers)

    # Combine all assembly
    full_asm = f"""
; ERB Binary Substrate - Generated Assembly (ARM64 / Apple Silicon)
; Generated from rulebook formulas - DO NOT HAND-EDIT
;
; This file is GENERATED by inject-into-binary.py
; The formulas are the source of truth, not this assembly.

{runtime}

{data_section}

    .text

{chr(10).join(all_functions)}
"""

    try:
        lib_path = assemble_and_link(full_asm, script_dir)
        print(f"\n✅ Successfully compiled: {lib_path}")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        # Still write the asm file for debugging
        asm_file = script_dir / "erb_calc.s"
        asm_file.write_text(full_asm)
        print(f"   Assembly source written to: {asm_file}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Compilation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
