"""Tests for the sub-agent orchestrator: routing, dispatch, aggregation."""

import pytest

from subagents.orchestrator import (
    Orchestrator,
    Result,
    Task,
    demo,
    infer_kind,
)


def test_routes_search_task():
    orch = Orchestrator()
    result = orch.delegate(Task(kind="search", payload="mcp"))
    assert result.handled_by == "search_agent"
    assert result.ok


def test_routes_summarise_task():
    orch = Orchestrator()
    result = orch.delegate(
        Task(kind="summarise", payload="One. Two. Three. Four. Five sentences here.")
    )
    assert result.handled_by == "summarise_agent"
    assert isinstance(result.output, str)


def test_routes_calculate_task():
    orch = Orchestrator()
    result = orch.delegate(Task(kind="calculate", payload="6 * 7"))
    assert result.handled_by == "calculate_agent"
    assert result.output == 42.0
    assert result.ok


def test_calculate_error_is_captured_not_raised():
    orch = Orchestrator()
    result = orch.delegate(Task(kind="calculate", payload="1 / 0"))
    assert result.ok is False
    assert result.error
    assert result.output is None


def test_unknown_kind_raises():
    orch = Orchestrator()
    with pytest.raises(ValueError):
        orch.delegate(Task(kind="nope", payload="x"))


def test_run_returns_one_result_per_task():
    orch = Orchestrator()
    results = orch.run(
        [
            Task(kind="search", payload="skills"),
            Task(kind="calculate", payload="2 + 2"),
        ]
    )
    assert len(results) == 2
    assert all(isinstance(r, Result) for r in results)


@pytest.mark.parametrize(
    "request_text,expected_kind",
    [
        ("2 + 2 * 10", "calculate"),
        ("sqrt(16)", "calculate"),
        ("summarise this passage for me", "summarise"),
        ("give me the tldr", "summarise"),
        ("find the docs about MCP", "search"),
        ("what is a forward deployed engineer", "search"),
    ],
)
def test_infer_kind(request_text, expected_kind):
    assert infer_kind(request_text) == expected_kind


def test_infer_kind_empty_raises():
    with pytest.raises(ValueError):
        infer_kind("   ")


def test_handle_infers_and_dispatches_calculation():
    orch = Orchestrator()
    result = orch.handle("100 / 4")
    assert result.handled_by == "calculate_agent"
    assert result.output == 25.0


def test_handle_separate_payload():
    orch = Orchestrator()
    result = orch.handle("summarise this", payload="A. B. C. D. E sentences total.")
    assert result.handled_by == "summarise_agent"


def test_custom_registry_is_used():
    sentinel = Result(kind="search", output="custom", handled_by="custom_agent")
    orch = Orchestrator(registry={"search": lambda task: sentinel})
    assert orch.delegate(Task(kind="search", payload="x")) is sentinel


def test_demo_runs_end_to_end():
    results = demo()
    assert len(results) == 3
    kinds = {r.handled_by for r in results}
    assert kinds == {"search_agent", "summarise_agent", "calculate_agent"}
    assert all(r.ok for r in results)
