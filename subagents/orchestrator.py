"""A minimal orchestrator / sub-agent example.

The orchestrator does not call any model. It demonstrates the *shape* of an
agentic delegation: a coordinator routes a task to a specialised sub-agent
function based on the task type, collects the result, and returns a combined
report. This is the pattern an FDE scales up by swapping the stub sub-agents
for real Claude-backed workers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from claude_fde_showcase.mcp_server.server import search_docs, summarise


@dataclass
class Task:
    """A unit of work routed to a sub-agent."""

    kind: str  # "search" or "summarise"
    payload: str


@dataclass
class Result:
    """The outcome of running a task through a sub-agent."""

    kind: str
    output: object
    handled_by: str


def search_agent(task: Task) -> Result:
    """Sub-agent specialised in document retrieval."""
    return Result(kind=task.kind, output=search_docs(task.payload), handled_by="search_agent")


def summarise_agent(task: Task) -> Result:
    """Sub-agent specialised in summarisation."""
    return Result(kind=task.kind, output=summarise(task.payload), handled_by="summarise_agent")


# Registry mapping a task kind to the sub-agent that handles it.
_REGISTRY: dict[str, Callable[[Task], Result]] = {
    "search": search_agent,
    "summarise": summarise_agent,
}


@dataclass
class Orchestrator:
    """Routes tasks to registered sub-agents and aggregates results."""

    registry: dict[str, Callable[[Task], Result]] = field(default_factory=lambda: dict(_REGISTRY))

    def delegate(self, task: Task) -> Result:
        agent = self.registry.get(task.kind)
        if agent is None:
            raise ValueError(f"No sub-agent registered for task kind: {task.kind!r}")
        return agent(task)

    def run(self, tasks: list[Task]) -> list[Result]:
        return [self.delegate(t) for t in tasks]


def demo() -> list[Result]:
    """Run a small fixed plan through the orchestrator."""
    orchestrator = Orchestrator()
    plan = [
        Task(kind="search", payload="mcp"),
        Task(kind="summarise", payload="A Forward Deployed Engineer ships production AI systems alongside customers every single week."),
    ]
    return orchestrator.run(plan)


if __name__ == "__main__":
    for result in demo():
        print(f"[{result.handled_by}] {result.kind} -> {result.output}")
