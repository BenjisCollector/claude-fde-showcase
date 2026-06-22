"""Tests for the safe arithmetic calculator, including security guards."""

import math

import pytest

from claude_fde_showcase.tools.calculator import CalculatorError, calculate


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("2 + 2", 4.0),
        ("2 + 2 * 10", 22.0),
        ("(2 + 2) * 10", 40.0),
        ("10 / 4", 2.5),
        ("10 // 3", 3.0),
        ("10 % 3", 1.0),
        ("2 ** 8", 256.0),
        ("-5 + 3", -2.0),
        ("+7", 7.0),
    ],
)
def test_basic_arithmetic(expr, expected):
    assert calculate(expr) == expected


def test_functions_and_constants():
    assert calculate("sqrt(144)") == 12.0
    assert calculate("max(1, 2, 3)") == 3.0
    assert calculate("abs(-9)") == 9.0
    assert calculate("pi") == pytest.approx(math.pi)
    assert calculate("log(e)") == pytest.approx(1.0)


def test_nested_expression():
    assert calculate("sqrt(144) + 2 ** 5") == pytest.approx(44.0)


def test_division_by_zero_raises_calculator_error():
    with pytest.raises(CalculatorError):
        calculate("1 / 0")


def test_empty_expression_raises():
    with pytest.raises(CalculatorError):
        calculate("")
    with pytest.raises(CalculatorError):
        calculate("   ")


def test_syntax_error_raises():
    with pytest.raises(CalculatorError):
        calculate("2 +")


def test_unknown_name_rejected():
    with pytest.raises(CalculatorError):
        calculate("foo + 1")


def test_arbitrary_function_call_rejected():
    # The classic injection: must NOT execute.
    with pytest.raises(CalculatorError):
        calculate("__import__('os').system('echo pwned')")


def test_attribute_access_rejected():
    with pytest.raises(CalculatorError):
        calculate("(1).__class__")


def test_huge_exponent_rejected():
    with pytest.raises(CalculatorError):
        calculate("2 ** 100000")


def test_result_is_float():
    assert isinstance(calculate("3 + 4"), float)
