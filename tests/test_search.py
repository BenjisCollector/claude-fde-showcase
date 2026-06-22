"""Tests for the TF-IDF document search tool.

All run without the mcp package and without network access.
"""

import pytest

from claude_fde_showcase.tools.search import DocStore, search_docs


@pytest.fixture
def store():
    return DocStore.from_mapping(
        {
            "mcp": "The Model Context Protocol lets tools expose capabilities to LLM clients.",
            "subagents": "Sub-agents let an orchestrator delegate a scoped task to a worker.",
            "skills": "Agent skills package a capability as a SKILL.md plus helper code.",
            "fde": "A Forward Deployed Engineer ships production AI systems with customers.",
        }
    )


def test_search_ranks_relevant_doc_first(store):
    hits = store.search("model context protocol", limit=3)
    assert hits, "expected at least one hit"
    assert hits[0]["id"] == "mcp"


def test_search_returns_score_and_snippet(store):
    hits = store.search("orchestrator", limit=1)
    assert hits[0]["id"] == "subagents"
    assert hits[0]["score"] > 0
    assert "orchestrator" in hits[0]["snippet"].lower()


def test_search_respects_limit(store):
    hits = store.search("a", limit=2)
    assert len(hits) <= 2


def test_search_empty_query_returns_nothing(store):
    assert store.search("") == []
    assert store.search("   ") == []


def test_search_zero_or_negative_limit(store):
    assert store.search("mcp", limit=0) == []
    assert store.search("mcp", limit=-1) == []


def test_search_unmatched_query_returns_empty(store):
    assert store.search("zzzqqq nonexistentterm", limit=3) == []


def test_search_is_deterministic(store):
    assert store.search("capability", limit=3) == store.search("capability", limit=3)


def test_search_results_sorted_by_score_desc(store):
    hits = store.search("agent capability task", limit=4)
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_empty_store_returns_nothing():
    empty = DocStore.from_mapping({})
    assert empty.search("anything") == []


def test_from_dir_loads_repo_docs():
    # The real docs/ corpus ships with the repo; it should be non-empty and
    # searchable for a term that appears in it.
    store = DocStore.from_dir()
    ids = [d.id for d in store.documents]
    assert "mcp" in ids
    hits = store.search("Forward Deployed Engineer", limit=3)
    assert hits


def test_from_dir_missing_directory_is_empty(tmp_path):
    missing = tmp_path / "does-not-exist"
    store = DocStore.from_dir(missing)
    assert store.documents == []


def test_search_docs_convenience_wrapper():
    hits = search_docs("model context protocol", limit=2)
    assert any(h["id"] == "mcp" for h in hits)
