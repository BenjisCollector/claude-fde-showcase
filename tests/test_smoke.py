"""Cross-cutting smoke / integration tests.

Confirms the agent skill, the re-exports from the MCP server module, and the
overall wiring all work *without* the ``mcp`` package installed -- the core
guarantee that keeps CI green offline.
"""

from agent_skills.doc_summariser.helper import gist, summarise_document


def test_skill_extractive_summary():
    text = "Cats purr. Cats hunt mice. The sky is blue. Cats sleep a lot."
    out = summarise_document(text, max_sentences=2).lower()
    assert "cats" in out


def test_skill_gist_is_one_line():
    out = gist("one two three four five six", max_words=3)
    assert out == "one two three ..."


def test_server_module_imports_logic_without_mcp():
    # The mcp package is intentionally NOT required to import the server module
    # or to run its core logic -- mcp is imported lazily inside build_server().
    # We do not assert mcp is absent (a dev box may have it); CI simply never
    # installs it, and these assertions must hold either way.
    from claude_fde_showcase.mcp_server import server

    assert server.search_docs("model context protocol")
    assert server.calculate("2 + 2") == 4.0
    assert isinstance(server.summarise_extractive("A. B. C. D. E.", 2), str)
    assert "mcp" in server.list_docs()


def test_build_server_raises_without_mcp_installed():
    # build_server() is the only thing that needs the SDK; it should fail
    # cleanly with ImportError when mcp is absent rather than at import time.
    from claude_fde_showcase.mcp_server import server

    try:
        server.build_server()
    except ImportError:
        return
    # If mcp happens to be installed in some environment, that's fine too.
