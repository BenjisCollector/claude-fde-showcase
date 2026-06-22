"""A runnable orchestrator that routes tasks to specialised sub-agents.

The orchestrator owns three responsibilities an FDE cares about in production:

1. **Routing** -- map an incoming task to the sub-agent that handles its kind,
   either explicitly (the caller names the kind) or by inference
   (:func:`infer_kind` classifies a free-text request).
2. **Dispatch & isolation** -- run the chosen sub-agent, capturing success or a
   structured error so one failing task never aborts a whole plan.
3. **Aggregation** -- collect per-task results into a single report.

No model is called: each sub-agent wraps a deterministic tool from
:mod:`claude_fde_showcase.tools`. The point is the *shape* of agentic
delegation -- swap a stub worker for a Claude-backed one and nothing else
changes. It runs end to end with ``python -m subagents.orchestrator``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from claude_fde_showcase.tools.calculator import CalculatorError, calculate
from claude_fde_showcase.tools.search import search_docs
from claude_fde_showcase.tools.summarise import summarise_extractive


@dataclass
class Task:
    """A unit of work routed to a sub-agent.

    ``kind`` is one of ``"search"``, ``"summarise"``, or ``"calculate"``.
    ``payload`` is the input for that kind (a query, a passage, or an
    expression).
    """

    kind: str
    payload: str


@dataclass
class Result:
    """The outcome of running a task through a sub-agent."""

    kind: str
    output: object
    handled_by: str
    ok: bool = True
    error: str | None = None


# -- sub-agents ---------------------------------------------------------------
def search_agent(task: Task) -> Result:
    """Sub-agent specialised in document retrieval."""
    return Result(kind=task.kind, output=search_docs(task.payload), handled_by="search_agent")


def summarise_agent(task: Task) -> Result:
    """Sub-agent specialised in extractive summarisation."""
    return Result(
        kind=task.kind,
        output=summarise_extractive(task.payload),
        handled_by="summarise_agent",
    )


def calculate_agent(task: Task) -> Result:
    """Sub-agent specialised in exact arithmetic.

    Wraps the calculator's domain error in a structured failed ``Result`` so a
    bad expression does not raise out of the orchestrator.
    """
    try:
        value = calculate(task.payload)
    except CalculatorError as exc:
        return Result(
            kind=task.kind,
            output=None,
            handled_by="calculate_agent",
            ok=False,
            error=str(exc),
        )
    return Result(kind=task.kind, output=value, handled_by="calculate_agent")


# Registry mapping a task kind to the sub-agent that handles it.
_REGISTRY: dict[str, Callable[[Task], Result]] = {
    "search": search_agent,
    "summarise": summarise_agent,
    "calculate": calculate_agent,
}

# Keywords used by :func:`infer_kind` to classify free-text requests.
_SEARCH_HINTS = ("search", "find", "look up", "lookup", "what is", "docs", "where")
_SUMMARISE_HINTS = ("summarise", "summarize", "tl;dr", "tldr", "gist", "shorten")
_CALC_HINTS = ("calculate", "compute", "evaluate", "what is", "how much")


def infer_kind(request: str) -> str:
    """Classify a free-text request into a task kind.

    A small, deterministic heuristic: an expression that looks arithmetic
    routes to ``calculate``; otherwise keyword hints decide between
    ``summarise`` and ``search``, defaulting to ``search``.
    """
    text = request.strip().lower()
    if not text:
        raise ValueError("Cannot infer kind from an empty request")

    # If it is mostly digits and operators, treat it as arithmetic.
    arithmetic_chars = set("0123456789+-*/().% ")
    stripped = text.replace("sqrt", "").replace("pi", "")
    if stripped and all(c in arithmetic_chars for c in stripped):
        return "calculate"

    if any(h in text for h in _SUMMARISE_HINTS):
        return "summarise"
    if any(h in text for h in _CALC_HINTS) and any(ch.isdigit() for ch in text):
        return "calculate"
    if any(h in text for h in _SEARCH_HINTS):
        return "search"
    return "search"


@dataclass
class Orchestrator:
    """Routes tasks to registered sub-agents and aggregates results."""

    registry: dict[str, Callable[[Task], Result]] = field(
        default_factory=lambda: dict(_REGISTRY)
    )

    def delegate(self, task: Task) -> Result:
        """Route a single task to its sub-agent and return the result."""
        agent = self.registry.get(task.kind)
        if agent is None:
            raise ValueError(f"No sub-agent registered for task kind: {task.kind!r}")
        return agent(task)

    def run(self, tasks: list[Task]) -> list[Result]:
        """Run every task in ``tasks`` and return their results in order."""
        return [self.delegate(t) for t in tasks]

    def handle(self, request: str, payload: str | None = None) -> Result:
        """Infer the task kind from ``request`` and delegate.

        If ``payload`` is omitted, the request itself is used as the payload --
        convenient for one-shot calls like ``handle("2 + 2 * 10")``.
        """
        kind = infer_kind(request)
        return self.delegate(Task(kind=kind, payload=payload if payload is not None else request))


def demo() -> list[Result]:
    """Run a small fixed plan through the orchestrator."""
    orchestrator = Orchestrator()
    plan = [
        Task(kind="search", payload="how does an MCP server expose tools"),
        Task(
            kind="summarise",
            payload=(
                "A Forward Deployed Engineer embeds with a customer to design, build, "
                "and ship production systems. The work is end to end. You scope the "
                "problem, prototype fast to prove value, then harden the prototype "
                "into something reliable. You also translate business goals into "
                "precise technical specifications."
            ),
        ),
        Task(kind="calculate", payload="sqrt(144) + 2 ** 5"),
    ]
    return orchestrator.run(plan)


if __name__ == "__main__":
    for result in demo():
        status = "ok" if result.ok else f"error: {result.error}"
        print(f"[{result.handled_by}] {result.kind} ({status}) -> {result.output}")
