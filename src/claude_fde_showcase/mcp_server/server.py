"""A minimal MCP server exposing two tools.

This uses the official ``mcp`` Python SDK (FastMCP). The tools return
deterministic placeholder output so the server is genuinely runnable as a
scaffold without any external API keys or network calls.

Run it over stdio with::

    python -m claude_fde_showcase.mcp_server.server

The pure-logic helpers (``search_docs`` / ``summarise``) are importable and
unit-testable independently of the MCP transport.
"""

from __future__ import annotations

# A tiny in-memory "corpus" so search returns something deterministic.
_DOCS: dict[str, str] = {
    "mcp": "The Model Context Protocol (MCP) lets tools expose capabilities to LLM clients.",
    "subagents": "Sub-agents let an orchestrator delegate a scoped task to a specialised worker.",
    "skills": "Agent skills package a capability as a SKILL.md plus optional helper code.",
    "fde": "A Forward Deployed Engineer ships production AI systems alongside customers.",
}


def search_docs(query: str, limit: int = 3) -> list[dict[str, str]]:
    """Return docs whose key or body contains the query (case-insensitive).

    Deterministic placeholder retrieval over a small in-memory corpus.
    """
    q = query.strip().lower()
    if not q:
        return []
    hits = [
        {"id": key, "text": text}
        for key, text in _DOCS.items()
        if q in key.lower() or q in text.lower()
    ]
    return hits[: max(0, limit)]


def summarise(text: str, max_words: int = 20) -> str:
    """Return a deterministic, length-bounded "summary" of ``text``.

    Placeholder logic: truncate to ``max_words`` words. No model call.
    """
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(".,;:") + " ..."


def build_server():
    """Construct and return the FastMCP server with both tools registered."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("claude-fde-showcase")

    @mcp.tool()
    def search_docs_tool(query: str, limit: int = 3) -> list[dict[str, str]]:
        """Search the demo corpus and return matching documents."""
        return search_docs(query, limit)

    @mcp.tool()
    def summarise_tool(text: str, max_words: int = 20) -> str:
        """Summarise text down to at most ``max_words`` words."""
        return summarise(text, max_words)

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
