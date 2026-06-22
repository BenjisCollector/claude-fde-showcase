"""Smoke tests covering the deterministic helper logic.

These run without the MCP transport or any network access.
"""

from agent_skills.doc_summariser.helper import summarise_document
from claude_fde_showcase.mcp_server.server import search_docs, summarise
from subagents.orchestrator import Orchestrator, Task


def test_search_docs_finds_match():
    hits = search_docs("mcp")
    assert any(h["id"] == "mcp" for h in hits)


def test_search_docs_empty_query():
    assert search_docs("") == []


def test_search_docs_respects_limit():
    assert len(search_docs("e", limit=2)) <= 2


def test_summarise_truncates():
    out = summarise("one two three four five", max_words=2)
    assert out == "one two ..."


def test_summarise_passthrough_when_short():
    assert summarise("short text", max_words=10) == "short text"


def test_skill_helper_matches_truncation():
    assert summarise_document("a b c d", max_words=2) == "a b ..."


def test_orchestrator_routes_tasks():
    orch = Orchestrator()
    results = orch.run([Task(kind="search", payload="skills")])
    assert results[0].handled_by == "search_agent"


def test_orchestrator_unknown_kind_raises():
    orch = Orchestrator()
    try:
        orch.delegate(Task(kind="nope", payload="x"))
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown task kind")
