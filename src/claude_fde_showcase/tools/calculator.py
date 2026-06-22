"""A safe arithmetic calculator.

Evaluates arithmetic expressions by parsing them into a Python AST and walking
only an explicit allowlist of node types. It never calls ``eval`` on the raw
string, so it cannot execute arbitrary code, access names, or call functions --
the classic injection trap when "just letting the model do maths".

Supported: + - * / // % ** , unary +/- , parentheses, and a handful of common
math functions (sqrt, abs, round, floor, ceil, log, sin, cos) plus the
constants pi and e.

This is the kind of small, hardened tool an FDE writes so the model offloads
exact computation to deterministic code instead of hallucinating digits.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Callable

__all__ = ["calculate", "CalculatorError"]


class CalculatorError(ValueError):
    """Raised for any invalid or disallowed expression."""


_BIN_OPS: dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type, Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCTIONS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "min": min,
    "max": max,
}

_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

# Guard against absurd exponents that would hang or exhaust memory.
_MAX_POW_EXPONENT = 1000


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError(f"Unsupported constant: {node.value!r}")
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        fn = _BIN_OPS.get(op_type)
        if fn is None:
            raise CalculatorError(f"Unsupported operator: {op_type.__name__}")
        left, right = _eval(node.left), _eval(node.right)
        if op_type is ast.Pow and abs(right) > _MAX_POW_EXPONENT:
            raise CalculatorError("Exponent too large")
        try:
            return fn(left, right)
        except ZeroDivisionError as exc:
            raise CalculatorError("Division by zero") from exc

    if isinstance(node, ast.UnaryOp):
        fn = _UNARY_OPS.get(type(node.op))
        if fn is None:
            raise CalculatorError(f"Unsupported unary operator: {type(node.op).__name__}")
        return fn(_eval(node.operand))

    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise CalculatorError(f"Unknown name: {node.id!r}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise CalculatorError("Unsupported function call")
        if node.keywords:
            raise CalculatorError("Keyword arguments are not supported")
        args = [_eval(arg) for arg in node.args]
        return _FUNCTIONS[node.func.id](*args)

    raise CalculatorError(f"Unsupported expression element: {type(node).__name__}")


def calculate(expression: str) -> float:
    """Safely evaluate an arithmetic ``expression`` and return the result.

    Raises :class:`CalculatorError` for empty input, syntax errors, disallowed
    constructs (names, attribute access, arbitrary calls), or runtime maths
    errors such as division by zero.
    """
    if not expression or not expression.strip():
        raise CalculatorError("Empty expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"Invalid syntax: {exc.msg}") from exc
    result = _eval(tree)
    return float(result)
